#Builtins
import time 
import serial

#Third party
from colorama import Fore, Style, init
from tenacity import retry, stop_after_attempt, wait_fixed

#Locals
from controllers import *
from analyzers import *
from utils import *
from threads import *

def handle_exit():
    pass

def main():

    valid_multimeter_ports = []
    devices = list_serial_ports()
    for device in devices:
        if "MODEL 92015" in device[1]:
            print(f"Found Yokogawa multimeter: {device[0]}")
            valid_multimeter_ports.append(device[0])
            assert len(valid_multimeter_ports) < 3, "Only two Yokogawa multimeters are supported"
    
    #Automatically open serial ports for multimeters
    multimeter_ports = [serial.Serial(baudrate = 9600, timeout = 0.050) for _ in range(len(valid_multimeter_ports))]
    for port in multimeter_ports:
        port.port = valid_multimeter_ports[multimeter_ports.index(port)]

    relay_port = serial.Serial(baudrate = 9600, timeout = 0.050)
    relay_port.port = "COM17"

    all_serial_ports = multimeter_ports + [relay_port]

    serial_opener_threads = [SerialOpenerThread(serial) for serial in all_serial_ports]
    for opener in serial_opener_threads:
        opener.start()
    
    multimeters = [YokogawaController(serial) for serial in multimeter_ports]

    relay_controller = RelayController(relay_port)
    charge_controller = ChargeController(relay_controller)

    power_analyzer = PowerAnalyzer()
    power_analyzer.log_enabled = True

    keyboard_thread = threading.Thread(target = handle_keyboard_input, args = (charge_controller,))
    keyboard_thread.daemon = True
    keyboard_thread.start()

    try:
        while True:
            values = [(None, None, None) for _ in range(len(valid_multimeter_ports))]
            terminal_output = ""
            for multimeter in multimeters:
                value, unit, timestamp = multimeter.read_measurements()
                values[multimeters.index(multimeter)] = (value, unit, timestamp)
                if value is None:
                    continue
                terminal_output += f"{multimeter.serial.port}: {value} {unit}\t"

            if len(values) == 2 and values[0][0] is not None and values[1][0] is not None:
                #Only measure power if both voltage and current are available
                if not re.search(r"\w?[AV]", values[0][1]) and not re.search(r"\w?[AV]", values[1][1]):
                    continue
                    
                voltage = float(values[0][0])
                current = float(values[1][0])
                power = voltage * current
                power_analyzer.add_entry(values[0][2], voltage, current)
                total_energy = power_analyzer.calculate_energy()
                power_analyzer.save_data()
                terminal_output += f"Power: {power:.4f}W\t\tEnergy: {total_energy:.4f}Wh"

            if terminal_output:
                print(terminal_output)
            time.sleep(measurement_interval := 0.300)

    except (KeyboardInterrupt, SystemExit): 
        for opener in serial_opener_threads:
            opener.stop()
        handle_exit()

if __name__ == '__main__':
    main()
