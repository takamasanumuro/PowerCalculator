import os 
import subprocess

def generate_test_folder_name():
    import datetime
    now = datetime.datetime.now()
    return now.strftime('%H-%M-%S')
    

def main():
    script_path = os.path.join('src', 'multimeter.py')

    # Predefine the arguments
    multimeter_ports = ['COM19', 'COM20']  # Replace with your desired ports
    relay_port = 'COM30'  # Replace with your desired relay port
    relay_number = '1' # Replace with your desired relay number
    folder_name = '15S8P'  # Replace with your desired folder name

    command = [
        'python', script_path,
        '--multimeter_ports', multimeter_ports[0], multimeter_ports[1],
        '--relay_port', relay_port,
        '--relay_number', relay_number,
        '--folder', folder_name,

    ]

    try:
        subprocess.run(command)
    except (subprocess.SubprocessError):
        print("[RUNNER]Error running subprocess")
    except (KeyboardInterrupt, SystemExit):
        print("[RUNNER]Exiting")

if __name__ == "__main__":
    main()
