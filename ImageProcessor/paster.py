import os
from PIL import Image
from .logger import Logger


class Paster:
    def __init__(self,
                 output_directory: str = None,
                 ratio: float = None,
                 logger: Logger = None):
        self.output_directory: str = output_directory
        self.ratio: float = ratio
        self.logger: Logger = logger
        if output_directory is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

    def make_image(self, path: str, ratio: float = None) -> str:
        if not ratio:
            ratio: float = self.ratio
            if not self.ratio:
                raise RuntimeError('Ratio not set!')
        if not os.path.exists(path):
            raise RuntimeError('File not found!')
        if self.output_directory is not None:
            output_path: str = f'{self.output_directory}/{os.path.basename(path)}'
        else:
            output_path: str = path
        input_size: int = os.path.getsize(path)
        height: int
        width: int
        original_image: Image = Image.open(path)
        width, height = original_image.size
        target_width: int
        target_height: int
        target_width, target_height = self.get_new_size(width, height, ratio)
        new_image: Image = Image.new("RGB", (target_width, target_height), (255, 255, 255))
        if target_width == width:
            x: int = 0
        else:
            x: int = int((target_width-width)/2)
        if target_height == height:
            y: int = 0
        else:
            y: int = int((target_width-width)/2)
        new_image.paste(original_image, (x, y))
        new_image.save(output_path)
        if self.logger is not None:
            self.logger.cropping_message(path, (height, width), (target_height, target_width),
                                         input_size, os.path.getsize(output_path))
        return output_path

    @staticmethod
    def get_new_size(width: float, height: float, ratio: float) -> tuple:
        new_width: float = int(height * ratio)
        new_height: float = int(width / ratio)
        if new_width > width:
            return new_width, height
        elif new_height > height:
            return width, new_height
        else:
            return width, height
