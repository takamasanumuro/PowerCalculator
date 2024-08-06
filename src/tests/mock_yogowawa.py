#Builtin
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

current_directory = os.path.dirname(__file__)
src_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
sys.path.append(src_directory)

#Locals
from controllers import YokogawaController

class TestYokogawaController(unittest.TestCase):

    @patch('serial.Serial')
    def test_parse_response(self, mock_serial):
        responses = [
            "RR,B,+0.0047 VACC",
            "RR,B,+01.978mVAC7",
            "RR,B,+0.0000 VDC4",
            "RR,B,-00.001mVDC4",
            "RR,B,-000.01uADC7",
            "RR,B,-00.002mADC0",
            "RR,B,-0.0008 ADC9"
        ]

        expected_results = [
            (0.0047, 'VACC'),
            (1.978, 'mVAC'),
            (0.0, 'VDC'),
            (-0.001, 'mVDC'),
            (-0.01, 'uADC'),
            (-0.002, 'mADC'),
            (-0.0008, 'ADC')
        ]

        controller = YokogawaController(mock_serial)
        
        for response, expected in zip(responses, expected_results):
            mock_serial.readline.return_value = response.encode()
            value, unit, _ = controller.read_measurements()
            self.assertEqual((value, unit), expected)
        
if __name__ == '__main__':
    unittest.main()