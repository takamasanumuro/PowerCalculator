#Builtins
import threading
import time
import serial
import getpass

#Third party
import keyboard
import chime

#Locals
from controllers import *
from utils import *

@retry(wait = wait_fixed(3))
def open_serial_port(serial):
    try:
        serial.open()
    except serial.SerialException as e:
        raise e

class MultimeterThread(threading.Thread):
    def __init__(self, serial, queue, interval):
        threading.Thread.__init__(self)
        self.serial = serial
        self.queue = queue
        self.interval = interval
        self.running = True

    def run(self):
        print(f"Starting thread for {self.serial}")
        assert self.serial.port is not None, "Port was not set"
        assert self.serial.baudrate is not None, "Baudrate was not set"

        try:
            open_serial_port(self.serial)
        except serial.SerialException as e:
            print(f"Could not open serial port: {e}")
            return
        multimeter = YokogawaController(self.serial)

        while self.running:
            value, unit, timestamp = multimeter.read_measurements()
            if value is not None:
                self.queue.put((value, unit, timestamp))
            time.sleep(self.interval)

    def stop(self):
        self.running = False

class SerialOpenerThread(threading.Thread):
    def __init__(self, serial):
        threading.Thread.__init__(self)
        self.serial = serial
        self.running = True

    def run(self):
        print(f"Starting thread for {self.serial}")
        assert self.serial.port is not None, "Port was not set"
        assert self.serial.baudrate is not None, "Baudrate was not set"

        try:
            open_serial_port(self.serial)
        except serial.SerialException as e:
            print(f"Could not open serial port: {e}")
            return
    
    def stop(self):
        self.running = False


def handle_keyboard_input(charge_controller : ChargeController):
    while True:
        try:
            if keyboard.is_pressed("ctrl+m"):
                charge_controller.set_mode("monitor")
                print("[CONTROLLER]Mode set to monitor")
                time.sleep(1.000)

            if keyboard.is_pressed("ctrl+k"):
                charge_controller.set_mode("cycle")
                print("[CONTROLLER]Mode set to cycle")
                previous_theme = chime.theme()
                chime.theme('pokemon')
                chime.success()
                time.sleep(6.000)
                chime.theme(previous_theme)

            if keyboard.is_pressed("ctrl+r"):
                charge_controller.flip_relay()
                print("[CONTROLLER]Relay flipped")
                time.sleep(1.000)

            time.sleep(0.100)
            
        except KeyboardInterrupt:
            exit()


def keyboard_input_callback(charge_controller : ChargeController, command : str):
    match command:
        case 'K':
            if (charge_controller.mode == "cycle"):
                return
            charge_controller.set_mode("cycle")
            print("[CONTROLLER]Mode set to cycle")
            previous_theme = chime.theme()
            chime.theme('big-sur')
            chime.success()
            chime.theme(previous_theme)
        case 'R':
            previous_theme = chime.theme()
            chime.theme('big-sur')
            chime.success()
            chime.theme(previous_theme)
            charge_controller.flip_relay()
            print("[CONTROLLER]Relay flipped")
            time.sleep(1.000)
    
    time.sleep(0.100)
    

class KeyboardListenerThread(threading.Thread):
    def __init__(self, input_callback, charge_controller):
        self.input_callback = input_callback
        threading.Thread.__init__(self)
        self.charge_controller = charge_controller
        self.daemon = True

    def run(self):
        try:
            while True:
                self.input_callback(self.charge_controller, getpass.getpass(""))
        except (KeyboardInterrupt):
            exit()
            
    def stop(self):
        self.running = False

    


