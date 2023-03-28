import types
import typing
import re
import os
import mimetypes
import asyncio
import multiprocessing
from .resizer import Resizer
from .cropper import Cropper
from .paster import Paster
from .compressor_tiny_png import Compressor as CompressorTinyPng
from .compressor import Compressor as LocalCompressor
from .progress_bar import ProgressBar
from .logger import Logger
from .errors import TinyPNGAccountError


class Processor:
    progress: ProgressBar

    def __init__(self,
                 output_directory: str = 'output',
                 directory: str = '',
                 width: int = None,
                 height: int = None,
                 stretch: bool = False,
                 save_proportions: bool = True,
                 resize_auto_orientation: bool = False,
                 crop_auto_orientation: bool = False,
                 ratio: float = None,
                 quality: int or None = None,
                 compressor: str or None = 'leanify',
                 dynamic_quality_range: typing.Tuple[int, int] = (80, 85),
                 use_gpu_for_compress: bool = False,
                 tiny_png_api_key: list or str = None,
                 write_log: bool = False):
        self.__mp_pool: multiprocessing.Pool = multiprocessing.Pool()
        self.directory: str = directory
        self.has_key_error: bool = False
        if write_log:
            self.logger: Logger = Logger(f'{output_directory}/log.txt')
        else:
            self.logger: None = None
        self.resizer: Resizer = Resizer(output_directory, width, height, stretch, save_proportions,
                                        resize_auto_orientation, logger=self.logger)
        self.cropper: Cropper = Cropper(output_directory, ratio, crop_auto_orientation, self.logger)
        self.paster: Paster = Paster(output_directory, ratio, self.logger)
        if tiny_png_api_key is not None:
            self.tiny_png_compressor: CompressorTinyPng = CompressorTinyPng(tiny_png_api_key, logger=self.logger)
        self.local_compressor: LocalCompressor = LocalCompressor(output_directory,
                                                                 quality,
                                                                 compressor,
                                                                 dynamic_quality_range,
                                                                 use_gpu_for_compress,
                                                                 self.logger)

    def resize_all(self, files: list = None, width: int = None, height: int = None, stretch: bool = None,
                   save_proportions: bool = None, auto_orientation: bool = None) -> list:
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        if self.logger is not None:
            self.logger.start_resizing(len(files), self.get_overall_size(files))
        print('Resize in progress...')
        self.progress: ProgressBar = ProgressBar(len(files))
        self.progress.show()
        output_files: list = []
        results: list = []
        overall_output_weight: int = 0
        for file in files:
            results.append(self.__mp_pool.apply_async(self.resizer.resize, (file, width, height, stretch,
                                                                            save_proportions, auto_orientation)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_resizing(overall_output_weight)
        return output_files

    def crop_all(self, files: list = None, ratio: float = None, auto_orientation: bool = None):
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        if self.logger is not None:
            self.logger.start_cropping(len(files), self.get_overall_size(files))
        print('Crop in progress...')
        self.progress: ProgressBar = ProgressBar(len(files))
        self.progress.show()
        output_files: list = []
        results: list = []
        overall_output_weight: int = 0
        for file in files:
            results.append(self.__mp_pool.apply_async(self.cropper.crop_image, (file, ratio, auto_orientation)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_cropping(overall_output_weight)
        return output_files

    def paste_all(self, files: list = None, ratio: float = None):
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        if self.logger is not None:
            self.logger.start_pasting(len(files), self.get_overall_size(files))
        print('Paste in progress...')
        self.progress: ProgressBar = ProgressBar(len(files))
        self.progress.show()
        output_files: list = []
        results: list = []
        overall_output_weight: int = 0
        for file in files:
            results.append(self.__mp_pool.apply_async(self.paster.make_image, (file, ratio)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_pasting(overall_output_weight)
        return output_files

    def compress_all(self, files: list = None) -> list:
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        files = self.__validate_files_to_compress(files, self.local_compressor)
        if self.logger is not None:
            self.logger.start_compressing(len(files), self.get_overall_size(files))
        print('Compression in progress...')
        self.progress: ProgressBar = ProgressBar(len(files))
        self.progress.show()
        output_files: list = []
        results: list = []
        overall_output_weight: int = 0
        for file in files:
            results.append(self.__mp_pool.apply_async(self.local_compressor.compress, (file,)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_compressing(overall_output_weight)
        return output_files

    def compress_all_tiny_png(self, files: list = None):
        if not hasattr(self, 'compressor'):
            raise AttributeError('"tiny_png_api_key" must be defined when instantiating "Processor" class.')
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        files = self.__validate_files_to_compress(files, self.tiny_png_compressor)
        if self.logger is not None:
            self.logger.start_compressing(len(files), self.get_overall_size(files))
        asyncio.get_event_loop().run_until_complete(self.async_compress_all_tiny_png(files))
        if self.logger is not None:
            self.logger.stop_compressing()

    async def async_compress_all_tiny_png(self, files: list, continuation: bool = False):
        self.tiny_png_compressor.compressed_files = set()
        if not hasattr(self.tiny_png_compressor, 'session') or self.tiny_png_compressor.session.closed:
            await self.tiny_png_compressor.create_web_session()
        if not continuation:
            print('\nCompress in progress...')
            self.progress: ProgressBar = ProgressBar(len(files))
            self.progress.show()
        tasks: set = set()
        for file in files:
            tasks.add(
                asyncio.create_task(self.exception_wrapper(self.tiny_png_compressor.compress(file, self.progress))))
        await asyncio.wait(tasks)
        if self.has_key_error:
            await self.tiny_png_compressor.session.close()
            self.has_key_error = False
        not_processed_files: list = self.__check_compressed_files(files)
        if len(not_processed_files) != 0:
            await self.async_compress_all_tiny_png(not_processed_files, True)
        else:
            await self.tiny_png_compressor.session.close()

    def __check_compressed_files(self, files: list) -> list:
        files_set: set = set(files)
        if self.tiny_png_compressor.compressed_files == files_set:
            return []
        else:
            return list(files_set.difference(self.tiny_png_compressor.compressed_files))

    def __validate_files_to_compress(self, files: list, compressor: CompressorTinyPng or LocalCompressor) -> list:
        for file in files.copy():
            if not compressor.is_compression_supported(file):
                supported_types: tuple = compressor.get_supported_types()
                supported_types_str: str = ''
                for t in supported_types[:-1]:
                    supported_types_str += f'{t}, '
                supported_types_str += supported_types[-1]
                error_text: str = f'\n{file} not supported by compressor. Only {supported_types_str} files.'
                print(error_text)
                if self.logger is not None:
                    self.logger.error_message(error_text)
                files.remove(file)
        return files

    async def exception_wrapper(self, coroutine: types.coroutine):
        try:
            return await coroutine
        except TinyPNGAccountError as e:
            if not self.has_key_error:
                self.has_key_error = True
                print(e.message)
                if self.logger is not None:
                    self.logger.error_message(e.message)

    @staticmethod
    def get_overall_size(files: list) -> int:
        overall_size: int = 0
        for file in files:
            overall_size += os.path.getsize(file)
        return overall_size

    @staticmethod
    def is_image(file_name: str) -> bool:
        return bool(re.fullmatch('image/.*', str(mimetypes.guess_type(file_name)[0])))
