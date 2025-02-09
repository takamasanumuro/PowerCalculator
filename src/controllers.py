#Builts-ins
import serial
import time
import re
from collections import namedtuple
from typing import Optional

import serial.serialutil
import chime
import requests


#Locals
from analyzers import *


class PowerSupplyController:
    def __init__(self, port, baudrate = 9600):
        self.serial = serial.Serial(port, baudrate, timeout = 0.1)
    
    def send_command(self, command):
        self.serial.write(command.encode())
        time.sleep(0.050)
    
    def lock_front_panel(self):
        self.send_command('LOCK1\r')

    def unlock_front_panel(self):
        self.send_command('LOCK0\r')
    
    def turn_off(self):
        self.send_command('OUT0\r')
    
    def turn_on(self):
        self.send_command('OUT1\r')

    def set_output(self, voltage, current):
        command = f"ISET1:{current:.3f}\rVSET1:{voltage:.2f}\r"
        self.send_command(command)

    def _ask_readings(self):
        self.send_command('VOUT1?\rIOUT1?\r')
    
    def _parse_readings(self, lines):
        if len(lines) != 2:
            return ValueError("Could not parse the readings")
        
        voltage = float(lines[0].strip())
        current = float(lines[1].strip())
        power = voltage * current
        return (voltage, current, power)

    def read_measurements(self):
        #Format is {voltage:.2f}\n{current:.3f}\n
        self._ask_readings()
        lines = self.serial.readlines()
        voltage, current, power = self._parse_readings(lines)
        timestamp = time.time()
        return (voltage, current, power, timestamp)
    
    def close(self):
        self.serial.close()



DataPoint = namedtuple("DataPoint", ["value", "unit", "timestamp"])

class YokogawaController:
    def __init__(self, serial_connection : serial.Serial):
        self.serial = serial_connection
    
    def send_command(self, command):
        self.serial.write(command.encode())
        time.sleep(0.050)
    
    def _ask_readings(self):
        self.send_command('RR,1\r\n')

    def _parse_readings(self, line):
        pattern = r"([+-]?\d+\.\d+)\s*([A-Za-z]+)"
        match = re.search(pattern, line)

        if not match:
            raise ValueError("Could not parse the readings")
        
        value = match.group(1)
        unit = match.group(2)
        return (value, unit)


    def read_measurements(self) -> DataPoint:
        if not self.serial.is_open:
            return DataPoint(None, None, None)
        self._ask_readings()
        line = self.serial.readline()
        try:
            value, unit = self._parse_readings(line.decode())
            unit = format_unit(value, unit)
        except ValueError as e:
            return DataPoint(None, None, None)
        timestamp = time.time()
        return DataPoint(float(value), unit, timestamp)
    
    def close(self):
        self.serial.close()

class RelayController:
    def __init__(self, serial_connection : serial.Serial, relay_number : int):
        self.serial = serial_connection
        self.relay_number = relay_number
        assert relay_number in [1, 2, 3, 4], "Invalid relay number"
        self.relay_state = "OFF"
    
    def _send_command(self, command):

        while not self.serial.is_open:
            try:
                self.serial.open()
            except (serial.serialutil.SerialException):
                raise

        self.serial.write(command.encode())
        self.serial.flush() # Make sure all data is written to the port
        self.serial.close()
        time.sleep(0.050)

    def set_relay(self, state : str):
        assert state in ["ON", "OFF"], "Invalid state"
        command = f"RELAY;{self.relay_number};{state}\r\n"
        self._send_command(command)
        self.relay_state = state

    def get_relay_state(self):
        return self.relay_state
    
    def close(self):
        self.serial.close()

class ChargeController():

    MODES = ["monitor", "cycle"]
    CYCLE_STATES = ["precharge", "discharge", "recharge"]

    def __init__(self, relay_controller : RelayController, power_analyzer : PowerAnalyzer, logger : DataLogger) -> None:
        self.mode = "monitor"
        self.cycle_state = "precharge"
        self.cycle_completed = False
        self.relay_controller = relay_controller
        self.power_analyzer = power_analyzer
        self.logger = logger
        self.max_charge_voltage = None
        self.charge_cutoff_current = None
        self.discharge_cutoff_voltage = None
        self.recent_measurements = []

        self.logger.add_save_paths(["monitor"])
        self.logger.add_save_paths(self.CYCLE_STATES)

    def _next_cycle_state(self):
        if self.mode != "cycle":
            return
        
        cycle_states = ["precharge", "discharge", "recharge"]
        current_index = cycle_states.index(self.cycle_state)
        next_index = (current_index + 1) % len(cycle_states)
        self.cycle_state = cycle_states[next_index]

        relay_state = "ON" if self.cycle_state == "discharge" else "OFF"
        self.relay_controller.set_relay(relay_state)

        self.power_analyzer.reset()
        
        print(f"CONTROLLER: Transitioning to {self.cycle_state}")

    def set_charge_threshold(self, max_charge_voltage : float, charge_cutoff_current : float):
        self.max_charge_voltage = max_charge_voltage
        self.charge_cutoff_current = charge_cutoff_current

    def set_discharge_threshold(self, discharge_cutoff_voltage : float):
        self.discharge_cutoff_voltage = discharge_cutoff_voltage

    def watch_values(self, voltage, current, timestamp):  
        assert voltage is not None, "CHARGE CONTROLLER: Voltage is None"
        assert current is not None, "CHARGE CONTROLLER: Current is None"

        self.recent_measurements.append((voltage, current, timestamp))
        self.recent_measurements = [m for m in self.recent_measurements if timestamp - m[2] <= 1.0]

        if len(self.recent_measurements) >= 3 and self.mode == "cycle":
            self.evaluate_cycle_state()

        power = voltage * current
        accumulated_energy = self.power_analyzer.calculate_energy()

        directory = self.mode if self.mode != "cycle" else self.cycle_state
        self._log_measurements(directory, voltage, current, power, accumulated_energy, timestamp)

    def evaluate_cycle_state(self):
        # Logic to evaluate whether to proceed to the next cycle state
        # based on the recent measurements
        voltages = [m[0] for m in self.recent_measurements]
        currents = [m[1] for m in self.recent_measurements]

        if self.cycle_state == "precharge":
            if all(v >= self.max_charge_voltage for v in voltages) and all(abs(c) <= self.charge_cutoff_current for c in currents):
                self._next_cycle_state()
        elif self.cycle_state == "discharge":
            if all(v <= self.discharge_cutoff_voltage for v in voltages):
                self._next_cycle_state()
        elif self.cycle_state == "recharge":
            if all(v >= self.max_charge_voltage for v in voltages) and all(abs(c) <= self.charge_cutoff_current for c in currents):
                self.cycle_completed = True
                self.set_mode("monitor")
                print("CONTROLLER: Cycle completed\nCheck the logs for more information")
                requests.post("https://ntfy.sh/alertas-bateria", data = "Ciclo de carga completado")
                chime.theme("pokemon")
                chime.success()
                time.sleep(6)
                exit()

    def _log_measurements(self, directory, voltage, current, power, energy, timestamp):
        #convert epoch time to human readable format
        data = f"{voltage:.2f}V {current:.3f}A {energy:.4f}Wh"
        timestamped_data = append_timestamp(timestamp, data)
        self.logger.save_data(directory, timestamped_data)
           

    def set_mode(self, mode):
        assert mode in self.MODES, f"Invalid mode: {mode}"
        if mode == self.mode:
            return
        self.mode = mode
        self.power_analyzer.reset()

        if mode == "monitor":
            self.relay_controller.set_relay("OFF")

    def flip_relay(self):
        current_state = self.relay_controller.get_relay_state()
        new_state = "ON" if current_state == "OFF" else "OFF"
        self.relay_controller.set_relay(new_state) 

    def get_mode(self):
        return self.mode
    
    def get_available_modes(self) -> list[str]:
        return self.MODES

        


def count_decimal_places(number: float) -> int:
    return len(str(number).split(".")[1])


def format_unit(value, raw_decoded_unit : str):

    #mV = 3 decimal places
    #V = 4 decimal places
    #uA = 2 decimal places
    #mA = 3 decimal places
    #A = 4 decimal places

    table = [
        {"unit": "mV"},
        {"unit": "V"},
        {"unit": "uA"},
        {"unit": "mA"},
        {"unit": "A"},
    ]

    units = ["mVAC", "VAC", "mVDC", "VDC", "OHM", "kOHM", "MOHM", "nF", "uF", "mF", "C", "nADC", "uADC", "mADC", "ADC"]

    pattern = r"({})".format("|".join(units))

    match = re.search(pattern, raw_decoded_unit)
    if not match:
        return ""
    
    match_unit = match.group()
    match_unit_trimmed = match_unit.rstrip()
    return match_unit_trimmed

    
def check_if_power_available(data_points : list[DataPoint]) -> tuple[bool, Optional[float], Optional[float]]:
    if len(data_points) != 2:
        return (False, None, None)
    if data_points[0].value is None or data_points[1].value is None:
        return (False, None, None)
    voltage, current = find_current_and_voltage_values(data_points)

    if voltage is None or current is None:
        return (False, None, None)

    return (True, voltage, current)

def get_timestamp(data_points : list[DataPoint]) -> int:
    for data_point in data_points:
        if data_point.timestamp:
            return data_point.timestamp


def find_current_and_voltage_values(data_points : list[DataPoint]) -> tuple[Optional[float], Optional[float]]:
    voltage, current = None, None
    for data_point in data_points:
        if voltage is None:
            voltage = find_voltage_value(data_point)
        if current is None:
            current = find_current_value(data_point)
    return (voltage, current)


def is_current_unit(unit : str) -> bool:
    if unit is None:
        return False
    return re.search(r"\w?[A]", unit)

def is_voltage_unit(unit : str) -> bool:
    return re.search(r"\w?[V]", unit)

def find_current_value(data_point: DataPoint) -> Optional[float]:
    if not is_current_unit(data_point.unit):
        return None
    return float(data_point.value)
        
def find_voltage_value(data_point : DataPoint) -> Optional[float]:
    if not is_voltage_unit(data_point.unit):
        return None
    return float(data_point.value)
