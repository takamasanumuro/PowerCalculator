#socket client communication

from typing import Optional
from typing import Protocol
from enum import Enum
from dataclasses import dataclass
import socket
import time

@dataclass
class DataPointClass:
    voltage: Optional[float]
    current: Optional[float]
    power: Optional[float]
    timestamp: int
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
    def set_state(self, mode : PowerStates):
        pass

#Bidirectional power supply that can read measurements and charge and discharge batteries itself via socket communication
class ITech6018Device(DataSource, StateManager):
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.state = PowerStates.PASSIVE
        self.charge_current = 0
        self.charge_cutoff_current = 0
        self.charge_cutoff_voltage = 0
        self.discharge_voltage = 0
        self.discharge_cutoff_voltage = 0
        self.discharge_cutoff_current = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.ip, self.port))
            self.send_command('SYSTEM:REMOTE\n')
            self.send_command('*CLS\n')
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
            self.send_command("FETCH:CURRENT?\n")
            current = float(self.receive_response())
            
            self.send_command("FETCH:VOLTAGE?\n")
            voltage = float(self.receive_response())
            
            power = voltage * current
            timestamp = int(time.time() * 1000)
            return DataPointClass(voltage, current, power, timestamp, True)
        except (socket.error, ValueError) as e:
            print(f"Error reading measurements: {e}")
            return DataPointClass(None, None, None, int(time.time() * 1000), False)
        
    def set_state(self, state: PowerStates):
        try:
            if state == PowerStates.CHARGE:
                self.send_command("BATTERY:MODE CHARGE\n")
                self._send_charge_rates()
            elif state == PowerStates.DISCHARGE:
                self.send_command("BATTERY:MODE DISCHARGE\n")
                self._send_discharge_rates()
            else:
                self.send_command("BATTERY:MODE FIXED\n")
            self.state = state
        except socket.error as e:
            print(f"Error setting mode: {e}")
        
    def set_charge_rates(self, charge_current: float, charge_cutoff_current: float, charge_cutoff_voltage: float):
        self.charge_current = charge_current
        self.charge_cutoff_current = charge_cutoff_current
        self.charge_cutoff_voltage = charge_cutoff_voltage

    def _send_charge_rates(self):
        try:
            self.send_command(f"BATTERY:CHARGE:CURRENT {self.charge_current}\n")
            self.send_command(f"BATTERY:CHARGE:VOLTAGE {self.charge_cutoff_voltage + 1}\n")
            self.send_command(f"BATTERY:SHUT:CURRENT {self.charge_cutoff_current}\n")
            self.send_command(f"BATTERY:SHUT:VOLTAGE {self.charge_cutoff_voltage}\n")
        except socket.error as e:
            print(f"Error setting charge rates: {e}")

    def set_discharge_rates(self, discharge_current: float, discharge_cutoff_current: float, discharge_cutoff_voltage: float):
        self.discharge_current = discharge_current
        self.discharge_cutoff_current = discharge_cutoff_current
        self.discharge_cutoff_voltage = discharge_cutoff_voltage

    def _send_discharge_rates(self):
        try:
            self.send_command(f"BATTERY:DISCHARGE:CURRENT {self.discharge_current}\n")
            self.send_command(f"BATTERY:DISCHARGE:VOLTAGE {self.discharge_cutoff_voltage - 1}\n")
            self.send_command(f"BATTERY:SHUT:CURRENT {self.discharge_cutoff_current}\n")
            self.send_command(f"BATTERY:SHUT:VOLTAGE {self.discharge_cutoff_voltage}\n")
        except socket.error as e:
            print(f"Error setting discharge rates: {e}")


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


device = ITech6018Device('169.254.150.40', 30000)
device.set_charge_rates(charge_current = 1.00, charge_cutoff_current = 0.040, charge_cutoff_voltage = 14.4)
device.set_discharge_rates(discharge_current = -1.00, discharge_cutoff_current = -0.040, discharge_cutoff_voltage = 11.8)
data_point = device.read_measurements()
print(data_point)
