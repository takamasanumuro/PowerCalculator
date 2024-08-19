#builtins
import unittest
from unittest.mock import MagicMock

import os
import sys

current_directory = os.path.dirname(__file__)
src_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
sys.path.append(src_directory)

#locals
from controllers import *


class TestChargeController(unittest.TestCase):

    def setUp(self):
        # Mock the RelayController and PowerAnalyzer
        self.mock_relay_controller = MagicMock()
        self.power_analyzer = PowerAnalyzer()

        # Mock the logger
        self.mock_logger = MagicMock()

        # Initialize the ChargeController with mocks
        self.charge_controller = ChargeController(
            relay_controller=self.mock_relay_controller,
            power_analyzer=self.power_analyzer,
            logger=self.mock_logger
        )

        # Set thresholds for testing
        self.charge_controller.set_charge_threshold(max_charge_voltage=3.65, charge_cutoff_current=0.1)
        self.charge_controller.set_discharge_threshold(discharge_cutoff_voltage=2.8)

        self.charge_controller.set_mode("cycle")

    def test_charge_controller_logic(self):
        # Simulate voltage and current readings
        charge_data = [
            (3.50, 0.5),  # Below max charge voltage
            (3.55, 0.5),  
            (3.60, 0.5),  # Above max charge voltage
            (3.65, 0.5),   
            (3.65, 0.3),  
            (3.65, 0.2),
            (3.65, 0.1),  # At the discharge cutoff point
            (3.65, 0.0),  # Below discharge cutoff voltage
        ]

        for voltage, current in charge_data:
            timestamp = time.time() * 1000  # Simulate a timestamp in milliseconds
            self.power_analyzer.add_entry(voltage, current, timestamp)
            self.charge_controller.watch_values(voltage, current, timestamp)

            # Reset mock to test the next data point
            self.mock_relay_controller.reset_mock()

        discharge_data = [
            (3.65, 0.5),  # Above discharge cutoff voltage
            (3.60, 0.5),
            (3.55, 0.5),
            (3.50, 0.5),
            (3.45, 0.5),
            (3.40, 0.5),
            (3.35, 0.5),
            (3.30, 0.5),
            (3.25, 0.5),
            (3.20, 0.5),
            (3.15, 0.5),
            (3.10, 0.5),
            (3.05, 0.5),
            (3.00, 0.5),
            (2.95, 0.5),
            (2.90, 0.5),
            (2.85, 0.5),
            (2.80, 0.5), # At the discharge cutoff point
            (2.75, 0.5), # Below discharge cutoff voltage
        ]

        for voltage, current in discharge_data:
            timestamp = time.time() * 1000
            self.power_analyzer.add_entry(voltage, current, timestamp)
            self.charge_controller.watch_values(voltage, current, timestamp)

        recharge_data = [
            (2.80, 0.5), # Above discharge cutoff voltage
            (2.85, 0.5),
            (2.90, 0.5),
            (2.95, 0.5),
            (3.00, 0.5),
            (3.05, 0.5),
            (3.10, 0.5),
            (3.15, 0.5),
            (3.20, 0.5),
            (3.25, 0.5),
            (3.30, 0.5),
            (3.35, 0.5),
            (3.40, 0.5),
            (3.45, 0.5),
            (3.50, 0.5),
            (3.55, 0.5),
            (3.60, 0.5),
            (3.65, 0.5),
            (3.65, 0.3),
            (3.65, 0.2),
            (3.65, 0.1), # At the discharge cutoff point
            (3.65, 0.0), # Below discharge cutoff voltage
        ]

        for voltage, current in recharge_data:
            timestamp = time.time() * 1000
            self.power_analyzer.add_entry(voltage, current, timestamp)
            self.charge_controller.watch_values(voltage, current, timestamp)



if __name__ == '__main__':
    unittest.main()
