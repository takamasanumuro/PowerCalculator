import os
import datetime
from colorama import Fore, Style, init

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
        
        parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        subdirectory = os.path.join(parent_directory, 'logs')
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)
        
        filename = os.path.join(subdirectory, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(filename, 'w') as file:
            file.write("Timestamp(epoch_ms)\tVoltage(V)\tCurrent(A)\n")
            for timestamp, voltage, current in self.entries:
                file.write(f"{timestamp}\t{voltage:.2f}V\t{current:.3f}A\n")
            file.write(f"Total energy: {self.total_energy:.3f} Wh\n")
        
        print(f"{Fore.CYAN}Data saved to {filename}{Style.RESET_ALL}")