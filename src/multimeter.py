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

    valid_ports = []
    devices = list_serial_ports()
    for device in devices:
        if "MODEL 92015" in device[1]:
            print(f"Found Yokogawa multimeter: {device[0]}")
            valid_ports.append(device[0])
            assert len(valid_ports) < 3, "Only two Yokogawa multimeters are supported"
    

    serial_ports = [serial.Serial(baudrate = 9600, timeout = 0.050) for _ in range(len(valid_ports))]
    for port in serial_ports:
        port.port = valid_ports[serial_ports.index(port)]

    serial_opener_threads = [SerialOpenerThread(serial) for serial in serial_ports]
    for opener in serial_opener_threads:
        opener.start()
    
    multimeters = [YokogawaController(serial) for serial in serial_ports]

    power_analyzer = PowerAnalyzer()
    power_analyzer.log_enabled = True

    try:
        while True:
            values = [(None, None, None) for _ in range(len(valid_ports))]
            terminal_output = ""
            for multimeter in multimeters:
                value, unit, timestamp = multimeter.read_measurements()
                values[multimeters.index(multimeter)] = (value, unit, timestamp)
                if value is None:
                    continue
                terminal_output += f"{multimeter.serial.port}: {value} {unit}\t"

            if len(values) == 2 and values[0][0] is not None and values[1][0] is not None:
                #Only measure power if both voltage and current are available
                if re.search(r"\w?[AV]", values[0][1]) and re.search(r"\w?[AV]", values[1][1]):
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
