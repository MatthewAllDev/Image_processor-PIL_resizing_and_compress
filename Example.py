from ImageProcessor import Processor

if __name__ == '__main__':
    processor: Processor = Processor(directory='input', max_height=1600,
                                     ratio=3 / 4,
                                     tiny_png_api_key=['TinyPNG_API_key1',
                                                       'TinyPNG_API_key2'],
                                     write_log=True)
    files: list = processor.crop_all()
    processor.resize_all()
    processor.compress_all(files)  # or processor.compress_all_tiny_png(files)
