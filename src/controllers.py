#Builts-ins
import serial
import time
import re

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
        timestamp_epoch_ms = int(time.time() * 1000)
        return (voltage, current, power, timestamp_epoch_ms)
    
    def close(self):
        self.serial.close()


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
            return ValueError("Could not parse the readings")
        
        value = float(match.group(1))
        unit = match.group(2)
        return (value, unit)


    def read_measurements(self):
        self._ask_readings()
        line = self.serial.readline()
        value, unit = self._parse_readings(line.decode())
        timestamp_epoch_ms = int(time.time() * 1000)
        return (value, unit, timestamp_epoch_ms)
    
    def close(self):
        self.serial.close()