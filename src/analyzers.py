#Builtin
import os
import time
import datetime

#Third party
from colorama import Fore, Style, init

class PowerAnalyzer:
    def __init__(self):
        self.entries = []
        self.start_time: float = None
        self.total_energy: float = 0.0  # Running total of energy
        self.total_capacity: float = 0.0  # Running total of capacity
    
    def add_entry(self, voltage, current, timestamp):
        self.entries.append((voltage, current, timestamp))
        if not self.start_time:
            self.start_time = timestamp

        # Calculate energy and capacity for the new entry
        if len(self.entries) > 1:
            previous_voltage, previous_current, previous_time = self.entries[-2]
            current_voltage, current_current, current_time = self.entries[-1]

            # Calculate the time difference in hours
            seconds_to_hours = 3600
            delta_time = current_time - previous_time
            delta_time_hours = delta_time / seconds_to_hours

            # Calculate average voltage and current
            average_voltage = (previous_voltage + current_voltage) / 2
            average_current = (previous_current + current_current) / 2

            # Calculate energy in Wh and capacity in Ah
            energy = average_voltage * average_current * delta_time_hours
            capacity = average_current * delta_time_hours

            # Update running totals
            self.total_energy += energy
            self.total_capacity += capacity

    def reset(self):
        self.entries = []
        self.total_energy = 0.0
        self.total_capacity = 0.0
    
    def calculate_energy(self) -> float:
        return self.total_energy
    
    def calculate_energy_capacity(self) -> tuple[float, float]:
        return self.total_energy, self.total_capacity

class DataLogger:
    def __init__(self, log_directories : list[str], root_folder : str = None):
        assert log_directories, "No log directories provided"
        self.log_directories : list[str] = log_directories
        self.root_folder : str = root_folder
        self.log_paths : dict = self._create_default_save_paths(self.log_directories)

    def save_data(self, log_directory : str, data : str):
        log_path = os.path.join(self.log_paths[log_directory], f"{log_directory}.log")
        with open(log_path, 'a') as file:
            file.write(data)
    
    def add_save_paths(self, log_directories: list[str]):
        for log_directory in log_directories:
            self.log_directories.append(log_directory)
            base_log_path = os.path.dirname(self.log_paths[self.log_directories[0]])
            log_path = os.path.join(base_log_path, log_directory)
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            self.log_paths[log_directory] = log_path


    def _create_default_save_paths(self, log_directories : list[str]) -> dict[str, str]:

        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory)

        logs_path = os.path.join(parent_directory, 'logs')
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)

        current_date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        current_date_path = os.path.join(logs_path, current_date)

        if self.root_folder:
            root_path = os.path.join(logs_path, self.root_folder)
        else:
            root_path = current_date_path
            
        if not os.path.exists(root_path):
            os.makedirs(root_path)
        else:
            print("[ERROR]Chosen save folder already exists!")
            exit()

        log_paths = {}
        for log_directory in log_directories:
            folder_path = os.path.join(root_path, log_directory)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            log_paths[log_directory] = folder_path
        return log_paths
    

def print_and_log(logger : DataLogger, message : str):
    print(message)
    if not message.endswith("\n"):
        message += "\n"
    logger.save_data("terminal", message)

def append_timestamp(timestamp, data):
    readable_timestamp = time.strftime("%H:%M:%S", time.localtime(timestamp))
    return f"{data}\t{timestamp}\t{readable_timestamp}\n"