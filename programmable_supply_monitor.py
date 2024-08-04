import serial
import time 
import threading

class PowerSupplyController:
    def __init__(self, port, baudrate = 9600):
        self.serial = serial.Serial(port, baudrate, timeout = 1)
        self.lock_front_panel()
        self.turn_off()
    
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

    def get_voltage(self):
        self.send_command('VOUT1?\r')
        return float(self.serial.readline().decode().strip())
    
    def get_current(self):
        self.send_command('IOUT1?\r')
        return float(self.serial.readline().decode().strip())
    
    def close(self):
        self.serial.close()

def monitor_power_supply(power_supply_controller):
    while True:
        voltage = power_supply_controller.get_voltage()
        current = power_supply_controller.get_current()
        print(f"Voltage: {voltage:.2f} V, Current: {current:.3f} A")
        time.sleep(0.1)

if __name__ == '__main__':
    power_supply_controller = PowerSupplyController('COM14')
    power_supply_controller.lock_front_panel()
    power_supply_controller.turn_on()
    
    monitor_thread = threading.Thread(target = monitor_power_supply, args = (power_supply_controller,))
    monitor_thread.daemon = True
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        power_supply_controller.turn_off()
        power_supply_controller.unlock_front_panel()
        power_supply_controller.close()