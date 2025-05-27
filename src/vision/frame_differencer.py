# filepath: /home/user/Bureau/stage/projet/src/vision/frame_differencer.py

import sensor, image
import config.settings as cfg
from hardware.led import LED_CYAN_ON, LED_CYAN_OFF
from vision.frame import Frame

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
        self.img_ori_fb: image.Image | None
        self.imagelog = imagelog
        self.has_found_blobs = False
        self.initialize_framebuffers()
        if (cfg.EXPOSURE_MODE=="auto"): 
            print("ATTENTION: using automatic exposure with frame differencing can result in spurious triggers!")
        
    def initialize_framebuffers(self):
        """Allocate frame buffers for reference and original images"""
        # De-allocate frame buffers just in case
        sensor.dealloc_extra_fb()
        sensor.dealloc_extra_fb()
        
        # Allocate frame buffers for reference and original images
        self.img_ref_fb = sensor.alloc_extra_fb(self.image_width, self.image_height, self.sensor_pixformat)
        self.img_ori_fb = None # sensor.alloc_extra_fb(self.image_width, self.image_height, self.sensor_pixformat)
    
    def save_reference_image(self, frame: Frame):
        """
        Save the current image as the reference image
        
        Args:
            img: Current image to use as reference
            current_folder: Folder where to save the reference image
            picture_count: Current picture count
            imagelog: Logger for image data
            picture_time: Time when the picture was taken
        """
        # Store the image as reference
        self.img_ref_fb.replace(frame.img)
        
        frame.save_and_log("reference", self.imagelog)
    
    def blend_background(self, frame: Frame):
        """
        Blend the new image into the background reference
        
        Args:
            img: New image to blend with reference
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

        
    def process_frame(self, frame: Frame):
        """
        Process a frame for motion detection with frame differencing.
        
        Args:
            img: Current image to process
            
        Returns:
            img_roi: Image with difference applied
            triggered: Boolean indicating if motion was detected
            blobs: List of detected blobs that triggered detection
        """
        # Save original image
        if self.img_ori_fb:
            self.img_ori_fb.replace(frame.img)
        else:
            self.img_ori_fb = frame.img
        
        # Compute absolute frame difference
        frame.img.difference(self.img_ref_fb)
        
        blobs_filt = []
        self.has_found_blobs = False
        
        try:
            # Find blobs in the difference image
            blobs = frame.img.find_blobs(cfg.BLOB_COLOR_THRESHOLDS, invert=True, merge=False, pixels_threshold=cfg.MIN_BLOB_PIXELS)
            
            # Filter blobs with maximum pixels condition
            blobs_filt = [b for b in blobs if b.pixels() < cfg.MAX_BLOB_PIXELS]
            
            if len(blobs_filt) > 0:
                print(f"{len(blobs_filt)} blob(s) within range!")
                self.has_found_blobs = True
                
        except MemoryError:
            # When there is a memory error, we assume that it is triggered because of many blobs
            self.has_found_blobs = True
            print("Memory error in blob detection - assuming triggered")
            
        return blobs_filt
    
    def get_original_image(self):
        """Return the original image framebuffer"""
        return self.img_ori_fb
        
    def get_reference_image(self):
        """Return the reference image framebuffer"""
        return self.img_ref_fb
    