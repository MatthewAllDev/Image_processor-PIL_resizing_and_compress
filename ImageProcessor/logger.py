from datetime import datetime
from codetiming import Timer
import os


class Logger:
    def __init__(self, log_path: str):
        self.log: str = log_path
        self.timer: Timer = Timer(text='')
        self.overall_input_weight: int = 0
        self.overall_output_weight: int = 0

    def start_resizing(self, images_count: int, weight: int):
        self.overall_input_weight = weight
        self.overall_output_weight = 0
        self.timer.start()
        self.write(f'\n{"_" * 120}\n'
                   f'Start resizing {images_count} images. '
                   f'Overall size: {round(self.overall_input_weight / (1024 ** 2), 2)}MB '
                   f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    def start_cropping(self, images_count: int, weight: int):
        self.overall_input_weight = weight
        self.overall_output_weight = 0
        self.timer.start()
        self.write(f'\n{"_" * 120}\n'
                   f'Start cropping {images_count} images. '
                   f'Overall size: {round(self.overall_input_weight / (1024 ** 2), 2)}MB '
                   f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    def start_compressing(self, images_count: int, weight: int):
        self.overall_input_weight = weight
        self.overall_output_weight = 0
        self.timer.start()
        self.write(f'\n{"_" * 120}\n'
                   f'Start compressing {images_count} images. '
                   f'Overall size: {round(self.overall_input_weight / (1024 ** 2), 2)}MB '
                   f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')

    def resizing_message(self, file: str, input_size: tuple, output_size: tuple, input_weight: int, output_weight: int):
        self.overall_output_weight += output_weight
        self.write(f'\nResized: {self.format_path(file)} '
                   f'| {self.format_string(str(self.get_size(input_size)), 9, "left")} '
                   f'/ {self.format_string(str(self.get_size(output_size)), 9, "right")} '
                   f'| {self.format_string(str(round(input_weight / 1024, 2)), 11, "left")}KB '
                   f'/ {self.format_string(str(round(output_weight / 1024, 2)) + "KB", 11, "right")} '
                   f'| -{round(100 - (output_weight / input_weight * 100), 2)}%')

    def cropping_message(self, file: str, input_size: tuple, output_size: tuple, input_weight: int, output_weight: int):
        self.write(f'\nCropped: {self.format_path(file)} '
                   f'| {self.format_string(str(self.get_size(input_size)), 9, "left")} '
                   f'/ {self.format_string(str(self.get_size(output_size)), 9, "right")} '
                   f'| {self.format_string(str(round(input_weight / 1024, 2)), 11, "left")}KB '
                   f'/ {self.format_string(str(round(output_weight / 1024, 2)) + "KB", 11, "right")} '
                   f'| -{round(100 - (output_weight / input_weight * 100), 2)}%')

    def compressing_massage(self, file: str, input_weight: int, output_weight: int):
        self.overall_output_weight += output_weight
        self.write(f'\nCompressed: {self.format_path(file)} '
                   f'| {self.format_string(str(round(input_weight / 1024, 2)), 11, "left")}KB '
                   f'/ {self.format_string(str(round(output_weight / 1024, 2)) + "KB", 11, "right")} '
                   f'| -{round(100 - (output_weight / input_weight * 100), 2)}%')

    def stop_resizing(self, overall_output_weight: int = None):
        if overall_output_weight is not None:
            self.overall_output_weight = overall_output_weight
        time: float = self.timer.stop()
        self.write(f'\n\nResizing complete. '
                   f'Elapsed time: {round(time, 2)}s. '
                   f'Total output size: {round(self.overall_output_weight / (1024 ** 2), 2)}MB '
                   f'-{round(100 - (self.overall_output_weight / self.overall_input_weight * 100), 2)}%.')

    def stop_cropping(self, overall_output_weight: int = None):
        if overall_output_weight is not None:
            self.overall_output_weight = overall_output_weight
        time: float = self.timer.stop()
        self.write(f'\n\nResizing complete. '
                   f'Elapsed time: {round(time, 2)}s. '
                   f'Total output size: {round(self.overall_output_weight / (1024 ** 2), 2)}MB '
                   f'-{round(100 - (self.overall_output_weight / self.overall_input_weight * 100), 2)}%.')

    def stop_compressing(self):
        time: float = self.timer.stop()
        self.write(f'\n\nCompressing complete. '
                   f'Elapsed time: {round(time, 2)}s. '
                   f'Total output size: {round(self.overall_output_weight / (1024 ** 2), 2)}MB '
                   f'-{round(100 - (self.overall_output_weight / self.overall_input_weight * 100), 2)}%.')

    def error_message(self, text: str):
        self.write(f'\n{"~" * 120}\n'
                   f'ERROR: {text}'
                   f'\n{"~" * 120}')

    def write(self, text: str):
        with open(self.log, 'a', encoding='utf-8') as log:
            log.write(text)

    @staticmethod
    def format_string(string: str, size: int, position: str) -> str:
        space_count: int = size - len(string)
        if position == 'left':
            return f'{" " * space_count}{string}'
        elif position == 'right':
            return f'{string}{" " * space_count}'
        else:
            raise AttributeError('Position must be equal to "right" or "left".')

    @staticmethod
    def format_path(path: str) -> str:
        space_count: int = 30 - len(os.path.basename(path))
        return f'{" " * (space_count // 2 + space_count % 2)}{path}{" " * (space_count // 2)}'

    @staticmethod
    def get_size(size: tuple) -> str:
        return f'{size[0]}x{size[1]}'
