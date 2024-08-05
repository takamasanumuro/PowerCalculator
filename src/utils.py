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

def check_readings(power_supply_controller) -> tuple:
    #Format is {voltage:.2f}\n{current:.3f}\n
    power_supply_controller.ask_readings()
    lines = power_supply_controller.serial.readlines()
    voltage = float(lines[0].strip())
    current = float(lines[1].strip())
    power = voltage * current
    timestamp_epoch_ms = int(time.time() * 1000)
    print(f"{Fore.BLUE}Voltage: {voltage:.2f}V{Style.RESET_ALL}\t{Fore.YELLOW}Current: {current:.3f}A{Style.RESET_ALL}\t{Fore.RED}Power: {power:.2f}W{Style.RESET_ALL}\t{Fore.GREEN}Timestamp: {timestamp_epoch_ms}{Style.RESET_ALL}")
    return (voltage, current, timestamp_epoch_ms)

def init_colorama():
    init(autoreset=True)