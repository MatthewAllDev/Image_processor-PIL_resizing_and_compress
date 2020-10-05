from ImageProcessor import Processor

if __name__ == '__main__':
    processor: Processor = Processor(directory='', max_height=1599,
                                     tiny_png_api_key=['TinyPNG_API_key1',
                                                       'TinyPNG_API_key2'],
                                     write_log=True)
    files: list = processor.resize_all()
    processor.compress_all(files)
