#Builtins
import os
import datetime
import re

def calculate_energy_from_file(filename):
    """Calculate total energy consumption from a file."""
    with open(filename, 'r') as file:
        data = file.read()

    entries = []
    for line in data.strip().split("\n"):
        # Extract date, time, voltage, and current
        date_str, time_str, voltage_str, current_str = re.split(r'\s+', line)
        
        # Combine date and time into a single timestamp
        timestamp_str = f"{date_str} {time_str}"
        timestamp = datetime.datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S')
        
        # Extract voltage and current
        voltage = float(voltage_str.rstrip("V"))
        current = float(current_str.rstrip("A"))
        
        entries.append((timestamp, voltage, current))

    total_energy = 0.0
    for i in range(1, len(entries)):
        t1, v1, i1 = entries[i - 1]
        t2, v2, i2 = entries[i]

        # Calculate the time difference in hours
        delta_time_hours = (t2 - t1).total_seconds() / 3600

        # Calculate average voltage and current
        average_voltage = (v1 + v2) / 2
        average_current = (i1 + i2) / 2

        # Calculate energy in Wh
        energy = average_voltage * average_current * delta_time_hours
        total_energy += energy

    return total_energy

def process_directory(root_dir, output_file):
    """Process all files in the given directory and its subdirectories."""
    with open(output_file, 'w') as outfile:
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                if file == os.path.basename(output_file):
                    continue

                if file.endswith('.txt'):
                    file_path = os.path.join(subdir, file)
                    total_energy = calculate_energy_from_file(file_path)
                    outfile.write(f"{file_path}: {total_energy:.3f} Wh\n")
                    print(f"Processed {file_path}: {total_energy:.3f} Wh")

if __name__ == "__main__":
    # Specify the root directory to search and the output file
    root_directory = os.path.dirname(__file__)  # or specify another directory
    output_filename = os.path.join(root_directory, 'energy_report.txt')

    process_directory(root_directory, output_filename)
    print(f"Energy report saved to {output_filename}")
