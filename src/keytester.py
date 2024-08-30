

import threading
import getpass

class KeyboardThread(threading.Thread):
    
    def __init__(self, input_callback = None, name = "keyboard-input-thread"):
        self.input_callback = input_callback
        super(KeyboardThread, self).__init__(name = name, daemon = True)
        self.start()

    def run(self):
        while True:
            self.input_callback(getpass.getpass(""))


def function_to_be_run_as_callback(input : str):
    #evaluate the input
    match input:
        case 'K':
            print(f"Cycle mode")
        case 'R':
            print(f"Toggling relay")

keyboard_thread = KeyboardThread(function_to_be_run_as_callback)

while True:
    import time
    time.sleep(1)