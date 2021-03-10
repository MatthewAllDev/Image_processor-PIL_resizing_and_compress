import types
import re
import os
import mimetypes
import asyncio
import multiprocessing
from .resizer import Resizer
from .cropper import Cropper
from .paster import Paster
from .compressor import Compressor
from .progress_bar import ProgressBar
from .logger import Logger
from .errors import TinyPNGAccountError


class Processor:
    progress: ProgressBar

    def __init__(self,
                 output_directory: str = 'output',
                 directory: str = '',
                 max_width: int = None,
                 max_height: int = None,
                 ratio: float = None,
                 tiny_png_api_key: list or str = None,
                 write_log: bool = False):
        self.directory: str = directory
        self.has_key_error: bool = False
        if write_log:
            self.logger: Logger = Logger(f'{output_directory}/log.txt')
        else:
            self.logger: None = None
        self.resizer: Resizer = Resizer(output_directory, max_width, max_height, logger=self.logger)
        self.cropper: Cropper = Cropper(output_directory, ratio, self.logger)
        self.paster: Paster = Paster(output_directory, ratio, self.logger)
        if tiny_png_api_key is not None:
            self.compressor: Compressor = Compressor(tiny_png_api_key, logger=self.logger)

    def resize_all(self, files: list = None, max_width: int = None, max_height: int = None) -> list:
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
        pool: multiprocessing.Pool = multiprocessing.Pool()
        overall_output_weight: int = 0
        for file in files:
            results.append(pool.apply_async(self.resizer.resize, (file, max_width, max_height)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_resizing(overall_output_weight)
        return output_files

    def crop_all(self, files: list = None, ratio: float = None):
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
        pool: multiprocessing.Pool = multiprocessing.Pool()
        overall_output_weight: int = 0
        for file in files:
            results.append(pool.apply_async(self.cropper.crop_image, (file, ratio)))
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
        pool: multiprocessing.Pool = multiprocessing.Pool()
        overall_output_weight: int = 0
        for file in files:
            results.append(pool.apply_async(self.paster.make_image, (file, ratio)))
        for result in results:
            file: str = result.get(timeout=10)
            self.progress.inc()
            self.progress.show()
            overall_output_weight += os.path.getsize(file)
            output_files.append(file)
        if self.logger is not None:
            self.logger.stop_pasting(overall_output_weight)
        return output_files

    def compress_all(self, files: list = None):
        if not hasattr(self, 'compressor'):
            raise AttributeError('"tiny_png_api_key" must be defined when instantiating "Processor" class.')
        if files is None:
            files: list = list(filter(self.is_image, os.listdir(self.directory)))
            files = list(map(lambda f: f'{self.directory}/{f}', files))
        files = self.__validate_files_to_compress(files)
        if self.logger is not None:
            self.logger.start_compressing(len(files), self.get_overall_size(files))
        asyncio.get_event_loop().run_until_complete(self.async_compress_all(files))
        if self.logger is not None:
            self.logger.stop_compressing()

    async def async_compress_all(self, files: list, continuation: bool = False):
        self.compressor.compressed_files = set()
        if not hasattr(self.compressor, 'session') or self.compressor.session.closed:
            await self.compressor.create_web_session()
        if not continuation:
            print('\nCompress in progress...')
            self.progress: ProgressBar = ProgressBar(len(files))
            self.progress.show()
        tasks: set = set()
        for file in files:
            tasks.add(asyncio.create_task(self.exception_wrapper(self.compressor.compress(file, self.progress))))
        await asyncio.wait(tasks)
        if self.has_key_error:
            await self.compressor.session.close()
            self.has_key_error = False
        not_processed_files: list = self.__check_compressed_files(files)
        if len(not_processed_files) != 0:
            await self.async_compress_all(not_processed_files, True)
        else:
            await self.compressor.session.close()

    def __check_compressed_files(self, files: list) -> list:
        files_set: set = set(files)
        if self.compressor.compressed_files == files_set:
            return []
        else:
            return list(files_set.difference(self.compressor.compressed_files))

    def __validate_files_to_compress(self, files: list) -> list:
        for file in files.copy():
            if not self.compressor.is_compression_supported(file):
                error_text: str = f'\n{file} not supported by compressor. Only jpeg and png files.'
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
