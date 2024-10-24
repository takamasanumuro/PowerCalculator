import os 
import subprocess
import datetime


def create_test_folder() -> str:
    folder_name = 'TEST'
    current_date = datetime.datetime.now().strftime('%H-%M-%S')
    test_folder_name = f'{folder_name}_{current_date}'
    return test_folder_name


def main():
    script_path = os.path.join('src', 'multimeter.py')

    # Predefine the arguments
    multimeter_ports = ['COM17', 'COM18']  # Replace with your desired ports
    relay_port = 'COM31'  # Replace with your desired relay port
    relay_number = '4'
    folder_name = 'A3'  # Replace with your desired folder name
    add_current_calibration = '0.000'  # Replace with your desired current calibration value

    command = [
        'python', script_path,
        '--multimeter_ports', multimeter_ports[0], multimeter_ports[1],
        '--relay_port', relay_port,
        '--relay_number', relay_number,
        '--folder', folder_name,
        '--add_current_calibration', add_current_calibration
    ]

    subprocess.run(command)

if __name__ == "__main__":
    main()
