import serial
import time 
import datetime
from colorama import Fore, Style, init
import os

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


def handle_exit(signal, frame):
    power_supply_controller.turn_off()
    power_supply_controller.unlock_front_panel()
    power_supply_controller.close()

    power_analyzer.save_data()

def handle_current(current, threshold):
    if current < threshold:
        power_supply_controller.turn_off()

def check_readings() -> tuple:
    #Format is {voltage:.2f}\n{current:.3f}\n
    
    lines = power_supply_controller.serial.readlines()
    voltage = float(lines[0].strip())
    current = float(lines[1].strip())
    power = voltage * current
    timestamp_epoch_ms = int(time.time() * 1000)
    print(f"{Fore.BLUE}Voltage: {voltage:.2f}V{Style.RESET_ALL}\t{Fore.YELLOW}Current: {current:.3f}A{Style.RESET_ALL}\t{Fore.RED}Power: {power:.2f}W{Style.RESET_ALL}\t{Fore.GREEN}Timestamp: {timestamp_epoch_ms}{Style.RESET_ALL}")
    return (voltage, current, timestamp_epoch_ms)

def init_colorama():
    init(autoreset=True)

class PowerAnalyzer:
    def __init__(self):
        self.entries = []
        self.log_enabled = False
        self.total_energy = 0.0
    
    def add_entry(self, timestamp, voltage, current):
        self.entries.append((timestamp, voltage, current))
    
    def calculate_energy(self):
        
        if len(self.entries) < 2:
            return 0.0
        
        total_energy = 0.0

        for i in range(1, len(self.entries)):
            previous_time, previous_voltage, previous_current = self.entries[i - 1]
            current_time, current_voltage, current_current = self.entries[i]

            # Calculate the time difference in hours
            milliseconds_to_hours = 3600000
            delta_time = current_time - previous_time
            delta_time_hours = (delta_time) / milliseconds_to_hours
            
            # Calculate average voltage and current
            average_voltage = (previous_voltage + current_voltage) / 2
            average_current = (previous_current + current_current) / 2

            # Calculate energy in Wh
            energy = average_voltage * average_current * delta_time_hours
            total_energy += energy
        
        self.total_energy = total_energy
        return total_energy
    
    def save_data(self):
        if not self.log_enabled:
            return
        
        subdirectory = 'logs'
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)
        
        filename = os.path.join(subdirectory, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(filename, 'w') as file:
            file.write("Timestamp(epoch_ms)\tVoltage(V)\tCurrent(A)\n")
            for timestamp, voltage, current in self.entries:
                file.write(f"{timestamp}\t{voltage:.2f}V\t{current:.3f}A\n")
            file.write(f"Total energy: {self.total_energy:.3f} Wh\n")
        
        print(f"{Fore.CYAN}Data saved to {filename}{Style.RESET_ALL}")


if __name__ == '__main__':
    power_supply_controller = PowerSupplyController('COM14')
    power_supply_controller.turn_on()

    power_analyzer = PowerAnalyzer()
    power_analyzer.log_enabled = True

    try:
        while True:
            measurement_interval = 0.400
            time.sleep(measurement_interval)
            power_supply_controller.ask_readings()
            voltage, current, timestamp = check_readings()
            power_analyzer.add_entry(timestamp, voltage, current)
            total_energy = power_analyzer.calculate_energy()
            print(f"{Fore.MAGENTA}Total energy: {total_energy:.3f} Wh{Style.RESET_ALL}")

    except (KeyboardInterrupt, SystemExit): 
        handle_exit(None, None) 

