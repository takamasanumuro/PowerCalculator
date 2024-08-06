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

def handle_exit():
    pass

def main():

    serial_connection = serial.Serial()
    open_serial_connection(serial_connection, port = "COM3", baudrate = 9600, timeout = 0.1)
    multimeter = YokogawaController(serial_connection)

    try:
        while True:
            value, unit, timestamp = multimeter.read_measurements()

            if value is not None:
                print(f"{Fore.GREEN}Value: {value} {unit}{Style.RESET_ALL}")

            time.sleep(measurement_interval := 0.300)

    except (KeyboardInterrupt, SystemExit): 
        handle_exit()

if __name__ == '__main__':
    main()
