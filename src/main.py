# Blob detection and image classification with whole image, image subsets, ROI, or blob-detected bounding rectangles

# import user defined parameters
import config.settings as cfg
from config.settings import Mode
#import libraries
from hardware.camera import Camera
from logging.detection_logger import DetectionLogger
from logging.image_logger import ImageLogger
import sensor, image, time, os, tf, pyb, machine, sys, gc, math
from pyb import Pin, Timer
# import external functions
from ecofunctions import *
from hardware.power import PowerManagement
from hardware.led import *
from timeutil import Suntime, Rtc
from logging.session import Session
from vision.frame import Frame
from vision.frame_differencer import FrameDifferencer
from vision.classifier import Classifier


class App:
    def __init__(self):
        self.solartime = Suntime(cfg.TIME_COVERAGE, cfg.SUNRISE_HOUR, cfg.SUNRISE_MINUTE, cfg.SUNSET_HOUR, cfg.SUNSET_MINUTE)
        self.rtc = Rtc()
        self.exposure_values = cfg.EXPOSURE_BRACKETING_VALUES if cfg.USE_EXPOSURE_BRACKETING else [1]
        self.illumination = Illumination()
        self.camera = Camera()
        self.session: Session
        self.power_mgmt: PowerManagement
        self.is_night = not self.solartime.is_daytime()
        self.frame_differencer: FrameDifferencer
        self.classifier: Classifier
        self.wifi_enabled= cfg.WIFI_ENABLED and wifishield_isconnnected()
        self.imagelog: ImageLogger
        self.detectionlog: DetectionLogger
        
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

        self.power_mgmt = PowerManagement(self.illumination, self.session)
        self.imagelog, self.detectionlog = self.session.imagelog, self.session.detectionlog

        self.power_mgmt.update(self.solartime, print_status)

        #import mobilenet model and labels
        if(cfg.CLASSIFY_MODE != "none"):
            self.classifier = Classifier(self.session)

        self.camera.initialize(self.illumination, cfg.SENSOR_PIXFORMAT, cfg.SENSOR_FRAMESIZE,
                        cfg.WIN_RECT, cfg.NB_SENSOR_FRAMEBUFFERS, cfg.EXPOSURE_MODE)
        
        self.image_width = cfg.WIN_RECT.w if cfg.USE_SENSOR_WINDOWING else sensor.width()
        self.image_height = cfg.WIN_RECT.h if cfg.USE_SENSOR_WINDOWING else sensor.height()

        #start counting time
        self.start_time_status_ms = pyb.millis()
        self.start_time_blending_ms = pyb.millis()
        self.start_time_active_LED_ms = pyb.millis()
        self.clock = time.clock()

        #Frame buffer memory management
        if(cfg.FRAME_DIFF_ENABLED):
            # Initialize the frame differencer
            self.frame_differencer = FrameDifferencer(self.image_width, self.image_height, cfg.SENSOR_PIXFORMAT, self.imagelog)
            frame = self.camera.take_picture(self.solartime.is_daytime(), self.clock, image_type="reference")
            self.frame_differencer.save_reference_image(frame)

            print("Saved background image - now frame differencing!")

    def process_frame(self, frame: Frame, roi_rect: tuple[int, int, int, int]):

        if(cfg.FRAME_DIFF_ENABLED):
            # Process the frame using the frame differencer
            blobs = self.frame_differencer.process_frame(frame)
            if blobs:
                self.process_blobs(blobs, frame)
        
        #log roi image data, possibly classify and save image
        if(cfg.MODE != Mode.LIVE_VIEW):#if frame differencing is disabled, every image is considered triggered and counted outside live view mode

            if (cfg.MODE != Mode.LIVE_VIEW):
                frame.log(self.imagelog)
            
            #classify image
            if(cfg.CLASSIFY_MODE=="image" or cfg.CLASSIFY_MODE=="objects"):
                #revert image_roi replacement to get original image for classification
                if cfg.FRAME_DIFF_ENABLED: frame.img.replace(self.frame_differencer.get_original_image()) 
                detected, detection_confidence = self.classifier.classify(frame.img, cfg.CLASSIFY_MODE, roi_rect=roi_rect)

            # saving picture
            if(cfg.SAVE_ROI_MODE == "all" or cfg.SAVE_ROI_MODE == "trigger" or (cfg.SAVE_ROI_MODE == "detect" and detected)):
                print("Saving ROI or whole image...")
                if cfg.INDICATORS_ENBLED: LED_GREEN_ON()
                if (cfg.FRAME_DIFF_ENABLED): #revert image_roi replacement to get original image for classification
                    frame.img.replace(self.frame_differencer.get_original_image())
                frame.save(str('_'.join(map(str,roi_rect))))
                if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()

    def process_blobs(self, blobs, frame: Frame):
        nb_blobs_to_process = len(blobs) if cfg.MAX_BLOB_TO_PROCESS == -1 else min(cfg.MAX_BLOB_TO_PROCESS, len(blobs))

        for i in range(0, nb_blobs_to_process):
            blob = blobs[i]
            color_statistics = frame.img.get_statistics(roi = blob.rect(), thresholds = cfg.BLOB_COLOR_THRESHOLDS)
            #optional marking of blobs
            if (cfg.INDICATORS_ENBLED):
                frame.mark_blob(blob)
            
            #log each detected blob, we finish the CSV line here if not classifying
            self.detectionlog.append(frame.id, blob, color_statistics, end_line=(cfg.CLASSIFY_MODE != "blobs"))

            if not (cfg.CLASSIFY_MODE == "blobs" or cfg.BLOBS_EXPORT_METHOD!=None):
                continue

            blob_rect, img_blob = frame.extract_blob_region(blob, cfg.BLOBS_EXPORT_METHOD)

            if (cfg.BLOBS_EXPORT_METHOD!=None):
                if (cfg.INDICATORS_ENBLED): LED_GREEN_ON()
                frame.save("blobs", str(frame.id) + "_d" + str(self.detectionlog.detection_count) + "_xywh" + str("_".join(map(str,blob_rect))))
                if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
            if (cfg.CLASSIFY_MODE == "blobs"):
                detected, output = self.classifier.classify(img_blob, cfg.CLASSIFY_MODE)
                self.detectionlog.append(frame.id, labels=self.classifier.labels, confidences=output, rect=blob.rect(), prepend_comma=True)

    def run(self):
        ### MAIN LOOP ###
        while(True):
            self.clock.tick()
            self.is_night = not self.solartime.is_daytime()

            # go to deep sleep when not operation time
            if(not self.solartime.is_operation_time()):
                print("Outside operation time - current time:",time.localtime()[0:6])
                self.illumination.off(message="before deep sleep")
                
                if(cfg.MIN_IMAGE_SCALE < cfg.THRESHOLD_IMAGE_SCALE_DEFER):
                    #deferred analysis of images when scale is too small (not working yet)
                    print("Starting deferred analysis of images before sleeping...")
                    # deferred_analysis(cfg.NET_PATH, cfg.MIN_IMAGE_SCALE, predictions_list)
                
                #compute time until wake-up
                if (cfg.TIME_COVERAGE == "day"):
                    sleep_time = self.solartime.time_until_sunrise()
                elif (cfg.TIME_COVERAGE == "night"):
                    sleep_time = self.solartime.time_until_sunset()
                self.session.save()
                self.session.log_status(self.power_mgmt.get_battery_voltage(), "Outside operation time - Sleeping")
                indicator_dsleep(sleep_time, cfg.ACTIVE_LED_INTERVAL_MS)

            # turn ON illumination LED at night if always ON || turn OFF illumination LED at daytime
            self.illumination.update(self.is_night)

            #log status and battery voltage (if possible) every period
            if (pyb.elapsed_millis(self.start_time_status_ms) > cfg.LOG_STATUS_PERIOD_MS):
                self.start_time_status_ms = pyb.millis()
                print_status=f"Script running - timed check (Y,M,D) {self.rtc.datetime()[0:3]} - (H,M,S) {self.rtc.datetime()[4:7]}"
                self.power_mgmt.update(self.solartime, print_status)

            #blink LED every period
            if (pyb.elapsed_millis(self.start_time_active_LED_ms) > cfg.ACTIVE_LED_INTERVAL_MS):
                self.start_time_active_LED_ms = pyb.millis()
                print("Blinking LED indicator after",str(cfg.ACTIVE_LED_INTERVAL_MS/1000),"seconds")
                LED_BLUE_BLINK(cfg.ACTIVE_LED_DURATION_MS)

            #auto-adjust exposure with user biases or gain, blend frame if frame differencing and no detection
            #wait up to twice expose period
            if (cfg.EXPOSURE_MODE!="auto" and (pyb.elapsed_millis(self.start_time_blending_ms) > cfg.EXPOSE_PERIOD_S * 1000) and not (cfg.FRAME_DIFF_ENABLED and self.frame_differencer.has_found_blobs)
            or (cfg.EXPOSURE_MODE!="auto" and (pyb.elapsed_millis(self.start_time_blending_ms) > 2 * cfg.EXPOSE_PERIOD_S * 1000))):
                
                #blend new frame only if frame differencing
                if (cfg.FRAME_DIFF_ENABLED):
                    print("Blending new frame, saving background image after",str(round(pyb.elapsed_millis(self.start_time_blending_ms)/1000)),"seconds")
                    #take new picture
                    frame = self.camera.take_picture(self.is_night, self.clock)
                    self.frame_differencer.blend_background(frame)
                    
                #reset blending time counter
                self.start_time_blending_ms = pyb.millis()

            ### Take and process picture(s) ###
            #loop over exposure values
            for exposure_mult in self.exposure_values:

                frame = self.camera.take_picture(self.is_night, self.clock, exposure_mult=exposure_mult)

                #start cycling over ROIs
                # cfg.ROIS_RECT) length==1 if cfg.USE_ROI==False
                if (not cfg.USE_ROI):
                    self.process_frame(frame, roi_rect=(0,0,self.image_width,self.image_height))
                else:
                    for roi_rect in cfg.ROI_RECTS:
                        frame = frame.copy(roi=roi_rect,copy_to_fb=True)
                        self.process_frame(frame, roi_rect)

                print("Frames per second: %s" % str(round(self.clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")
            
            #turn auto image adjustments back on if bracketing
            if (cfg.USE_EXPOSURE_BRACKETING):
                self.camera.reset_exposure()

            ### delay loop execution to control frame rate: ###

            pic_delay = cfg.PICTURE_DELAY_S
            # settings indicate regular sleeping for pic_delay seconds
            if (pic_delay > 0 and pic_delay < cfg.SLEEP_THRESHOLD_S):
                print("Delaying frame capture for",pic_delay,"seconds...")
                pyb.delay(pic_delay*1000)
            
            # settings indicate DEEP sleeping for pic_delay seconds to save power
            elif (pic_delay > cfg.SLEEP_THRESHOLD_S):
                # before deep sleep, turn off illumination LEDs if on
                self.illumination.off(no_cooldown=True, message="before deep sleep")
                # save variables and log status before going ot sleep
                self.session.save()
                self.session.log_status(self.power_mgmt.get_battery_voltage(), "Delay loop - Sleeping")
                # go to sleep until next picture with blinking indicator
                indicator_dsleep(pic_delay*1000,cfg.ACTIVE_LED_INTERVAL_MS)

                # (when light sleep is used) check voltage and save status, if battery too low -> sleep until sunrise
                self.power_mgmt.update(self.solartime, "Delay loop - Waking")


# Create and run the application
if __name__ == "__main__":
    app = App()
    app.run()
