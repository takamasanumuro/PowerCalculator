import time 
from colorama import Fore, Style, init

from controllers import PowerSupplyController
from analyzers import PowerAnalyzer
from utils import *

def main():
    power_supply_controller = PowerSupplyController('COM14')
    power_supply_controller.turn_on()

    power_analyzer = PowerAnalyzer()
    power_analyzer.log_enabled = True

    try:
        while True:
            voltage, current, power, timestamp = power_supply_controller.read_measurements()
            power_analyzer.add_entry(timestamp, voltage, current)
            total_energy = power_analyzer.calculate_energy()
            print_readings(voltage, current, power, total_energy, timestamp)
            time.sleep(measurement_interval:=0.300)

    except (KeyboardInterrupt, SystemExit): 
        handle_exit(None, None, power_supply_controller, power_analyzer)

if __name__ == '__main__':
    main()
