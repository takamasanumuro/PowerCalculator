import os
import datetime

class DataLogger:
    def __init__(self, log_directories : list[str]):
        assert log_directories, "No log directories provided"
        self.log_directories : list[str] = log_directories
        self.log_paths : dict = self._create_default_save_paths(self.log_directories)

    def save_data(self, log_directory : str, data : str):
        log_path = os.path.join(self.log_paths[log_directory], f"{log_directory}.log")
        with open(log_path, 'a') as file:
            file.write(data)

    def add_save_path(self, log_directory : str):
        self.log_directories.append(log_directory)
        base_log_path = os.path.dirname(self.log_paths[self.log_directories[0]])
        log_path = os.path.join(base_log_path, log_directory)
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        self.log_paths[log_directory] = log_path


    def _create_default_save_paths(self, log_directories : list[str]) -> dict[str, str]:

        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory)

        logs_path = os.path.join(parent_directory, 'logs')
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)

        current_execution = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        current_execution_path = os.path.join(logs_path, current_execution)
        if not os.path.exists(current_execution_path):
            os.makedirs(current_execution_path)

        log_paths = {}
        for log_directory in log_directories:
            folder_path = os.path.join(current_execution_path, log_directory)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            log_paths[log_directory] = folder_path
        return log_paths
            

            
if __name__ == "__main__":
    
    logger = DataLogger(["test1", "test2"])

    logger.save_data("test1", "Hello, World!\n")
    logger.save_data("test2", "BABA YAGA\n")
    logger.add_save_path("test3")
    logger.save_data("test3", "I am inevitable\n")

    print(logger.log_paths)

