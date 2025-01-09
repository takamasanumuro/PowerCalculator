import os 
import subprocess

def generate_test_folder_name():
    import datetime
    now = datetime.datetime.now()
    return now.strftime('%H-%M-%S')
    

def main():
    script_path = os.path.join('src', 'multimeter.py')


    # Predefine the arguments
    multimeter_ports = ['COM18', 'COM17']  # Replace with your desired ports
    relay_port = 'COM31'  # Replace with your desired relay port
    relay_number = '3' # Replace with your desired relay number
    folder_name = '3S1P'  # Replace with your desired folder name
    add_current_calibration = '0.000'  # Replace with your desired current calibration value
    charge_cutoff_voltage = '3.640' #Must be above this value to cut off charging
    charge_cutoff_current = '0.040' #Must be below this value to cut off charging
    discharge_cutoff_voltage = '2.00' #Must be below this value to cut off discharging

    command = [
        'python', script_path,
        '--multimeter_ports', multimeter_ports[0], multimeter_ports[1],
        '--relay_port', relay_port,
        '--relay_number', relay_number,
        '--folder', folder_name,
        '--charge_cutoff_voltage', charge_cutoff_voltage,
        '--charge_cutoff_current', charge_cutoff_current,
        '--discharge_cutoff_voltage', discharge_cutoff_voltage
    ]

    try:
        subprocess.run(command)
    except (subprocess.SubprocessError):
        print("[RUNNER]Error running subprocess")
    except (KeyboardInterrupt, SystemExit):
        print("[RUNNER]Exiting")

if __name__ == "__main__":
    main()
