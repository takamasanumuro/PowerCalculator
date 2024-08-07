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

    MAX_DEVICES = 2

    serial_ports = [serial.Serial(baudrate = 9600, timeout = 0.050) for _ in range(MAX_DEVICES)]
    serial_ports[0].port = "COM3"
    serial_ports[1].port = "COM4"

    serial_opener_threads = [SerialOpenerThread(serial) for serial in serial_ports]
    for opener in serial_opener_threads:
        opener.start()
    
    multimeters = [YokogawaController(serial) for serial in serial_ports]

    try:
        while True:
            values = [(None, None, None) for _ in range(MAX_DEVICES)]
            output = ""
            for multimeter in multimeters:
                value, unit, timestamp = multimeter.read_measurements()
                values[multimeters.index(multimeter)] = (value, unit, timestamp)
                if value is None:
                    continue
                output += f"{multimeter.serial.port}: {value} {unit}\t"

            if values[0][0] is not None and values[1][0] is not None:
                if re.search(r"\w?[AV]", values[0][1]) and re.search(r"\w?[AV]", values[1][1]):
                    voltage = float(values[0][0])
                    current = float(values[1][0])
                    power = voltage * current
                    output += f"Power: {power:.2f}W"

            if output:
                print(output)
            time.sleep(measurement_interval := 0.300)

    except (KeyboardInterrupt, SystemExit): 
        for opener in serial_opener_threads:
            opener.stop()
        handle_exit()

if __name__ == '__main__':
    main()
