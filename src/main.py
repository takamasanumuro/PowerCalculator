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
            voltage, current, timestamp = check_readings(power_supply_controller)
            power_analyzer.add_entry(timestamp, voltage, current)
            total_energy = power_analyzer.calculate_energy()
            print(f"{Fore.MAGENTA}Total energy: {total_energy:.3f} Wh{Style.RESET_ALL}")
            time.sleep(measurement_interval:=0.300)

    except (KeyboardInterrupt, SystemExit): 
        handle_exit(None, None, power_supply_controller, power_analyzer)

if __name__ == '__main__':
    main()
