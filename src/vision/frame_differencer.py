# filepath: /home/user/Bureau/stage/projet/src/vision/frame_differencer.py

import sensor, image
import config.settings as cfg
from hardware.led import LED_CYAN_ON, LED_CYAN_OFF
from vision.frame import Frame
import pyb

class FrameDifferencer:
    """
    Handles frame differencing functionality for motion detection.
    """

    def __init__(self, image_width, image_height, sensor_pixformat, imagelog):
        """
        Initialize the frame differencer with reference and original framebuffers.
        
        Args:
            image_width: Width of the images to process
            image_height: Height of the images to process
            sensor_pixformat: Pixel format (e.g., sensor.RGB565)
        """
        self.image_width = image_width
        self.image_height = image_height
        self.sensor_pixformat = sensor_pixformat
        self.img_ref_fb: image.Image
        self.imagelog = imagelog
        self.has_found_blobs = False
        self.initialize_framebuffers()
        if (cfg.EXPOSURE_MODE=="auto"): 
            print("ATTENTION: using automatic exposure with frame differencing can result in spurious triggers!")
        
    def initialize_framebuffers(self):
        """Allocate frame buffers for reference and original images"""
        # De-allocate frame buffers just in case
        sensor.dealloc_extra_fb()  
        # Allocate frame buffers for reference images
        self.img_ref_fb = sensor.alloc_extra_fb(self.image_width, self.image_height, self.sensor_pixformat)
    
    def set_reference_image(self, frame: Frame):
        """
        Save the current image as the reference image
        
        Args:
            frame: Frame object containing the current image to save as reference
        """
        # Store the image as reference
        self.img_ref_fb.replace(frame.img)
        frame.save_and_log("reference", self.imagelog)
        self.start_time_blending_ms = pyb.millis()

    def get_reference_image(self):
        """Return the reference image framebuffer"""
        return self.img_ref_fb
    
    def blend_background(self, frame: Frame):
        """
        Blend the new image into the background reference
        
        Args:
            frame: Frame object containing the new image to blend into the background
        """

        if cfg.INDICATORS_ENBLED: LED_CYAN_ON()

        # Blend in new frame. We're doing 256-alpha here because we want to
        # blend the new frame into the background. Not the background into the
        # new frame which would be just alpha. Blend replaces each pixel by
        # ((NEW*(alpha))+(OLD*(256-alpha)))/256. So, a low alpha results in
        # low blending of the new image while a high alpha results in high
        # blending of the new image. We need to reverse that for this update.
        #blend with frame that is in buffer
        frame.img.blend(self.img_ref_fb, alpha=(256-cfg.BACKGROUND_BLEND_LEVEL))
        self.img_ref_fb.replace(frame.img)

        if cfg.INDICATORS_ENBLED: LED_CYAN_OFF()

        # Save reference image to disk
        frame.save_and_log("reference", self.imagelog)

        self.start_time_blending_ms = pyb.millis()
        return

    def difference(self, frame: Frame):
        """
        Compute the absolute difference between the current frame and the reference image.
        Post process the difference image to reduce noise and enhance contrast.
        
        Args:
            frame: Frame object containing the current image to process
        """
        # Compute absolute frame difference
        frame.img.difference(self.img_ref_fb)
        frame.img.gaussian(2)  # Apply Gaussian blur to reduce noise
        # frame.img.gamma(2.0)  # Apply gamma correction to enhance contrast
        return frame
        
    def find_blobs(self, frame: Frame):
        """
        Process a frame for motion detection with frame differencing.
        
        Args:
            img: Current image to process
            
        Returns:
            blobs: List of detected blobs that triggered detection
        Sets: self.has_found_blobs to True if blobs are found, False otherwise.
        """
        
        self.difference(frame)

        blobs: list[image.blob]
        self.has_found_blobs = False

        try:
            # Find blobs in the difference image
            blobs = frame.img.find_blobs(cfg.BLOB_COLOR_THRESHOLDS, invert=True, merge=False, pixels_threshold=cfg.MIN_BLOB_PIXELS)
        except MemoryError:
            self.has_found_blobs = True
            print("Memory error in blob detection - assuming triggered")
        
        # filter blobs with maximum pixels condition
        blobs = [b for b in blobs if b.pixels() < cfg.MAX_BLOB_PIXELS]

        if len(blobs) > 0:
            print(f"{len(blobs)} blob(s) within range!")
            self.has_found_blobs = True

        return blobs
    
    def update(self, frame: Frame):
        """
        Update the frame differencer with a new frame.
        
        Args:
            frame: Frame object containing the new image to process
        """
        
        # If no reference image is set, set the current image as reference
        if self.img_ref_fb == None or self.has_found_blobs:
            self.set_reference_image(frame)
            return
        elif pyb.elapsed_millis(self.start_time_blending_ms) > cfg.BLEND_TIMEOUT_MS:
            self.blend_background(frame)
            return

        # copy at save-quality before differencing it (image.difference() overwrites)
        jpeg_img = frame.img.to_jpeg(quality=cfg.JPEG_QUALITY, copy=True)
        self.difference(frame)
        blobs = self.find_blobs(frame)

        
        
            