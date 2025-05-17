import image
import time

class Frame(image.Image):
    """
    image.Image adapter to extend with picture ID, datetime and save method.
    """

    id = 0 # (static) (overflow à 9223372036854775807/(86400*60fps)=1779199852788j)
    BASE_PATH = "jpegs/"
    
    def __init__(self, arg, buffer:bytes|bytearray|memoryview|None=None, copy_to_fb:bool=False):
        super().__init__(arg, buffer, copy_to_fb)
        self.init_identification()

    def init_identification(self):
        self.time_str = "-".join(map(str,time.localtime()[0:6]))
        self.id = Frame.id
        Frame.id += 1

    @classmethod
    def from_Image(cls, obj: image.Image):
        """
        "casts" an existing image.Image to Frame.
        """
        obj.__class__ = cls
        obj.init_identification()
        return obj

    def save(self, foldername):
        """
        Save the image to the specified path
        """
        path = f"{Frame.BASE_PATH}{foldername}/{self.id}.jpg"
        super().save(path)

    @staticmethod
    def set_starting_id(id):
        """
        Set the static ID/picture_count for the Frame class
        """
        Frame.id = id