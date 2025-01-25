#Builtins
import time 
import serial
from collections import namedtuple
import argparse
import threading

#Third party
from colorama import Fore, Style, init
from tenacity import retry, stop_after_attempt, wait_fixed
import matplotlib.pyplot as plot
from matplotlib.animation import FuncAnimation
from queue import Queue, Empty

#Locals
from controllers import *
from analyzers import *
from threads import *
import sounds

#Thread safe queue
data_queue = Queue()

#Setup the live plot
voltage_values =  []
current_values =  []
timestamps     =  []

figure, axes = plot.subplots(2, 1, figsize = (10, 6))

#Voltage plot
axes[0].set_title("Voltage")
axes[0].set_ylabel("Voltage (V)")
axes[0].set_xlabel("Time (s)")
axes[0].set_xlim(0, 10)
axes[0].set_ylim(2, 4)
axes[0].legend(loc = "upper right")
line_voltage, = axes[0].plot([], [], label = "Voltage", color = "blue")

#Current plot
axes[1].set_title("Current")
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("Current (A)")
axes[1].set_xlim(0, 10)
axes[1].set_ylim(-5, 5)
axes[1].legend(loc = "upper right")
line_current, = axes[1].plot([], [], label = "Current", color = "red")

#Update function for the live plot
def update_plot(frame):
    global voltage_values, current_values, timestamps

    try:
        while True:
            voltage, current, timestamp = data_queue.get_nowait()
            voltage_values.append(voltage)
            current_values.append(current)
            timestamps.append(timestamp)
    except Empty:
        pass

    if len(timestamps) > 0:
        #Update data for voltage
        line_voltage.set_data(timestamps, voltage_values)
        axes[0].set_xlim(timestamps[0], timestamps[-1])

        #Update data for current
        line_current.set_data(timestamps, current_values)
        axes[1].set_xlim(timestamps[0], timestamps[-1])

        axes[0].relim()
        axes[0].autoscale_view()
        axes[1].relim()
        axes[1].autoscale_view()
    
    return line_voltage, line_current

animation = FuncAnimation(figure, update_plot, interval = 100)

def start_plot():
    plot.tight_layout()
    plot.show()

def handle_exception(exception : Exception, runner_name : str):
    timestamp = time.strftime("%m-%d %H:%M:%S")
    message = f"[{timestamp}]\t[{runner_name}]\tType: {type(exception).__name__}\tMessage: {exception}\n"
    file = open("error_log.txt", "a")
    file.write(message)
    file.close()

    #send to ntfy.sh/alertas-bateria-erros
    chime.theme('pokemon')
    chime.error()
    requests.post("https://ntfy.sh/alertas-bateria", data = f"Error:{message}")
    time.sleep(4)


def main_loop(args, multimeters, relay_controller, power_analyzer, logger, charge_controller):
    start_time = time.time()
    try:
        while True:
            data_points: list[DataPoint] = [DataPoint(None, None, None)] * len(multimeters)
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
                relative_timestamp_seconds = timestamp - start_time
                data_queue.put((voltage, current, relative_timestamp_seconds))
                power_analyzer.add_entry(voltage, current, timestamp)
                charge_controller.watch_values(voltage, current, timestamp)
                
                accumulated_energy = power_analyzer.calculate_energy()
                power = voltage * current
                terminal_output_message += f"Power: {power:.4f}W\t\tEnergy: {accumulated_energy:.4f}Wh"

            if terminal_output_message:
                folder_str = f"\t{args.folder}" if args.folder else ""
                output_message_with_folder = terminal_output_message + folder_str
                output_message_with_mode = f"{output_message_with_folder}\t{charge_controller.get_mode()}"
                output_message_with_mode = f"{output_message_with_mode}\t{time.time() - start_time:.2f}s"
                stamped_output_message = append_timestamp(timestamp, output_message_with_mode)
                print_and_log(logger, stamped_output_message)

            time.sleep(measurement_interval := 0.100)

    except (KeyboardInterrupt, SystemExit): 
        print(Fore.RED + "Exiting..." + Style.RESET_ALL)
    except Exception as exception:
        print(Fore.RED + f"Error: {exception}" + Style.RESET_ALL)
        handle_exception(exception, args.runner_name)
    finally:
        charge_controller.set_mode("monitor")

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
    parser.add_argument("--runner_name", default = 'multimeter.py', help = "Specify the name of the runner script")
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
    print(f"Runner Name = {args.runner_name}")
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
    charge_controller.set_mode("monitor")
    
    keyboard_listener_thread = KeyboardListenerThread(keyboard_input_callback, charge_controller)
    keyboard_listener_thread.daemon = True
    keyboard_listener_thread.start()

    main_thread = threading.Thread(target=main_loop, args=(args, multimeters, relay_controller, power_analyzer, logger, charge_controller))
    main_thread.daemon = True
    main_thread.start()

    window_title = args.runner_name
    figure.suptitle(args.folder)
    figure.canvas.manager.set_window_title(window_title)
    start_plot()
    main_thread.join()

if __name__ == '__main__':
    main()
