#Builtins
import time 
import serial
from collections import namedtuple

#Third party
from colorama import Fore, Style, init
from tenacity import retry, stop_after_attempt, wait_fixed

#Locals
from controllers import *
from analyzers import *
from threads import *

def handle_exit():
    pass

def main():

    multimeter_port_names : list[str] = list_yokogawa_multimeters()

    #Automatically open serial ports for multimeters
    multimeter_ports = [serial.Serial(baudrate = 9600, timeout = 0.050) for _ in range(len(multimeter_port_names))]
    for i in range(len(multimeter_port_names)):
        multimeter_ports[i].port = multimeter_port_names[i]

    relay_port = serial.Serial(baudrate = 9600, timeout = 0.050)
    relay_port.port = "COM17"

    all_ports = multimeter_ports + [relay_port]

    serial_opener_threads = [SerialOpenerThread(port) for port in all_ports]
    for opener in serial_opener_threads:
        opener.daemon = True
        opener.start()
    
    multimeters = [YokogawaController(multimeter_port) for multimeter_port in multimeter_ports]

    relay_controller = RelayController(relay_port, relay_number = 1)
    power_analyzer = PowerAnalyzer()
    logger = DataLogger(["terminal"])
    charge_controller = ChargeController(relay_controller, power_analyzer, logger)

    charge_controller.set_charge_threshold(max_charge_voltage = 3.62, charge_cutoff_current = 0.250)
    charge_controller.set_discharge_threshold(discharge_cutoff_voltage = 2.8)

    
    keyboard_listener_thread = KeyboardListenerThread(charge_controller)
    keyboard_listener_thread.daemon = True
    keyboard_listener_thread.start()

    try:
        while True:
            data_points : DataPoint = [None] * len(multimeters)
            terminal_output_message = ""
            for i, multimeter in enumerate(multimeters):
                data_point = multimeter.read_measurements()
                data_points[i] = data_point
                if data_point.value is None:
                    continue
                terminal_output_message += f"{multimeter.serial.port}: {data_point.value} {data_point.unit}\t"

            is_power_available, voltage, current = check_if_power_available(data_points)
            if is_power_available:
                timestamp = data_points[0].timestamp
                power_analyzer.add_entry(voltage, current, timestamp)
                charge_controller.watch_values(voltage, current, timestamp)
                
                accumulated_energy = power_analyzer.calculate_energy()
                power = voltage * current
                terminal_output_message += f"Power: {power:.4f}W\t\tEnergy: {accumulated_energy:.4f}Wh"

            if terminal_output_message:
                stamped_output_message = append_timestamp(data_points[0].timestamp, terminal_output_message)
                print_and_log(logger, stamped_output_message)

            time.sleep(measurement_interval := 0.200)

    except (KeyboardInterrupt, SystemExit): 
        for opener in serial_opener_threads:
            opener.stop()
        handle_exit()

if __name__ == '__main__':
    main()
