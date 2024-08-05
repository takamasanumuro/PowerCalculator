import serial
import time

class PowerSupplyController:
    def __init__(self, port, baudrate = 9600):
        self.serial = serial.Serial(port, baudrate, timeout = 0.1)
        self.command = ''
    
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

    def ask_readings(self):
        self.send_command('VOUT1?\rIOUT1?\r')
    
    def close(self):
        self.serial.close()