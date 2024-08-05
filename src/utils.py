from colorama import init, Fore, Style
from controllers import PowerSupplyController
import time

def handle_exit(signal, frame, power_supply_controller, power_analyzer):
    power_supply_controller.turn_off()
    power_supply_controller.unlock_front_panel()
    power_supply_controller.close()

    power_analyzer.save_data()

def handle_current(current, threshold, power_supply_controller):
    if current < threshold:
        power_supply_controller.turn_off()

def print_readings(voltage, current, power, total_energy, timestamp):
    print(
        f"{Fore.BLUE}Voltage: {voltage:.2f}V{Style.RESET_ALL}\t"
        f"{Fore.YELLOW}Current: {current:.3f}A{Style.RESET_ALL}\t"
        f"{Fore.RED}Power: {power:.2f}W{Style.RESET_ALL}\t"
        f"{Fore.MAGENTA}Total energy: {total_energy:.3f} Wh{Style.RESET_ALL}\t"
        f"{Fore.GREEN}Timestamp: {timestamp}{Style.RESET_ALL}\n"
    )

def init_colorama():
    init(autoreset=True)