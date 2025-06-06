# import user defined parameters
import config.settings as cfg
from config.settings import Mode
#import libraries
from hardware.camera import Camera
from logging.detection_logger import DetectionLogger
import sensor, time, tf, pyb, machine, image
# import external functions
from ecofunctions import *
from hardware.power import PowerManagement
from hardware.led import *
from util.timeutil import Suntime, Rtc
from logging.session import Session
from vision.frame import Frame
from vision.frame_differencer import FrameDifferencer
from vision.classifier import Classifier


class App:
    def __init__(self):
        self.solartime = Suntime(cfg.TIME_COVERAGE, cfg.SUNRISE_HOUR, cfg.SUNRISE_MINUTE, cfg.SUNSET_HOUR, cfg.SUNSET_MINUTE)
        self.rtc = Rtc()
        self.illumination = Illumination()
        self.camera = Camera()
        self.session: Session | None = None
        self.power_mgmt: PowerManagement
        self.is_night = not self.solartime.is_daytime()
        self.frame_differencer: FrameDifferencer
        self.classifier: Classifier
        self.wifi_enabled= cfg.WIFI_ENABLED and wifishield_isconnnected()
        self.detectionlog: DetectionLogger | None = None
        
        # perform quick start from sleep check
        start_check()

        print(f"Initializing on {Mode.to_str(cfg.MODE)} mode...")

        # On wakeup from deep sleep, fetch environment from session.json
        if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
            self.session = Session().load()
            if not self.session: self.session = Session().create(self.rtc)
            print_status="Script start - Waking"
        # create and initialize new folders only on powerup or soft reset
        elif (cfg.MODE != Mode.LIVE_VIEW):
            # create necessary files & folders
            self.session = Session().create(self.rtc)
            print_status="Script start - Initialising"
        else:
            print_status="Script start - Live view"

        self.power_mgmt = PowerManagement(self.illumination, self.solartime, self.rtc, self.session)
        
        if self.session:
            self.detectionlog=self.session.detectionlog

        self.power_mgmt.sleep_if_low_bat(print_status)

        if(cfg.CLASSIFY_MODE != "none"):
            self.classifier = Classifier(self.session)

        winrect = cfg.WIN_RECT if cfg.USE_SENSOR_WINDOWING else None

        self.camera.initialize(self.illumination, cfg.SENSOR_PIXFORMAT, cfg.SENSOR_FRAMESIZE,
                        winrect, cfg.NB_SENSOR_FRAMEBUFFERS, cfg.EXPOSURE_MODE)
        
        print("camera initialized")
        
        self.image_width = winrect.w if winrect else sensor.width()
        self.image_height = winrect.h if winrect else sensor.height()

        self.clock = time.clock()

        if(cfg.FRAME_DIFF_ENABLED):
            self.frame_differencer = FrameDifferencer(self.image_width, self.image_height, 
                                                      cfg.SENSOR_PIXFORMAT, self, self.session)

    def on_triggered(self, jpeg_frame : Frame):
        """
        Called when motion/blobs were found on a frame. Before blob processing.
        
        Args:
            frame: Frame object containing the image that triggered the event
        """
        pass

    def on_blob_found(self, jpeg_frame: Frame, blob: image.blob):
        """
        Called when a blob has been processed by the frame differencer.
        
        Args:
            frame: Frame object containing the image with the processed blob
            blob: The blob that was processed
        """
        if (cfg.CLASSIFY_MODE != "blobs" and cfg.BLOBS_EXPORT_METHOD==None):
            return

        frame_blob = jpeg_frame.extract_blob_region(blob, cfg.BLOBS_EXPORT_METHOD)

        if (cfg.BLOBS_EXPORT_METHOD!=None):
            filename = str(jpeg_frame.id) + "_d" + str(self.detectionlog.detection_count) + "_xywh" + str("_".join(map(str,frame_blob.roi_rect)));
            frame_blob.save("blobs", filename)
        if (cfg.CLASSIFY_MODE == "blobs"):
            detected, output = self.classifier.classify(frame_blob.img, cfg.CLASSIFY_MODE)
            self.detectionlog.append(jpeg_frame.id, labels=self.classifier.labels, confidences=output, rect=blob.rect(), prepend_comma=True)

    def on_background_reset(self):
        """
        Called when the background reference image is reset.
        """
        pass
        
    def run(self):
        ### MAIN LOOP ###
        while(True):
            self.clock.tick()
            self.is_night = not self.solartime.is_daytime()

            # turn ON illumination LED at night if always ON || turn OFF illumination LED at daytime, blink busy led every period
            self.illumination.update(self.is_night)

            # handle power mangment, enter deeplseep if needed, lower frame rate using a configured delay
            self.power_mgmt.update()

            ### Take and process picture(s) ###
            
            frame = self.camera.take_picture(self.is_night, self.clock)
            
            if(self.frame_differencer):
                frame = self.frame_differencer.update(frame)

            if(self.session):
                frame.log(self.session.imagelog) ### keep in main

                if(cfg.CLASSIFY_MODE=="image" or cfg.CLASSIFY_MODE=="objects"):
                    detected, detection_confidence = self.classifier.classify(frame.img, cfg.CLASSIFY_MODE, roi_rect=frame.roi_rect)

                if(cfg.SAVE_ROI_MODE == "all" 
                or (cfg.SAVE_ROI_MODE  == "trigger" and self.frame_differencer.has_found_blobs)
                or (cfg.SAVE_ROI_MODE == "detect" and detected)):
                    frame.save("img")

            print("Frames per second: %s" % str(round(self.clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")


# Create and run the application
if __name__ == "__main__":
    app = App()
    try:
        app.run()
    except Exception as e:
        with open("error_log.txt", "a") as f:
            error_str = f"Error: {e}\n{e.args}\n"
            print(error_str)
            f.write(error_str)
