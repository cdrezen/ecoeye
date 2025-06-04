import os
from config.settings import BlobExportShape
from hardware.led import led_green
import image
import time
from util import colors
import config.settings as cfg

class Frame:
    """
    image.Image extension with capture data and logging methods.
    """

    id = 0 # (static) (overflow à 9223372036854775807/(86400*60fps)=1779199852788j)
    BASE_FOLDER = "jpegs"
    
    # def __init__(self, arg, buffer:bytes|bytearray|memoryview|None=None, copy_to_fb:bool=False):
    #     super().__init__(arg, buffer, copy_to_fb)
    #     self._init_identification()

    def __init__(self, img: image.Image, capture_time: time.struct_time, 
                 exposure_us: int, gain_db: float, fps: float,
                 image_type: str = "", roi_rect=None, id=None):
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
        if id != None:
            self.id = id
        else:
            self.id = Frame.id
            Frame.id += 1

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

    def copy(self, *args, **kwargs):
        img_copy = self.img.copy(*args, **kwargs)
        return Frame(img_copy, self.capture_time, self.exposure_us, self.gain_db, self.fps, self.image_type, self.roi_rect, id=self.id)

    def to_jpeg(self, quality=90, copy=False):
        img_jpeg = self.img.to_jpeg(quality=quality, copy=copy)
        return self if not copy \
                    else Frame(img_jpeg, self.capture_time, self.exposure_us, self.gain_db, self.fps, self.image_type, self.roi_rect, id=self.id)


    def get_statistics(self, *args, **kwargs):
        return self.img.get_statistics(*args, **kwargs)
    
    @led_green
    def save(self, foldername: str, filename: str = "",):
        if not filename:
            filename = str(self.id)
        folderpath = f"{Frame.BASE_FOLDER}/{foldername}"
        if not foldername in os.listdir(Frame.BASE_FOLDER):
            os.mkdir(folderpath)
        path = f"{folderpath}/{filename}.jpg"
        print(f"Saving image to {path}")
        self.img.save(path, quality=cfg.JPEG_QUALITY)

    def log(self, imagelog):
        imagelog.append(self)

    def save_and_log(self, foldername: str, imagelog, filename: str = ""):
        self.save(foldername, filename)
        self.log(imagelog)
        
    def mark_blob(self, blob: image.blob, thickness: int = 5, edge_color=colors.BLUE, rect_color=colors.RED):
        """
        Mark the detected blob on the image with a rectangle and corners.
        :param blob: The detected blob to mark.
        :param thickness: The thickness of the rectangle lines.
        """
        self.img.draw_edges(blob.corners(), color=edge_color, thickness=thickness)
        self.img.draw_rectangle(*blob.rect(), color=rect_color, thickness=thickness)
        return self
    
    def extract_blob_region(self, blob, shape: BlobExportShape = BlobExportShape.RECTANGLE, img = None):
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
        
        # Extract blob region from the image
        if not img:
            return Frame(self.img.copy(roi=blob_rect), self.capture_time, self.exposure_us, self.gain_db, self.fps, self.image_type, blob_rect)
        else:
            return Frame(img.copy(roi=blob_rect), self.capture_time, self.exposure_us, self.gain_db, self.fps, self.image_type, blob_rect)
