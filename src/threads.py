#Builtins
import threading
from queue import Queue, Empty
import time
import serial


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