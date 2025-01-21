import csv
import os
from dataclasses import dataclass, asdict, fields
from typing import Optional, Union, List, Type

@dataclass
class DataPointClass:
    voltage: Optional[float]
    current: Optional[float]
    new_field : Optional[float]
    power: Optional[float]
    ahour: Optional[float]
    whour: Optional[float]
    timestamp: float
    is_valid: bool

def serialize_to_csv(data_points : Union[object, List[object]],
                     data_point_type : Type,
                     file_path : str):
    if isinstance(data_points, data_point_type):
        data_points = [data_points]
    elif not isinstance(data_points, list):
        raise ValueError(f"Expected {data_point_type}, got {type(data_points)}")
    
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode = 'a' if file_exists else 'w', newline = '') as file:
        writer = csv.DictWriter(file, fieldnames =  [field.name for field in fields(data_point_type)], delimiter = ';')

        if not file_exists:
            writer.writeheader()
        for data_point in data_points:
            writer.writerow(asdict(data_point))

def generate_folder():
    import datetime
    now = datetime.datetime.now()
    return now.strftime('data_points_%H-%M-%S')
folder = generate_folder()

# Example usage with a single data point
single_data_point = DataPointClass(voltage=3.7, new_field= 2.0, current=1.5, power=5.55, ahour=0.1, whour=0.37, timestamp=1625247600.0, is_valid=True)
serialize_to_csv(single_data_point, DataPointClass, 'folder')

# Example usage with a list of data points
data_points = [
    DataPointClass(voltage=3.7, new_field= 2.5, current=1.5, power=5.55, ahour=0.1, whour=0.37, timestamp=1625247600.0, is_valid=True),
    DataPointClass(voltage=3.8, new_field= 2.4, current=1.6, power=6.08, ahour=0.2, whour=0.76, timestamp=1625247660.0, is_valid=True)
]

serialize_to_csv(data_points, DataPointClass, 'folder')

#get vscode to open the csv
