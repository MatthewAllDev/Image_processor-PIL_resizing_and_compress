# Image Processor: PIL Resizing and Compression

This project is a tool for image processing that includes functions for cropping, resizing, and compressing images. It uses the Pillow (PIL) library for image manipulation and provides a simple interface for performing these operations on a batch of images.

## Installation

To install the dependencies, use `pip`:

```bash
pip install -r requirements.txt
```

## Usage

### Main Script

Example usage of the main script:

```python
from ImageProcessor import Processor

if __name__ == '__main__':
    processor: Processor = Processor(directory='input', height=1600,
                                     ratio=3 / 4,
                                     tiny_png_api_key=['TinyPNG_API_key1',
                                                       'TinyPNG_API_key2'],
                                     write_log=True)
    files: list = processor.crop_all()
    processor.resize_all(files)
    processor.compress_all(files)  # or processor.compress_all_tiny_png(files)
```

### Processor

The `Processor` class is used to manage the processes of cropping, resizing, and compressing images.

#### Constructor

```python
Processor(output_directory='output', directory='', width=None, height=None,
          stretch=False, save_proportions=True, resize_auto_orientation=False,
          crop_auto_orientation=False, ratio=None, quality=None,
          compressor='leanify', dynamic_quality_range=(80, 85), use_gpu_for_compress=False,
          tiny_png_api_key=None, write_log=False)
```

Parameters:
- `output_directory` (str): Directory for saving processed images.
- `directory` (str): Directory of input images.
- `width` (int): Width for resizing images.
- `height` (int): Height for resizing images.
- `stretch` (bool): Stretch the image to the specified size.
- `save_proportions` (bool): Maintain proportions when resizing.
- `resize_auto_orientation` (bool): Automatic orientation when resizing.
- `crop_auto_orientation` (bool): Automatic orientation when cropping.
- `ratio` (float): Aspect ratio for cropping.
- `quality` (int): Compression quality of images.
- `compressor` (str): Compression method (e.g., `leanify`).
- `dynamic_quality_range` (tuple): Quality range for dynamic compression.
- `use_gpu_for_compress` (bool): Use GPU for compression.
- `tiny_png_api_key` (list or str): API keys for TinyPNG.
- `write_log` (bool): Enable logging.

#### Methods

- `resize_all(files=None, width=None, height=None, stretch=None, save_proportions=None, auto_orientation=None)`: Resize all images.
- `crop_all(files=None, ratio=None, auto_orientation=None)`: Crop all images.
- `paste_all(files=None, ratio=None)`: Fit all images to a specific aspect ratio by overlaying them on a white background.
- `compress_all(files)`: Compress all images.
- `compress_all_tiny_png(files)`: Compress all images using TinyPNG.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
