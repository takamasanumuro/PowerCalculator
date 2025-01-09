#Builtins
import time 
import serial
from collections import namedtuple
import argparse

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

    parser = argparse.ArgumentParser(description = "Program to control charge / discharge cycles via serial-connected multimeters and relays")
    parser.add_argument("--multimeter_ports", nargs = 2, help = "Specify two multimeter ports (eg., COM3 COM4)")
    parser.add_argument("--relay_port", default = "COM30", help = "Specify the relay port")
    parser.add_argument("--relay_number", default = '1', help = "Specify the relay number on the relay board")
    parser.add_argument("--folder", default = None, help = "Name of file to save")
    parser.add_argument("--add_current_calibration", default = '0.0', help = "Add a current calibration value to the current")
    parser.add_argument("--charge_cutoff_voltage", default = '3.65', help = "Specify the charge cutoff voltage")
    parser.add_argument("--charge_cutoff_current", default = '0.600', help = "Specify the charge cutoff current")
    parser.add_argument("--discharge_cutoff_voltage", default = '2.50', help = "Specify the discharge cutoff voltage")
    args = parser.parse_args()

    multimeter_port_names : list[str] = args.multimeter_ports
    if not multimeter_port_names:
        multimeter_port_names = list_yokogawa_multimeters()

    print('\n' * 2)
    program_args_intro = "-------------Chosen arguments-------------"
    print(program_args_intro)
    print(f"Multimeter Ports = {multimeter_port_names}")
    print(f"Relay Port: {args.relay_port}")
    print(f"Relay Number: {args.relay_number}")
    print(f"Folder = {args.folder}")
    print(f"Add Current Calibration = {args.add_current_calibration}")
    print(f"Charge Cutoff Voltage = {args.charge_cutoff_voltage}")
    print(f"Charge Cutoff Current = {args.charge_cutoff_current}")
    print(f"Discharge Cutoff Voltage = {args.discharge_cutoff_voltage}")
    print("-"*len(program_args_intro))
    print('\n' * 2)

    #Automatically open serial ports for multimeters
    multimeter_ports = [serial.Serial(baudrate = 9600, timeout = 0.050) for _ in range(len(multimeter_port_names))]
    for i in range(len(multimeter_port_names)):
        multimeter_ports[i].port = multimeter_port_names[i]

    relay_port = serial.Serial(baudrate = 9600, timeout = 0.500)
    relay_port.port = args.relay_port
    disable_reset_on_connect(relay_port)
    relay_port.open()
    relay_port.reset_output_buffer()
    relay_port.close()

    serial_opener_threads = [SerialOpenerThread(port) for port in multimeter_ports]
    for opener in serial_opener_threads:
        opener.daemon = True
        opener.start()
    
    multimeters = [YokogawaController(multimeter_port) for multimeter_port in multimeter_ports]

    relay_controller = RelayController(relay_port, relay_number = int(args.relay_number))
    power_analyzer = PowerAnalyzer()
    logger = DataLogger(["terminal"], args.folder)
    charge_controller = ChargeController(relay_controller, power_analyzer, logger)

    charge_controller.set_charge_threshold(float(args.charge_cutoff_voltage), float(args.charge_cutoff_current))
    charge_controller.set_discharge_threshold(float(args.discharge_cutoff_voltage))

    
    keyboard_listener_thread = KeyboardListenerThread(keyboard_input_callback, charge_controller)
    keyboard_listener_thread.daemon = True
    keyboard_listener_thread.start()

    try:
        while True:
            data_points : list[DataPoint] = [DataPoint(None, None, None)] * len(multimeters)
            terminal_output_message = ""
            for i, multimeter in enumerate(multimeters):
                raw_data_point = multimeter.read_measurements()
                if raw_data_point.value is None:
                    continue
                
                if is_current_unit(raw_data_point.unit):
                    data_point = DataPoint(raw_data_point.value + float(args.add_current_calibration), raw_data_point.unit, raw_data_point.timestamp)
                else:
                    data_point = raw_data_point   
                data_points[i] = data_point
                terminal_output_message += f"{multimeter.serial.port}: {data_point.value:.4f} {data_point.unit}\t"

            is_power_available, voltage, current = check_if_power_available(data_points)
            timestamp = get_timestamp(data_points)
            if is_power_available:
                #current += float(args.add_current_calibration)
                power_analyzer.add_entry(voltage, current, timestamp)
                charge_controller.watch_values(voltage, current, timestamp)
                
                accumulated_energy = power_analyzer.calculate_energy()
                power = voltage * current
                terminal_output_message += f"Power: {power:.4f}W\t\tEnergy: {accumulated_energy:.4f}Wh"

            if terminal_output_message:
                folder_str = f"\t{args.folder}" if args.folder else ""
                output_message_with_folder = terminal_output_message + folder_str
                output_message_with_mode = f"{output_message_with_folder}\t{charge_controller.get_mode()}"
                stamped_output_message = append_timestamp(timestamp, output_message_with_mode)
                print_and_log(logger, stamped_output_message)

            time.sleep(measurement_interval := 0.200)

    except (KeyboardInterrupt, SystemExit): 
        for opener in serial_opener_threads:
            opener.stop()
        handle_exit()

if __name__ == '__main__':
    main()
