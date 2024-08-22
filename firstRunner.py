import os 
import subprocess

def main():
    script_path = os.path.join('src', 'multimeter.py')

    # Predefine the arguments
    multimeter_ports = ['COM19', 'COM20']  # Replace with your desired ports
    relay_port = 'COM17'  # Replace with your desired relay port
    relay_number = '4'
    folder_name = 'CELL6'  # Replace with your desired folder name

    command = [
        'python', script_path,
        '--multimeter_ports', multimeter_ports[0], multimeter_ports[1],
        '--relay_port', relay_port,
        '--relay_number', relay_number,
        '--folder', folder_name
    ]

    subprocess.run(command)

if __name__ == "__main__":
    main()
