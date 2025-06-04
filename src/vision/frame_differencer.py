import sensor, image, pyb
import config.settings as cfg
from hardware.led import LED_CYAN_ON, LED_CYAN_OFF
from vision.frame import Frame

class FrameDifferencer:
    """
    Handles frame differencing functionality for motion detection.
    """

    def __init__(self, image_width: int, image_height: int, sensor_pixformat, listener, session=None):
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
        self.listener = listener
        self.session = session
        if session:
            self.detectionlog = session.detectionlog
            self.imagelog = session.imagelog
        self.img_ref_fb: image.Image
        self.started = False
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

        if cfg.INDICATORS_ENABLED: LED_CYAN_ON()

        # Blend in new frame. We're doing 256-alpha here because we want to
        # blend the new frame into the background. Not the background into the
        # new frame which would be just alpha. Blend replaces each pixel by
        # ((NEW*(alpha))+(OLD*(256-alpha)))/256. So, a low alpha results in
        # low blending of the new image while a high alpha results in high
        # blending of the new image. We need to reverse that for this update.
        #blend with frame that is in buffer
        frame.img.blend(self.img_ref_fb, alpha=(256-cfg.BACKGROUND_BLEND_LEVEL))
        self.img_ref_fb.replace(frame.img)

        if cfg.INDICATORS_ENABLED: LED_CYAN_OFF()

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
        
    def find_blobs(self, diff_frame: Frame):
        """
        Process a frame for motion detection with frame differencing.
        
        Args:
            img: Current image to process
            
        Returns:
            blobs: List of detected blobs that triggered detection
        Sets: self.has_found_blobs to True if blobs are found, False otherwise.
        """

        blobs: list[image.blob]
        self.has_found_blobs = False

        try:
            # Find blobs in the difference image
            blobs = diff_frame.img.find_blobs(cfg.BLOB_COLOR_THRESHOLDS, invert=True, merge=False, pixels_threshold=cfg.MIN_BLOB_PIXELS)
        except MemoryError:
            self.has_found_blobs = True
            print("Memory error in blob detection - assuming triggered")
        
        # filter blobs with maximum pixels condition
        blobs = [b for b in blobs if b.pixels() < cfg.MAX_BLOB_PIXELS]

        if len(blobs) > 0:
            print(f"{len(blobs)} blob(s) within range!")
            self.has_found_blobs = True

        return blobs
    
    def process_blobs(self, blobs: list[image.blob], jpeg_frame: Frame, diff_frame: Frame, mark: bool = cfg.INDICATORS_ENABLED):
        
        nb_blobs_to_process = len(blobs) if cfg.MAX_BLOB_TO_PROCESS == -1 else min(cfg.MAX_BLOB_TO_PROCESS, len(blobs))

        for i in range(0, nb_blobs_to_process):
            
            blob = blobs[i]
            # optional marking of blobs, drawing not supported on compressed images...
            if (mark):
                diff_frame.mark_blob(blob)
            
            if self.session:
                # log each detected blob, we finish the CSV line here if not classifying
                # stats not supported on compressed images...
                color_statistics = diff_frame.get_statistics(roi = blob.rect(), thresholds = cfg.BLOB_COLOR_THRESHOLDS)
                self.detectionlog.append(diff_frame.id, blob, color_statistics, end_line=(cfg.CLASSIFY_MODE != "blobs"))
            
            self.listener.on_blob_found(jpeg_frame, blob)

    
    def update(self, frame: Frame):
        """
        Update the frame differencer with a new frame.
        
        Args:
            frame: Frame object containing the new image to process
        """
        
        # If no reference image is set or there was any change precedently, set the current image as reference
        if (not self.started):
            self.set_reference_image(frame)
            self.has_found_blobs = False
            self.started = True
            self.listener.on_background_reset()
            return frame
        # If the reference image is set, check if we need to blend the background
        # TODO: track detections rects and blend on no movement, multi blobs: mask?
        elif (pyb.elapsed_millis(self.start_time_blending_ms) > cfg.BLEND_TIMEOUT_MS):
            self.blend_background(frame)
            self.has_found_blobs = False
            return frame

        # copy at save-quality before differencing it (image.difference() overwrites)
        jpeg_frame = frame.to_jpeg(quality=cfg.JPEG_QUALITY, copy=True)
        diff_frame = Frame(frame.img, frame.capture_time, frame.exposure_us, frame.gain_db, frame.fps, frame.image_type, frame.roi_rect, id=frame.id)
        
        self.difference(diff_frame)
        diff_frame.save("diff")
        blobs = self.find_blobs(diff_frame)

        if self.has_found_blobs:
            self.listener.on_triggered(jpeg_frame)

        if not blobs: return jpeg_frame

        self.process_blobs(blobs, jpeg_frame, diff_frame)

        return jpeg_frame

        
        
            