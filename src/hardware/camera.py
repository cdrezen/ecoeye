from hardware.led import LED_WHITE_BLINK, Illumination
import sensor
import time
from config.settings import Mode
import config.settings as cfg
import sys
from util.rect import Rect
from vision.frame import Frame

class Camera:
    """
    Camera class to encapsulate camera operations for the EcoVision project.
    Handles sensor setup, exposure control, and image capture.
    """
    _initialized = False
    EXPOSURE_RESET_TIMEOUT = 2000  # ms
    AFTER_EXPOSURE_TIMEOUT = 300  # ms
        
    def initialize(self, illumination: Illumination, sensor_pixformat, sensor_framesize, windowing_rect: Rect|None =None, 
                 nb_framebuffers=0, exposure_mode="auto"):
        """
        Reset and initialize the camera sensor with the configured settings.
        Args:
            sensor_pixformat: Pixel format to use (e.g., sensor.RGB565)
            sensor_framesize: Frame size to use (e.g., sensor.QVGA)
            windowing_rect: Windowing rectangle (x, y, w, h) if windowing_rect is used (else None)
            nb_framebuffers: Number of framebuffers to use (0 for auto)
            exposure_mode: Exposure control self.exposure_mode ("auto", "exposure", "bias", or "manual")
        """
        self.illumination = illumination
        self.sensor_pixformat = sensor_pixformat
        self.sensor_framesize = sensor_framesize
        self.windowing_rect = windowing_rect
        self.nb_framebuffers = nb_framebuffers
        self.exposure_mode = exposure_mode
        _initialized = True

        #indicate initialisation with LED
        LED_WHITE_BLINK(200,3)

        # Reset and initialize the sensor
        sensor.reset()
        sensor.set_pixformat(self.sensor_pixformat)
        sensor.set_framesize(self.sensor_framesize)
        
        if self.windowing_rect:
            if (windowing_rect.y + windowing_rect.h > sensor.height() or windowing_rect.x + windowing_rect.w > sensor.width()):
                print("windowing_y:", windowing_rect.y, "windowing_h:", windowing_rect.h, "sensor.height:", sensor.height())
                print("windowing_x:", windowing_rect.x, "windowing_w:", windowing_rect.w, "sensor.width:", sensor.width())
                sys.exit("Windowing dim exceeds image dim!")
            sensor.set_windowing((self.windowing_rect.x, self.windowing_rect.y, 
                                  self.windowing_rect.w, self.windowing_rect.h))
        
        if self.nb_framebuffers:
            sensor.set_framebuffers(self.nb_framebuffers)

        self.last_gain_db = sensor.get_gain_db()
        self.last_exposure = sensor.get_exposure_us()

        self.reset_exposure(Camera.EXPOSURE_RESET_TIMEOUT)
        
    
    def get_image_dimensions(self):
        """Return the current width and height of captured images."""
        if self.windowing_rect:
            return self.windowing_rect.w, self.windowing_rect.h
        else:
            return sensor.width(), sensor.height()
        
    def take_picture(self, is_night: bool, clock: time.clock, exposure_mult=None, image_type=""):
        """
        Take a picture with the current or modified camera settings.
        
        Args:
            do_expose: Whether to adjust exposure before taking the picture
            exposure_mode: Exposure self.exposure_mode if adjusting exposure
            exposure_bias_day: Exposure bias for daytime if adjusting exposure
            exposure_bias_night: Exposure bias for nighttime if adjusting exposure
            gain_bias: Gain bias if adjusting exposure
            exposure_ms: Explicit exposure time if adjusting exposure
            gain_db: Explicit gain if adjusting exposure
            is_night: Boolean indicating if it's night time
            exposure_mult: Multiplier for exposure bracketing
            illumination: Illumination controller object
            
        Returns:
            Tuple of (image, timestamp_string)
        """
        
        if exposure_mult is not None:
            # Fix the gain so image is stable
            sensor.set_auto_gain(False)
            sensor.set_auto_exposure(False, exposure_us=int(self.last_exposure * exposure_mult))
            # Wait for new exposure time to be applied
            sensor.skip_frames(time=Camera.EXPOSURE_RESET_TIMEOUT)
        
        # Handle illumination if provided
        if self.illumination and self.illumination.can_turn_on(is_night):
            self.illumination.on(message="to take the picture")
        
        if self.exposure_mode == "bias":
            self.update_exposure_bias(is_night)        
        # Take the picture
        img = sensor.snapshot()
        
        # Turn off illumination if needed
        if self.illumination and self.illumination.can_turn_off():
            self.illumination.off(message="to save power...")

        self.last_gain_db = sensor.get_gain_db()
        self.last_exposure = sensor.get_exposure_us()
        
        return Frame(img, time.localtime(), self.last_exposure, self.last_gain_db, clock.fps(), image_type)
    
    def update_exposure_bias(self, is_night: bool, gain_bias=cfg.GAIN_BIAS, exposure_bias=None):
        """
        Adjust camera exposure based on the given parameters.
        
        Args:
            self.exposure_mode: Exposure self.exposure_mode ("auto", "exposure", "bias", "manual")
            exposure_bias_day: Exposure bias for daytime
            exposure_bias_night: Exposure bias for nighttime
            gain_bias: Gain bias 
            exposure_ms: Explicit exposure time in milliseconds for manual self.exposure_mode
            gain_db: Explicit gain in dB for manual self.exposure_mode
            is_night: Boolean indicating if it's night time
        """
        # Get current exposure
        current_exposure = sensor.get_exposure_us()
        # Apply bias (based on day/night)
        if not exposure_bias:
            exposure_bias = cfg.EXPOSURE_BIAS_DAY if not is_night else cfg.EXPOSURE_BIAS_NIGHT
        sensor.set_auto_exposure(False, exposure_us=int(current_exposure * exposure_bias))
        # Set fixed gain with bias
        sensor.set_auto_gain(False, gain_db=int(sensor.get_gain_db() + gain_bias))
        # Wait for settings to take effect
        sensor.skip_frames(time=Camera.AFTER_EXPOSURE_TIMEOUT)
        return
        
    
    def reset_exposure(self, timeout=EXPOSURE_RESET_TIMEOUT):
        if self.exposure_mode == "auto":
            # Auto gain and exposure
            sensor.set_auto_gain(True)
            sensor.set_auto_exposure(True)
        elif self.exposure_mode == "exposure":
            # Auto gain but fixed exposure
            sensor.set_auto_gain(True)
            sensor.set_auto_exposure(False, exposure_us=int(cfg.EXPOSURE_MS * 1000))
        elif self.exposure_mode == "manual":
            # Set fixed exposure and gain
            sensor.set_auto_gain(False, gain_db=cfg.GAIN_DB)
            sensor.set_auto_exposure(False, exposure_us=int(cfg.EXPOSURE_MS * 1000))
        elif self.exposure_mode == "bias":
            sensor.set_auto_gain(False, gain_db=int(self.last_gain_db))
            sensor.set_auto_exposure(False, exposure_us=self.last_exposure)
            
        # Wait for auto-adjustment
        sensor.skip_frames(time=timeout)