#Builtins
import unittest
from unittest.mock import patch

import os
import sys

current_directory = os.path.dirname(__file__)
src_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
sys.path.append(src_directory)
#Locals
from utils import *

class TestListYokogawaMultimeters(unittest.TestCase):
    
    @patch('utils.list_serial_ports')
    def test_no_multimeters_found(self, mock_list_serial_ports):
        mock_list_serial_ports.return_value = []
        with self.assertRaises(AssertionError) as context:
            list_yokogawa_multimeters()
        self.assertEqual(str(context.exception), "No Yokogawa multimeters found")

    @patch('utils.list_serial_ports')
    def test_one_multimeter_found(self, mock_list_serial_ports):
        mock_list_serial_ports.return_value = [SerialPortInfo("COM1", "MODEL 92015")]
        result = list_yokogawa_multimeters()
        self.assertEqual(result, ["COM1"])

    @patch('utils.list_serial_ports')
    def test_two_multimeters_found(self, mock_list_serial_ports):
        mock_list_serial_ports.return_value = [SerialPortInfo("COM1", "MODEL 92015"), SerialPortInfo("COM2", "MODEL 92015")]
        result = list_yokogawa_multimeters()
        self.assertEqual(result, ["COM1", "COM2"])

    @patch('utils.list_serial_ports')
    def test_three_multimeters_found(self, mock_list_serial_ports):
        mock_list_serial_ports.return_value = [SerialPortInfo("COM1", "MODEL 92015"), SerialPortInfo("COM2", "MODEL 92015"), SerialPortInfo("COM3", "MODEL 92015")]
        with self.assertRaises(AssertionError) as context:
            list_yokogawa_multimeters()
        self.assertEqual(str(context.exception), "Only two Yokogawa multimeters are supported")


if __name__ == '__main__':
    unittest.main()
