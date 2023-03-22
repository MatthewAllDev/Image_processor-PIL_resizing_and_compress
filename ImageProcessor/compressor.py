from io import BytesIO
from PIL import Image
import mozjpeg_lossless_optimization
import typing
import PIL.Image
from PIL.JpegImagePlugin import JpegImageFile
from SSIM_PIL import compare_ssim
import math
import subprocess
import re
import mimetypes
import os
import pathlib
from .logger import Logger
from .progress_bar import ProgressBar


class Compressor:
    def __init__(self,
                 output_directory: str = None,
                 quality: float = None,
                 compressor: str = None,
                 dynamic_quality_range: typing.Tuple[int, int] = (80, 85),
                 use_gpu: bool = False,
                 logger: Logger = None):
        self.__supported_types: typing.Tuple[str, ...] = ('jpeg',)
        self.__quality: float or None = quality
        if compressor.lower() not in ('mozjpeg', 'leanify', None):
            raise TypeError(f'Unsupported compressor "{compressor}".\n'
                            f'Supported:\n'
                            f'mozjpeg\n'
                            f'leanify\n'
                            f'None (only quality optimize)')
        self.__compressor: str or None = compressor
        if dynamic_quality_range[0] >= dynamic_quality_range[1]:
            raise TypeError('The first value "dynamic_quality_range" must be < the second value.')
        self.__dynamic_quality_range: typing.Tuple[int, int] = dynamic_quality_range
        self.__output_directory: str = output_directory
        self.__use_gpu: bool = use_gpu
        self.__logger: Logger = logger
        if output_directory is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

    def compress(self, path: str, progress: ProgressBar = None) -> str:
        if not os.path.exists(path):
            raise RuntimeError('File not found!')
        file_type: str = str(mimetypes.guess_type(path)[0])
        if not bool(re.fullmatch('.*/jpeg', file_type)):
            raise TypeError(f'Compressor does not support "{file_type}" type.')
        if self.__output_directory is not None:
            output_path: str = f'{self.__output_directory}/{os.path.basename(path)}'
        else:
            output_path: str = path
        input_size: int = os.path.getsize(path)
        jpeg_io: BytesIO = BytesIO()
        with Image.open(path, "r") as image:
            if self.__quality is None:
                quality, default_ssim = self.__get_dynamic_quality_for_jpeg(image)
            image.convert("RGB").save(jpeg_io, format="JPEG", quality=quality, optimize=False, progressive=True)
        jpeg_io.seek(0)
        jpeg_bytes: bytes = jpeg_io.read()
        if self.__compressor == 'mozjpeg':
            jpeg_bytes = mozjpeg_lossless_optimization.optimize(jpeg_bytes)
        with open(output_path, "wb") as output_file:
            output_file.write(jpeg_bytes)
        if self.__compressor == 'leanify':
            subprocess.run([pathlib.Path('ImageProcessor/bin/Leanify.exe'), output_path],
                           shell=True,
                           capture_output=True)
        if progress is not None:
            progress.inc()
            progress.show()
        if self.__logger is not None:
            self.__logger.compressing_massage(path, input_size, os.path.getsize(output_path))
        return output_path

    def is_compression_supported(self, file_name: str) -> bool:
        result: bool = False
        for t in self.__supported_types:
            t: str
            result |= bool(re.fullmatch(r'.*/{0}'.format(t), str(mimetypes.guess_type(file_name)[0])))
        return result

    def get_supported_types(self):
        return self.__supported_types

    def __get_dynamic_quality_for_jpeg(self, original_image: JpegImageFile) -> typing.Tuple[int or None, float or None]:
        ssim_goal: float = 0.95
        height: int = self.__dynamic_quality_range[1]
        low: int = self.__dynamic_quality_range[0]
        image: PIL.Image.Image = original_image.resize((400, 400))
        normalized_ssim: float = self.__get_ssim_at_quality(image, 95, self.__use_gpu)
        selected_quality: int or None = None
        selected_ssim: int or None = None
        for i in range(self.__ssim_iteration_count(low, height)):
            i: int
            curr_quality: int = (low + height) // 2
            curr_ssim: float = self.__get_ssim_at_quality(image, curr_quality, self.__use_gpu)
            ssim_ratio: float = curr_ssim / normalized_ssim
            if ssim_ratio >= ssim_goal:
                selected_quality = curr_quality
                selected_ssim = curr_ssim
                height: int = curr_quality
            else:
                low: int = curr_quality
        if selected_quality:
            return selected_quality, selected_ssim
        else:
            default_ssim: float = self.__get_ssim_at_quality(image, height, self.__use_gpu)
            return height, default_ssim

    @staticmethod
    def __get_ssim_at_quality(image: PIL.Image.Image, quality: int, use_gpu: bool = False) -> float:
        ssim_photo: BytesIO = BytesIO()
        image.save(ssim_photo, format="JPEG", quality=quality, progressive=True)
        ssim_photo.seek(0)
        ssim_score: float = compare_ssim(image, PIL.Image.open(ssim_photo), GPU=use_gpu)
        return ssim_score

    @staticmethod
    def __ssim_iteration_count(low: int, height: int) -> int:
        if low >= height:
            return 0
        else:
            return int(math.log(height - low, 2)) + 1
