from logging.csv import Csv
from time import struct_time
from vision.frame import Frame

class ImageLogger(Csv):
    """
    A class to handle image logging operations, extending the Csv class.
    Provides methods for logging captured images with their metadata.
    """

    def __init__(self, path: str):
        """
        Initialize the ImageLogger with a path, csv headers and an optional picture count.
        
        :param path: The path to the CSV file.
        """
        super().__init__(path, "date_time", 
                        "exposure_us", "gain_dB", "frames_per_second", "image_type", 
                        "roi_x", "roi_y", "roi_width", "roi_height")
    
    def append(self, frame: Frame):
        """
        Append image data to the log.
        
        :param datetime: Timestamp of when the picture was taken
        :param fps: Frames per second
        :param image_type: Type of image (e.g., "reference")
        :param rect: Region of interest (ROI) parameters (x, y, width, height)
        """

        datetime_str = "-".join(map(str, frame.capture_time[0:6]))

        if frame.roi_rect:
            super().append(frame.id, datetime_str, frame.exposure_us, frame.gain_db, frame.fps, frame.image_type, *frame.roi_rect)
        else:
            super().append(frame.id, datetime_str, frame.exposure_us, frame.gain_db, frame.fps, frame.image_type)
