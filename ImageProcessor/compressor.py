import aiohttp
import os
import time
import mimetypes
import re
from .cycle_iterator import CycleIterator
from .errors import Error, TinyPNGAccountError
from .progress_bar import ProgressBar
from .logger import Logger


class Compressor:
    session: aiohttp.ClientSession

    def __init__(self, api_keys: list or str,
                 output_directory: str = None,
                 retry_count: int = 5,
                 delay_time: int = 1000,
                 logger: Logger = None):
        if type(api_keys) == str:
            self.api_keys: CycleIterator = CycleIterator([api_keys])
        else:
            self.api_keys: CycleIterator = CycleIterator(api_keys)
        self.output_directory: str = output_directory
        if output_directory is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)
        self.retry_count: int = retry_count
        self.delay_time: int = delay_time
        self.logger: Logger = logger
        self.compressed_files: set = set()

    async def create_web_session(self):
        try:
            key: str = next(self.api_keys)
            self.session: aiohttp.ClientSession = aiohttp.ClientSession(auth=aiohttp.BasicAuth('api', key))
            if not await self.__validate_api_key():
                await self.session.close()
                await self.create_web_session()
        except StopIteration:
            raise RuntimeError('No valid API keys found or keys have reached the images processing limit.')

    async def compress(self, path: str, progress: ProgressBar = None):
        if not hasattr(self, 'session'):
            raise RuntimeError('Web session was not created. Use .create_web_session () before compressing.')
        if not self.is_compression_supported(path):
            await self.session.close()
            raise TypeError(f'Extension "{os.path.splitext(path)[1]}" not supported by compressor.')
        output_url: str = await self.__upload_image(path)
        input_size: int = os.path.getsize(path)
        if self.output_directory is not None:
            output_path: str = f'{self.output_directory}/{os.path.basename(path)}'
        else:
            output_path: str = path
        await self.__download_image(output_url, output_path)
        self.compressed_files.add(path)
        if self.logger is not None:
            self.logger.compressing_massage(path, input_size, os.path.getsize(output_path))
        if progress is not None:
            progress.inc()
            progress.show()

    async def __upload_image(self, path: str, retry: int = 0) -> str:
        with open(path, 'rb') as file:
            data: bytes = file.read()
            response: aiohttp.ClientResponse = await self.session.post('https://api.tinify.com/shrink/', data=data)
            if response.status != 201:
                if response.status == 401 or response.status == 429:
                    raise TinyPNGAccountError(f'\nAPI key "{self.api_keys.element}" is not valid or '
                                              f'the key\'s imaging limit has been reached.')
                if response.status >= 500 and retry < self.retry_count:
                    time.sleep(self.delay_time / 1000)
                    return await self.__upload_image(path, retry + 1)
                else:
                    try:
                        details: dict = await response.json()
                    except Exception as err:
                        details: dict = {'message': 'Error while parsing response: {0}'.format(err),
                                         'error': 'ParseError'}
                    raise Error.create(details.get('message'), details.get('error'), response.status)
            response: dict = await response.json()
            return response['output']['url']

    async def __download_image(self, url: str, output_path: str):
        response: aiohttp.ClientResponse = await self.session.get(url)
        if response.status == 200:
            with open(output_path, 'wb') as file:
                data: bytes = await response.read()
                file.write(data)
        else:
            error_text: str = f'\nError downloading image. Status code: {response.status}'
            print(error_text)
            if self.logger is not None:
                self.logger.error_message(error_text)

    async def __validate_api_key(self, retry: int = 0) -> bool:
        response: aiohttp.ClientResponse = await self.session.post('https://api.tinify.com/shrink/')
        if response.status != 400:
            if response.status >= 500 and retry < self.retry_count:
                time.sleep(self.delay_time / 1000)
                return await self.__validate_api_key(retry + 1)
            elif response.status == 401 or response.status == 429:
                error_text: str = f'\nAPI key "{self.api_keys.element}" is not valid or ' \
                                  f'the key\'s imaging limit has been reached.'
                print(error_text)
                if self.logger is not None:
                    self.logger.error_message(error_text)
                self.api_keys.delete(self.api_keys.element)
                return False
            else:
                try:
                    details: dict = await response.json()
                except Exception as err:
                    details: dict = {'message': 'Error while parsing response: {0}'.format(err), 'error': 'ParseError'}
                raise Error.create(details.get('message'), details.get('error'), response.status)
        return True

    @staticmethod
    def is_compression_supported(file_name: str) -> bool:
        return bool(re.fullmatch('.*/png', str(mimetypes.guess_type(file_name)[0]))) \
               or bool(re.fullmatch('.*/jpeg', str(mimetypes.guess_type(file_name)[0])))
