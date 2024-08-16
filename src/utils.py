#Builtins
import time
from serial import Serial
from collections import namedtuple

#Third party
from colorama import init, Fore, Style
from tenacity import retry, stop_after_attempt, wait_fixed

#locals
from controllers import PowerSupplyController

@retry(wait = wait_fixed(3))
def open_serial_connection(serial: Serial, port: str, baudrate: int, timeout: float):
    print(f"Opening serial connection on port {port} with baudrate {baudrate} and timeout {timeout}")
    serial.port = port
    serial.baudrate = baudrate
    serial.timeout = timeout
    serial.open()

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

SerialPortInfo = namedtuple("SerialPortInfo", ["device", "description"])

def list_serial_ports_verbose() -> None:
    from serial.tools.list_ports import comports
    ports = comports()
    for port in ports:
        print(f"Device: {port.device}")
        print(f"Name: {port.name}")
        print(f"Description: {port.description}")
        print(f"HWID: {port.hwid}")
        print(f"VID: {port.vid}")
        print(f"PID: {port.pid}")
        print(f"Serial number: {port.serial_number}")
        print(f"Location: {port.location}")
        print(f"Manufacturer: {port.manufacturer}")
        print(f"Product: {port.product}")
        print(f"Interface: {port.interface}")
        print("")

def list_serial_ports() -> list[SerialPortInfo]:
    from serial.tools.list_ports import comports
    return [SerialPortInfo(port.device, port.description) for port in comports()]

def list_yokogawa_multimeters() -> list[str]:
    devices = list_serial_ports()
    valid_multimeter_ports = [device.device for device in devices if "MODEL 92015" in device.description]
    assert len(valid_multimeter_ports) > 0, "No Yokogawa multimeters found"
    assert len(valid_multimeter_ports) < 3, "Only two Yokogawa multimeters are supported"
    
    return valid_multimeter_ports

