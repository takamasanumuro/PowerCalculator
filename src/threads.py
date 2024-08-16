#Builtins
import threading
from queue import Queue, Empty
import time
import serial

#Third party
import keyboard

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
                print("Mode set to monitor")
                time.sleep(1.000)

            if keyboard.is_pressed("ctrl+k"):
                charge_controller.set_mode("cycle")
                print("Mode set to cycle")
                time.sleep(1.000)

            if keyboard.is_pressed("ctrl+r"):
                charge_controller.flip_relay()
                print("Relay flipped")
                time.sleep(1.000)

            time.sleep(0.100)
            
        except KeyboardInterrupt:
            exit()

class KeyboardListenerThread(threading.Thread):
    def __init__(self, charge_controller):
        threading.Thread.__init__(self)
        self.charge_controller = charge_controller
        self.running = True
        self.daemon = True

    def run(self):
        handle_keyboard_input(self.charge_controller)

    def stop(self):
        self.running = False

    


