#socket client communication

from typing import Optional
from typing import Protocol
from enum import Enum
from dataclasses import dataclass
import socket
import time
import logging
import os
from utils import generate_test_folder_name
from analyzers import PowerAnalyzer

'''
48V Battery Charging Command: 
SYSTEM:REMOTE  # Enter remote state
BATTERY:MODE CHARGE  # Select charge mode
BATTERY:CHARGE:VOLTAGE 50  # Set charge voltage to 50V
BATTERY:CHARGE:CURRENT 20  # Set charge current to 20A
BATTERY:SHUT:VOLTAGE 49  # Set charge cutoff voltage at 49V
BATTERY:SHUT:CURRENT 0.1  # Set charge cutoff current at 0.1A
BATTERY:SHUT:CAPACITY 50  # Set cutoff capacity at 50Ah
BATTERY:SHUT:TIME 5000  # Set cutoff time at 5000 seconds
FUNCTION:MODE BATTERY  # Execute RUN/RESET
FUNCTION:MODE FIXED  # Execute STOP
OUTPUT 0  # Turn off output

SYSTEM:REMOTE  # Enter remote state
BATTERY:MODE DISCHARGE  # Select discharge mode
BATTERY:DISCHARGE:VOLTAGE 10  # Set discharge voltage to 10V
BATTERY:DISCHARGE:CURRENT -5  # Set discharge current to -5A
BATTERY:SHUT:VOLTAGE 36  # Set discharge cutoff voltage at 36V
BATTERY:SHUT:CURRENT -0.1  # Set discharge cutoff current at -0.1A
BATTERY:SHUT:CAPACITY -50  # Set cutoff capacity at -50Ah
BATTERY:SHUT:TIME 5000  # Set cutoff time at 5000 seconds
FUNCTION:MODE BATTERY  # Execute RUN/RESET
FUNCTION:MODE FIXED  # Execute STOP
OUTPUT 0  # Turn off output
'''


@dataclass
class DataPointClass:
    voltage: Optional[float]
    current: Optional[float]
    power: Optional[float]
    ahour: Optional[float]
    whour: Optional[float]
    timestamp: float
    is_valid : bool

#Let's define protocols for objects that can read measurements and control devices that can set the mode to charge or discharge
class DataSource(Protocol):
    def read_measurements(self) -> DataPointClass:
        pass

class PowerStates(Enum):
    CHARGE = "charge"
    DISCHARGE = "discharge"
    PASSIVE = "passive"

class StateManager(Protocol):
    state : PowerStates
    def set_state(self, state : PowerStates, current : float, cutoff_voltage : float, cutoff_current : float):
        pass

#Bidirectional power supply that can read measurements and charge and discharge batteries itself via socket communication
class ITech6018Device(DataSource, StateManager):
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.state = PowerStates.PASSIVE
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.ip, self.port))
            self.send_command('SYSTEM:REMOTE\n')
            self.send_command('*CLS\n')
            self.send_command('FUNCTION:MODE FIXED\n')
            self.send_command('SENSE:ACQUIRE:POINTS 10\n')
            self.send_command('SENSE:WHOUR:RESET\n')
            self.send_command('SENSE:AHOUR:RESET\n')

        except socket.error as e:
            print(f"Error connecting to device: {e}")
            self.socket.close()

    def __del__(self):
        try:
            self.send_command('SYSTEM:LOCAL\n')
        except socket.error as e:
            print(f"Error sending SYSTEM:LOCAL command: {e}")
        finally:
            self.socket.close()

    def send_command(self, command : str):
        try:
            self.socket.sendall(command.encode('utf-8'))
        except socket.error as e:
            print(f"Error sending command: {e}")

    def receive_response(self) -> str:
        try:
            data = self.socket.recv(1024)
            return data.decode('utf-8').strip()
        except socket.error as e:
            print(f"Error receiving response: {e}")
            return ""

    def read_measurements(self) -> DataPointClass:
        try:
            self.send_command("MEASURE:CURRENT?\n")
            current = float(self.receive_response())
            
            self.send_command("MEASURE:VOLTAGE?\n")
            voltage = float(self.receive_response())

            self.send_command("MEASURE:AHOUR?\n")
            ahour = float(self.receive_response())

            self.send_command("MEASURE:WHOUR?\n")
            whour = float(self.receive_response())
            
            power = voltage * current
            timestamp = time.time()
            return DataPointClass(voltage, current, power, ahour, whour, timestamp, True)
        except (socket.error, ValueError) as e:
            print(f"Error reading measurements: {e}")
            return DataPointClass(None, None, None, None, None, time.time(), False)
        
    def set_state(self, state: PowerStates, current : float, cutoff_voltage : float, cutoff_current : float):
        try:
            if state == PowerStates.CHARGE:
                self.send_command("FUNCTION:MODE FIXED\n")
                time.sleep(2)
                self.send_command("BATTERY:MODE CHARGE\n")
                self._send_charge_rates(charge_current = current, charge_cutoff_voltage = cutoff_voltage, charge_cutoff_current = cutoff_current)
                self.send_command("FUNCTION:MODE BATTERY\n")
            elif state == PowerStates.DISCHARGE:
                self.send_command("FUNCTION:MODE FIXED\n")
                time.sleep(2)
                self.send_command("BATTERY:MODE DISCHARGE\n")
                self._send_discharge_rates(discharge_current = current, discharge_cutoff_voltage = cutoff_voltage, discharge_cutoff_current = cutoff_current)
                self.send_command("FUNCTION:MODE BATTERY\n")
            else:
                self.send_command("FUNCTION:MODE FIXED\n")
                self.send_command("OUTPUT 0\n")
            self.state = state
        except socket.error as e:
            print(f"Error setting mode: {e}")

    def set_output(self, output: bool):
        try:
            if output:
                self.send_command("OUTPUT 1\n")
            else:
                self.send_command("OUTPUT 0\n")
        except socket.error as e:
            print(f"Error setting output: {e}")

    def _send_charge_rates(self, charge_current : float, charge_cutoff_voltage : float, charge_cutoff_current : float):
        try:
            self.send_command(f"BATTERY:CHARGE:CURRENT {charge_current}\n")
            self.send_command(f"BATTERY:CHARGE:VOLTAGE {charge_cutoff_voltage + 0.020}\n") #For charge, charge voltage must be the same as the cutoff voltage
            self.send_command(f"BATTERY:SHUT:CURRENT 0\n")
            self.send_command(f"BATTERY:SHUT:VOLTAGE {charge_cutoff_voltage + 1.000}\n") #For charge, shutdown voltage must be above the charge voltage
        except socket.error as e:
            print(f"Error setting charge rates: {e}")

    def _send_discharge_rates(self, discharge_current : float, discharge_cutoff_voltage : float, discharge_cutoff_current : float):
        try:
            self.send_command(f"BATTERY:DISCHARGE:CURRENT {discharge_current}\n")
            self.send_command(f"BATTERY:DISCHARGE:VOLTAGE {discharge_cutoff_voltage - 0.150}\n") #For discharge, discharge voltage must be below the shutdown voltage
            self.send_command(f"BATTERY:SHUT:CURRENT 0\n")
            self.send_command(f"BATTERY:SHUT:VOLTAGE {discharge_cutoff_voltage - 0.150}\n") #For discharge, shutdown voltage is the same as the cutoff voltage
        except socket.error as e:
            print(f"Error setting discharge rates: {e}")

class ChargeController:

    def __init__(self, data_source: DataSource, state_manager: StateManager, logger: logging.Logger, folder_name: str):
        self.data_source = data_source
        self.state_manager = state_manager
        self.logger = logger
        self.folder_name = folder_name
        self.sequence = []
        self.current_step = 0
        self.power_analyzer = PowerAnalyzer()

    def add_state(self, state: PowerStates, current: float, cutoff_voltage: float, cutoff_current: float):
        self.sequence.append((state, current, cutoff_voltage, cutoff_current))

    def execute_sequence(self):
        
        log_directory = f'./logs/{self.folder_name}'
        if os.path.exists(log_directory):
            raise FileExistsError(f"Directory {self.folder_name} already exists")
        os.makedirs(log_directory)
       
        while self.current_step < len(self.sequence):

            state, current, cutoff_voltage, cutoff_current = self.sequence[self.current_step]

            log_file = f'{log_directory}/{self.current_step}_{state.value}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(message)s')
            self.logger.addHandler(file_handler)

            self.state_manager.set_state(state, current, cutoff_voltage, cutoff_current)
            self.logger.info(f"Executing {state.value} with cutoff voltage {cutoff_voltage}V and current {current}A")
            
            while True:
                data_point = self.data_source.read_measurements()
                self.power_analyzer.add_entry(data_point.current, data_point.voltage, data_point.timestamp)
                energy, capacity = self.power_analyzer.calculate_energy_capacity()
                data_point.whour = energy
                data_point.ahour = capacity

                self.logger.debug(data_point)
                if state == PowerStates.CHARGE and data_point.voltage >= cutoff_voltage and abs(data_point.current) <= abs(cutoff_current):
                    break
                if state == PowerStates.DISCHARGE and data_point.voltage <= cutoff_voltage:
                    break

            self.current_step += 1
            self.logger.removeHandler(file_handler)
            file_handler.close()
        self.state_manager.set_state(PowerStates.PASSIVE, None, None, None)
        self.logger.info("Sequence complete")


#Use SENSE:ACQUIRE:POINTS <NUMBER> to set the number of points to acquire
#Use SENSE:ACQUIRE:TINTERVAL <TIME> to set the time interval between points
#Minimum is 10 points
def benchmark_response_time(ip: str, port: int):
    device = ITech6018Device(ip, port)
    time_list = []
    for i in range(10):
        time_begin = time.time()
        data_point = device.read_measurements()
        time_end = time.time()
        time_list.append(time_end - time_begin)
    
    print(f"Average response time: {sum(time_list) / len(time_list):.4f} seconds")

def set_system_time(ip : str, port : int) -> None:
    device = ITech6018Device(ip, port)
    current_time = time.localtime()
    command = f"SYSTEM:TIME {current_time.tm_hour}, {current_time.tm_min}, {current_time.tm_sec}\n"
    device.send_command(command)
    command = f"SYSTEM:DATE {current_time.tm_year}, {current_time.tm_mon}, {current_time.tm_mday}\n"
    device.send_command(command)


ip_address = '169.254.150.40'
port = 30000
folder_name = generate_test_folder_name()

def main():
    logger = logging.getLogger('ChargeController')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()   
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    device = ITech6018Device(ip_address, port)
    controller = ChargeController(data_source= device, state_manager= device, logger= logger, folder_name= folder_name)
    controller.add_state(PowerStates.CHARGE, current = 0.500, cutoff_voltage = 14.4, cutoff_current = 0.350)
    controller.add_state(PowerStates.DISCHARGE, current = -1.000, cutoff_voltage = 12.5, cutoff_current = None)
    controller.add_state(PowerStates.CHARGE, current = 0.500, cutoff_voltage = 14.4, cutoff_current = 0.350)
    controller.execute_sequence()


if __name__ == "__main__":
    main()