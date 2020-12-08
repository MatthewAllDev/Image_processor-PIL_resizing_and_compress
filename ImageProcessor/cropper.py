import os
import cv2
from numpy import ndarray
import math
from .logger import Logger


class Cropper:
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

    def crop_image(self, path: str, ratio: float = None) -> str:
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
        img: ndarray = cv2.imread(path)
        input_size: int = os.path.getsize(path)
        height: int
        width: int
        channels: int
        height, width, channels = img.shape
        target_width: int
        target_height: int
        target_width, target_height = Cropper.get_new_size(width, height, ratio)
        contour: dict = self.get_contour(img)
        if (contour['width'] < width or contour['height'] < height) and self.logger is not None:
            self.logger.write(f'\nWARNING: Cropping {path} could be affected important elements')
        crop_data: dict = Cropper.get_crop_coordinates((width, height), (target_width, target_height), contour)
        crop = img[crop_data['y_start']:crop_data['y_finish'], crop_data['x_start']:crop_data['x_finish']]
        cv2.imwrite(output_path, crop)
        if self.logger is not None:
            self.logger.cropping_message(path, (height, width), (target_height, target_width),
                                         input_size, os.path.getsize(output_path))
        return output_path

    @staticmethod
    def get_contour(img: ndarray) -> dict:
        retval: float
        thresh_gray: float
        contours: list
        hierarchy: ndarray
        gray: ndarray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        retval, thresh_gray = cv2.threshold(gray, thresh=100, maxval=255, type=cv2.THRESH_BINARY_INV)
        contours, hierarchy = cv2.findContours(thresh_gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        hierarchy: ndarray = hierarchy[0]
        new_contours: list = list()
        for component in zip(contours, hierarchy):
            current_contour: ndarray = component[0]
            current_hierarchy: ndarray = component[1]
            if current_hierarchy[2] > 0:
                x: int
                y: int
                w: int
                h: int
                x, y, w, h = cv2.boundingRect(current_contour)
                contour_data: dict = {'x_start': x, 'x_finish': x + w, 'y_start': y, 'y_finish': y + h,
                                      'width': w, 'height': h, 'area': w * h}
                new_contours.append(contour_data)
        return Cropper.join_all_contours(new_contours)

    @staticmethod
    def get_new_size(width: float, height: float, ratio: float) -> tuple:
        new_width: float = int(height * ratio)
        new_height: float = int(width / ratio)
        if new_width > width:
            return width, new_height
        elif new_height > height:
            return new_width, height

    @staticmethod
    def join_all_contours(contours: list) -> dict:
        contours.sort(key=lambda contour: contour['area'], reverse=True)
        unit_contour = contours[0]
        for i in range(1, len(contours)):
            if Cropper.is_intersect(unit_contour, contours[i]):
                unit_contour = Cropper.join_contours(unit_contour, contours[i])
        return unit_contour

    @staticmethod
    def is_intersect(contour_1: dict, contour_2: dict) -> bool:
        if Cropper.in_range(contour_2['x_start'], (contour_1['x_start'], contour_1['x_finish'])) or \
                Cropper.in_range(contour_2['x_finish'], (contour_1['x_start'], contour_1['x_finish'])):
            if Cropper.in_range(contour_2['y_start'], (contour_1['y_start'], contour_1['y_finish'])) or \
                    Cropper.in_range(contour_2['y_finish'], (contour_1['y_start'], contour_1['y_finish'])):
                return True
        return False

    @staticmethod
    def in_range(num: int, target_range: tuple):
        if target_range[0] <= num <= target_range[1]:
            return True

    @staticmethod
    def join_contours(contour_1: dict, contour_2: dict) -> dict:
        unit_contour: dict = dict()
        unit_contour['x_start'] = contour_1['x_start'] \
            if contour_1['x_start'] < contour_2['x_start'] else contour_2['x_start']
        unit_contour['y_start'] = contour_1['y_start'] \
            if contour_1['y_start'] < contour_2['y_start'] else contour_2['y_start']
        unit_contour['x_finish'] = contour_1['x_finish'] \
            if contour_1['x_finish'] > contour_2['x_finish'] else contour_2['x_finish']
        unit_contour['y_finish'] = contour_1['y_finish'] \
            if contour_1['y_finish'] > contour_2['y_finish'] else contour_2['y_finish']
        unit_contour['width'] = unit_contour['x_finish'] - unit_contour['x_start']
        unit_contour['height'] = unit_contour['y_finish'] - unit_contour['y_start']
        unit_contour['area'] = unit_contour['width'] * unit_contour['height']
        return unit_contour

    @staticmethod
    def get_crop_coordinates(original_size: tuple, target_size: tuple, contour: dict) -> dict:
        coordinates: dict = dict()
        w_space: int = (target_size[0] - contour['width'])
        h_space: int = (target_size[1] - contour['height'])
        if original_size[0] == target_size[0]:
            coordinates['x_start'] = 0
            coordinates['x_finish'] = target_size[0]
        else:
            if w_space >= 0:
                coordinates['x_start'] = contour['x_start'] - math.floor(w_space / 2)
                if coordinates['x_start'] < 0:
                    w_space: int = coordinates['x_start'] * -1 + math.ceil(w_space / 2)
                    coordinates['x_start'] = 0
                else:
                    w_space: int = math.ceil(w_space / 2)
                coordinates['x_finish'] = contour['x_finish'] + w_space
            else:
                coordinates['x_finish'] = contour['x_finish'] + w_space
                coordinates['x_start'] = contour['x_start']
        if original_size[1] == target_size[1]:
            coordinates['y_start'] = 0
            coordinates['y_finish'] = target_size[1]
        else:
            if h_space >= 0:
                coordinates['y_start'] = contour['y_start'] - math.floor(h_space / 2)
                if coordinates['y_start'] < 0:
                    h_space: int = coordinates['y_start'] * -1 + math.ceil(h_space / 2)
                    coordinates['y_start'] = 0
                else:
                    h_space: int = math.ceil(h_space / 2)
                coordinates['y_finish'] = contour['y_finish'] + h_space
                if coordinates['y_finish'] > original_size[1]:
                    coordinates['y_start'] = coordinates['y_start'] - (coordinates['y_finish'] - original_size[1])
                    coordinates['y_finish'] = original_size[1]
            else:
                coordinates['y_finish'] = contour['y_finish'] + h_space
                coordinates['y_start'] = contour['y_start']
        return coordinates
