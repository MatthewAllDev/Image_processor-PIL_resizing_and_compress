from PIL import Image
import os
from .logger import Logger


class Resizer:
    def __init__(self,
                 output_directory: str = None,
                 width: int = None,
                 height: int = None,
                 stretch: bool = False,
                 save_proportions: bool = True,
                 auto_orientation: bool = False,
                 logger: Logger = None):
        self.width: int or None = width
        self.height: int or None = height
        self.stretch: bool = stretch
        self.save_proportions: bool = save_proportions
        self.auto_orientation: bool = auto_orientation
        self.output_directory: str = output_directory
        self.logger: Logger = logger
        if output_directory is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

    def resize(self, path: str, width: int = None, height: int = None,
               stretch: bool = None, save_proportions: bool = None, auto_orientation: bool = None) -> str:
        if not os.path.exists(path):
            raise RuntimeError('File not found!')
        if auto_orientation is None:
            auto_orientation: bool = self.auto_orientation
        if stretch is None:
            stretch: bool = self.stretch
        if save_proportions is None:
            save_proportions: bool = self.save_proportions
        if not save_proportions and auto_orientation:
            raise TypeError('The "auto_orientation" flag supported only with active "save_proportions" flag.')
        if width is None and height is None:
            width: int = self.width
            height: int = self.height
        if width is None and height is None:
            raise RuntimeError('Width or height required!')
        if self.output_directory is not None:
            output_path: str = f'{self.output_directory}/{os.path.basename(path)}'
        else:
            output_path: str = path
        input_size: int = os.path.getsize(path)
        original_image: Image = Image.open(path)
        w, h = original_image.size
        ratio: float = w / h
        if save_proportions:
            if width is None:
                width: int = int(height * ratio)
            elif height is None:
                height: int = int(width / ratio)
            elif ratio != (width / height):
                if auto_orientation:
                    if (ratio < 1) == (width / height > 1):
                        width, height = height, width
                calc_width: int = int(height * ratio)
                calc_height: int = int(width / ratio)
                if stretch:
                    flag: bool = calc_width * height > width * calc_height
                else:
                    flag: bool = calc_width * height < width * calc_height
                if flag:
                    width = calc_width
                else:
                    height = calc_height
        else:
            if width is None:
                width: int = w
            elif height is None:
                height: int = h
        if (w * h > width * height) or stretch:
            original_image.resize((width, height))
        original_image.save(output_path)
        if self.logger is not None:
            self.logger.resizing_message(path, (h, w), (height, width), input_size, os.path.getsize(output_path))
        return output_path
