# import user defined parameters
import config.settings as cfg
from config.enums import Mode, ML_Mode
#import libraries
from hardware.camera import Camera
from logging.detection_logger import DetectionLogger
import sensor, machine, image
# import external functions
from hardware.power import PowerManagement
from hardware.led import *
from logging.session import Session
from vision.frame import Frame
from vision.frame_differencer import FrameDifferencer
from vision.classifier import Classifier
from util import timeutil
from hardware import power

class App:
    def __init__(self):
        self.camera = Camera()
        self.session: Session | None = None
        self.illumination = Illumination()
        self.power_mgmt: PowerManagement
        self.frame_differencer: FrameDifferencer
        self.classifier: Classifier
        self.detectionlog: DetectionLogger | None = None
        

        if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
            # On wakeup from hibernation update rtc & fetch environment from session.json
            power.on_reset_wakeup()
            self.session = Session().load()
            if not self.session: self.session = Session().create()
            print_status="Script start - Waking"
        elif (cfg.MODE != Mode.LIVE_VIEW):
            # only on powerup or soft reset
            # init rtc & create necessary files & folders
            timeutil.reset_rtc(cfg.START_DATETIME)
            self.session = Session().create()
            print_status=f"Initializing on {Mode.to_str(cfg.MODE)} mode..."
        else:
            print_status="Script start - Live view"

        self.power_mgmt = PowerManagement(self.illumination, self.session)
        
        if self.session:
            self.detectionlog=self.session.detectionlog

        self.power_mgmt.sleep_if_low_bat(print_status)

        if(cfg.ML_MODE):
            self.classifier = Classifier(self.session)

        self.camera.initialize(self.illumination, cfg.SENSOR_PIXFORMAT, cfg.SENSOR_FRAMESIZE,
                        cfg.WIN_RECT, cfg.NB_SENSOR_FRAMEBUFFERS, cfg.EXPOSURE_MODE)
        
        print("camera initialized")
        
        self.image_width = cfg.WIN_RECT.w if cfg.WIN_RECT else sensor.width()
        self.image_height = cfg.WIN_RECT.h if cfg.WIN_RECT else sensor.height()

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
        if (cfg.ML_MODE != ML_Mode.BLOB_CLASS 
            or not Frame.CAN_SAVE_DETECTION_IMG
            or not self.detectionlog):
            return

        frame_blob = jpeg_frame.extract_blob_region(blob, cfg.BLOBS_CROP_METHOD)

        if (frame_blob.can_save()):
            filename = str(jpeg_frame.id) + "_d" + str(self.detectionlog.detection_count) + "_xywh" + str("_".join(map(str,frame_blob.roi_rect)));
            frame_blob.save("blobs", filename)
        if (cfg.ML_MODE == ML_Mode.BLOB_CLASS):
            output = self.classifier.classify(frame_blob.img, cfg.ML_MODE)
            self.detectionlog.append(jpeg_frame.id, labels=self.classifier.labels, confidences=output, rect=blob.rect(), prepend_comma=True)

    def on_background_reset(self):
        """
        Called when the background reference image is reset.
        """
        pass
            
    def run(self):
        ### MAIN LOOP ###
        while(True):
            
            timeutil.clock.tick()

            # turn ON illumination LED at night if always ON || turn OFF illumination LED at daytime, blink busy led every period
            self.illumination.update()

            # handle power mangment, enter deeplseep if needed, lower frame rate using a configured delay
            self.power_mgmt.update()

            ### Take and process picture ###
            
            frame = self.camera.take_picture()
            
            if(self.frame_differencer):
                frame = self.frame_differencer.update(frame)

            if(self.session):
                frame.log(self.session.imagelog)

                if(cfg.ML_MODE==ML_Mode.FRAME_CLASS or cfg.ML_MODE==ML_Mode.OBJECT_DETECT):
                    detection_confidence = self.classifier.classify(frame.img, cfg.ML_MODE, roi_rect=frame.roi_rect)

                if(frame.can_save()):
                    frame.save("img")

            ###

            print("Frames per second: %s" % str(round(timeutil.clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")


# Create and run the application
if __name__ == "__main__":
    app = App()
    app.run()
