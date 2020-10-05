from PIL import Image
import os
from .logger import Logger


class Resizer:
    def __init__(self,
                 output_directory: str = None,
                 max_width: int = None,
                 max_height: int = None,
                 logger: Logger = None):
        self.max_width: int or None = max_width
        self.max_height: int or None = max_height
        self.output_directory: str = output_directory
        self.logger: Logger = logger
        if output_directory is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

    def resize(self, path: str, max_width: int = None, max_height: int = None) -> str:
        if not os.path.exists(path):
            raise RuntimeError('File not found!')
        if self.output_directory is not None:
            output_path: str = f'{self.output_directory}/{os.path.basename(path)}'
        else:
            output_path: str = path
        original_image: Image = Image.open(path)
        w, h = original_image.size
        input_size: int = os.path.getsize(path)
        if max_width or max_height:
            width: int = max_width if max_width else w
            height: int = max_height if max_height else h
        else:
            width: int = self.max_width if self.max_width else w
            height: int = self.max_height if self.max_height else h
        if self.max_height is self.max_width is max_height is max_width is None:
            raise RuntimeError('Width or height required!')
        if w <= width and h <= height:
            width = w
            height = h
        original_image.thumbnail((width, height), Image.ANTIALIAS)
        original_image.save(output_path)
        if self.logger is not None:
            self.logger.resizing_message(path, (h, w), (height, width), input_size, os.path.getsize(output_path))
        return output_path
