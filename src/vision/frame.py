from typing import List, Tuple
import image
from time import struct_time
from logging.image_logger import ImageLoggerA
from util import colors

class BlobExportShape:
    RECTANGLE = 0
    SQUARE = 1

class Frame():
    """
    image.Image extension with capture data and logging methods.
    """

    id = 0 # (static) (overflow à 9223372036854775807/(86400*60fps)=1779199852788j)
    BASE_PATH = "jpegs/"
    
    # def __init__(self, arg, buffer:bytes|bytearray|memoryview|None=None, copy_to_fb:bool=False):
    #     super().__init__(arg, buffer, copy_to_fb)
    #     self._init_identification()

    def __init__(self, img: image.Image, capture_time: struct_time, 
                 exposure_us: int, gain_db: float, fps: float,
                 image_type: str = "", roi_rect=None):
        """
        Initialize the Frame object with an image and its metadata.

        :param img: The image object.
        :param capture_time: The time the image was captured.
        :param exposure_us: Exposure time in microseconds.
        :param gain_db: Gain in decibels.
        :param fps: Frames per second
        :param image_type: Type of image (e.g., "reference").
        :param roi_rect: Region of interest (x, y, width, height).
        """
        self.img = img
        self.capture_time = capture_time
        self.exposure_us = exposure_us
        self.gain_db = gain_db
        self.fps = fps
        self.image_type = image_type
        self.roi_rect = roi_rect
        self.id = Frame.id
        Frame.id += 1

    @property
    def image(self):
        return self.img

    @staticmethod
    def set_starting_id(id: int):
        """
        Set the static starting ID/picture_count for the new Frame objects
        """
        Frame.id = id

    # @classmethod
    # def from_Image(cls, obj: image.Image):
    #     """
    #     "casts" an existing image.Image to Frame.
    #     """
    #     obj.__class__ = cls
    #     obj._init_identification()
    #     return obj

    def copy(self, x_scale:float=1.0, y_scale:float=1.0, roi:Tuple[int,int,int,int]|None=None, rgb_channel:int=-1, alpha:int=256, color_palette=None, alpha_palette=None, hint:int=0, copy_to_fb:float=False):
        img_copy = self.img.copy(x_scale=x_scale, y_scale=y_scale, roi=roi, rgb_channel=rgb_channel, alpha=alpha, color_palette=color_palette, alpha_palette=alpha_palette, hint=hint, copy_to_fb=copy_to_fb)
        return Frame(img_copy, self.capture_time, self.exposure_us, self.gain_db, self.fps, self.image_type, self.roi_rect)
    
    def get_stats(self, thresholds:List[Tuple[int,int]]|None=None, invert=False, roi:Tuple[int,int,int,int]|None=None, bins=256, l_bins=256, a_bins=256, b_bins=256, difference:image.Image|None=None):
        return self.img.get_stats(thresholds=thresholds, invert=invert, roi=roi, bins=bins, l_bins=l_bins, a_bins=a_bins, b_bins=b_bins, difference=difference)
    
    def save(self, foldername: str, filename: str = None):
        if not filename:
            filename = str(self.id)
        path = f"{Frame.BASE_PATH}{foldername}/{filename}.jpg"
        self.img.save(path)

    def log(self, imagelog: ImageLoggerA):
        imagelog.append(self.id, self.capture_time, self.fps, self.image_type, self.roi_rect)

    def save_and_log(self, foldername: str, imagelog: ImageLoggerA, filename: str = None):
        self.save(foldername, filename)
        self.log(imagelog)
        
    def mark_blob(self, blob: image.Blob, thickness: int = 5, edge_color=colors.BLUE, rect_color=colors.RED):
        """
        Mark the detected blob on the image with a rectangle and corners.
        :param blob: The detected blob to mark.
        :param thickness: The thickness of the rectangle lines.
        """
        self.img.draw_edges(blob.corners(), color=edge_color, thickness=thickness)
        self.img.draw_rectangle(blob.rect(), color=rect_color, thickness=thickness)
        return self
    
    def extract_blob_region(self, blob, shape: BlobExportShape = BlobExportShape.RECTANGLE):
        """
        Extract the region of interest around a blob
        
        Args:
            blob: The blob to extract
            shape: The shape to extract (rectangle or square)
            
        Returns:
            blob_rect: Rectangle coordinates for the blob region
            img_blob: Image of the extracted region
        """
        if shape == BlobExportShape.RECTANGLE:
            blob_rect = blob.rect()
        elif shape == BlobExportShape.SQUARE:
            # Make a square using the largest dimension
            size = max(blob.w(), blob.h())
            
            # Check if square is too large for the image
            if size > self.img.height():
                print("Cannot export blob bounding square as its size would exceed the image height! Using image height instead.")
                size = self.img.height()
            
            # Position the square, keeping original top-left corner if possible
            x = blob.x()
            y = blob.y()
            
            # Make sure the square stays within image bounds
            if x + size > self.img.width():
                x = self.img.width() - size
            
            if y + size > self.img.height():
                y = self.img.height() - size
            
            blob_rect = (x, y, size, size)
        
        # Extract blob img
        img_blob = self.img.copy(roi=blob_rect, copy_to_fb=True)
        
        return blob_rect, img_blob
