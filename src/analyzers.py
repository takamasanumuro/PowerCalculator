#Builtin
import os
import datetime

#Third party
from colorama import Fore, Style, init

class PowerAnalyzer:
    def __init__(self):
        self.entries = []
        self.log_enabled = False
        self.total_energy = 0.0
        self.log_path = None
    
    def add_entry(self, timestamp, voltage, current):
        self.entries.append((timestamp, voltage, current))

    def reset(self):
        self.entries = []
        self.total_energy = 0.0
    
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
        
        if self.log_path is None:
            parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            subdirectory = os.path.join(parent_directory, 'logs')
            if not os.path.exists(subdirectory):
                os.makedirs(subdirectory) 
            self.log_path = os.path.join(subdirectory, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

            with open(self.log_path, 'w') as file:
                file.write("Timestamp(epoch_ms)\tVoltage(V)\tCurrent(A)\tTotal Energy(Wh)")

        with open(self.log_path, 'a') as file:
            timestamp, voltage, current = self.entries[-1]
            file.write(f"{timestamp}\t{voltage:.2f}V\t{current:.3f}A\t{self.total_energy:.3f}Wh\n")
        