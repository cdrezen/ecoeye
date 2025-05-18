# Blob detection and image classification with whole image, image subsets, ROI, or blob-detected bounding rectangles

# import user defined parameters
import config.settings as cfg
from config.settings import Mode
#import libraries
from hardware.camera import Camera
import sensor, image, time, os, tf, pyb, machine, sys, gc, math
from pyb import Pin, Timer
# import external functions
from ecofunctions import *
from hardware.voltage_divider import vdiv_build, is_battery_low
from hardware.led import *
from timeutil import Suntime, Rtc
from logging.session import Session
from vision.frame import Frame
from vision.frame_differencer import FrameDifferencer
from vision.classifier import Classifier


AFTER_SUNRISE_DELAY = 30*60*1000 # 30 minutes
# create voltage divider class instance
vdiv_bat = vdiv_build()
# initialise time objects & print date and time from set or updated RTC
solartime = Suntime(cfg.TIME_COVERAGE, cfg.SUNRISE_HOUR, cfg.SUNRISE_MINUTE, cfg.SUNSET_HOUR, cfg.SUNSET_MINUTE)
rtc = Rtc()
exposure_values = cfg.EXPOSURE_BRACKETING_VALUES if cfg.USE_EXPOSURE_BRACKETING else [1]
last_exposure = 0
illumination = Illumination()
camera = Camera()
session: Session = None
picture_count, detection_count = 0, 0
imagelog, detectionlog = None, None
is_night = not solartime.is_daytime()
# future image width and height
image_width = cfg.WIN_RECT.w if cfg.USE_SENSOR_WINDOWING else sensor.width()
image_height = cfg.WIN_RECT.h if cfg.USE_SENSOR_WINDOWING else sensor.height()
#start counting time
start_time_status_ms = 0
start_time_blending_ms = 0
start_time_active_LED_ms = 0
#set trigger and detected state
triggered = False
detected = False
#start clock
clock = None
# Frame differencing handler
frame_differencer: FrameDifferencer = None
classifier: Classifier = None

def check_battery_sleep(vbat=None, print_status=""):
    # check voltage and save status, if battery too low -> sleep until sunrise
    if(vbat == None):
        vbat = vdiv_bat.read_voltage()
    if(print_status != ""):
        session.log_status(vbat, print_status)
    if is_battery_low(vbat):
        session.save()
        session.log_status(vbat, "Battery low - Sleeping")
        indicator_dsleep(solartime.time_until_sunrise() + AFTER_SUNRISE_DELAY, cfg.ACTIVE_LED_INTERVAL_MS)

def process_blobs(blobs, frame: Frame):

    nb_blobs_to_process = len(blobs) if cfg.MAX_BLOB_TO_PROCESS == -1 else min(cfg.MAX_BLOB_TO_PROCESS, len(blobs))

    for i in range(nb_blobs_to_process):
        blob = blobs[i]
        color_statistics = frame.get_statistics(roi = blob.rect(), thresholds = cfg.BLOB_COLOR_THRESHOLDS)
        #optional marking of blobs
        if (cfg.INDICATORS_ENBLED):
            frame.mark_blob(blob)
        
        #log each detected blob, we finish the CSV line here if not classifying
        detectionlog.append(frame.id, blob, color_statistics, end_line=(cfg.CLASSIFY_MODE != "blobs"))

        if not (cfg.CLASSIFY_MODE == "blobs" or cfg.BLOBS_EXPORT_METHOD!="none"):
            continue

        blob_rect, img_blob = frame.extract_blob_region(blob, cfg.BLOBS_EXPORT_METHOD)

        if (cfg.BLOBS_EXPORT_METHOD!="none"):
            if (cfg.INDICATORS_ENBLED): LED_GREEN_ON()
            frame.save("blobs", str(frame.id) + "_d" + str(detectionlog.detection_count) + "_xywh" + str("_".join(map(str,blob_rect))))
            if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
        if (cfg.CLASSIFY_MODE == "blobs"):
            output = classifier.classify(img_blob, cfg.CLASSIFY_MODE)
            detectionlog.append(frame.id, labels=classifier.labels,  confidences=output, rect=blob.rect(), prepend_comma=True)


def init():
    global start_time_status_ms, start_time_blending_ms, start_time_active_LED_ms, clock
    global wifi_enabled, session, imagelog, detectionlog, classifier
    
    # perform quick start from sleep check
    start_check()

    print(f"Initializing on {Mode.to_str(cfg.MODE)} mode...")

    # On wakeup from deep sleep, fetch environment from session.json
    if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
        session = Session.load()
        if not session: session = Session.create(rtc)
        check_battery_sleep(print_status="Script start - Waking")

    # create and initialize new folders only on powerup or soft reset
    if (machine.reset_cause() != machine.DEEPSLEEP_RESET and cfg.MODE != Mode.LIVE_VIEW):
        # create necessary files & folders
        session = Session.create(rtc)
        check_battery_sleep(print_status="Script start - Initialising")

    imagelog, detectionlog = session.imagelog, session.detectionlog

    #import mobilenet model and labels
    if(cfg.CLASSIFY_MODE != "none"):
        classifier = Classifier(session)

    # verify that wifi shield is connected when wifi is enabled
    wifi_enabled = cfg.WIFI_ENABLED and wifishield_isconnnected()

    camera.initialize(illumination, cfg.SENSOR_PIXFORMAT, cfg.SENSOR_FRAMESIZE,
                       cfg.WIN_RECT, cfg.NB_SENSOR_FRAMEBUFFERS, cfg.EXPOSURE_MODE)


    #start counting time
    start_time_status_ms = pyb.millis()
    start_time_blending_ms = pyb.millis()
    start_time_active_LED_ms = pyb.millis()
    clock = time.clock()

    #Frame buffer memory management
    if(cfg.FRAME_DIFF_ENABLED):
        # Initialize the frame differencer
        frame_differencer = FrameDifferencer(image_width, image_height, cfg.SENSOR_PIXFORMAT, imagelog)
        frame = camera.take_picture(solartime.is_daytime(), clock, image_type="reference")
        frame_differencer.save_reference_image(frame)

        print("Saved background image - now frame differencing!")

    return

init()

### MAIN LOOP ###
while(True):

    # go to deep sleep when not operation time
    if(not solartime.is_operation_time()):
        # outside of operation time
        print("Outside operation time - current time:",time.localtime()[0:6])
        # before deep sleep, turn off illumination LEDs if on
        illumination.off("before deep sleep")
        #deferred analysis of images when scale is too small (not working yet)
        # TODO: re-implement deferred analysis
        if(cfg.MIN_IMAGE_SCALE < cfg.THRESHOLD_IMAGE_SCALE_DEFER):
            print("Starting deferred analysis of images before sleeping...")
            # deferred_analysis(cfg.NET_PATH, cfg.MIN_IMAGE_SCALE, predictions_list)

        #compute time until wake-up
        if (cfg.TIME_COVERAGE == "day"):
            sleep_time = solartime.time_until_sunrise()
        if (cfg.TIME_COVERAGE == "night"):
            sleep_time = solartime.time_until_sunset()
        session.save()
        session.log_status(vbat, "Outside operation time - Sleeping")
        indicator_dsleep(sleep_time, cfg.ACTIVE_LED_INTERVAL_MS)

    # continue script when operation time
    
    clock.tick()
    # update night time check
    is_night = not solartime.is_daytime()

    # turn ON illumination LED at night if always ON || turn OFF illumination LED at daytime
    illumination.update(is_night)

    #log status and battery voltage (if possible) every period
    if (pyb.elapsed_millis(start_time_status_ms) > cfg.LOG_STATUS_PERIOD_MS):
        start_time_status_ms = pyb.millis()
        print("Updated time (Y,M,D):",rtc.datetime()[0:3],"and time (H,M,S):",rtc.datetime()[4:7])
        # turn on OFF LED module during voltage reading
        illumination.off(message="during voltage reading")
        # check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        check_battery_sleep(vbat=vbat)
        session.log_status(vbat, "Script running - Normal operation")
        # at night, turn ON selected illumination LEDs if always ON mode
        if(illumination.can_turn_on(is_night)):
            illumination.on(message="after voltage reading")

    #blink LED every period
    if (pyb.elapsed_millis(start_time_active_LED_ms) > cfg.ACTIVE_LED_INTERVAL_MS):
        start_time_active_LED_ms = pyb.millis()
        print("Blinking LED indicator after",str(cfg.ACTIVE_LED_INTERVAL_MS/1000),"seconds")
        LED_BLUE_BLINK(cfg.ACTIVE_LED_DURATION_MS)

    #auto-adjust exposure with user biases or gain, blend frame if frame differencing and no detection
    #wait up to twice expose period
    if (cfg.EXPOSURE_MODE!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > cfg.EXPOSE_PERIOD_S * 1000) and (not triggered or not cfg.FRAME_DIFF_ENABLED)
    or (cfg.EXPOSURE_MODE!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > 2 * cfg.EXPOSE_PERIOD_S * 1000))):
        
        #blend new frame only if frame differencing
        if (cfg.FRAME_DIFF_ENABLED):
            print("Blending new frame, saving background image after",str(round(pyb.elapsed_millis(start_time_blending_ms)/1000)),"seconds")
            #take new picture
            frame = camera.take_picture(is_night, clock)
            frame_differencer.blend_background(frame)
            
        #reset blending time counter
        start_time_blending_ms = pyb.millis()

    # TAKING PICTURE
    #loop over exposure values
    for exposure_mult in exposure_values:

        frame = camera.take_picture(is_night, clock, exposure_mult=exposure_mult)

        #start cycling over ROIs
        # cfg.ROIS_RECT) length==1 if cfg.USE_ROI==False
        for roi_temp in cfg.ROI_RECTS:
            if (cfg.USE_ROI):
                frame = frame.copy(roi=roi_temp,copy_to_fb=True)

            if(cfg.FRAME_DIFF_ENABLED):
                # Process the frame using the frame differencer
                frame, triggered, blobs = frame_differencer.process_frame(frame)
                if (triggered):
                    print(len(blobs),"blob(s) within range!")
                    process_blobs(blobs, frame)
            
            #log roi image data, possibly classify and save image
            if(triggered or cfg.MODE != Mode.LIVE_VIEW):#if frame differencing is disabled, every image is considered triggered and counted outside live view mode

                if (cfg.MODE != Mode.LIVE_VIEW):
                    frame.log(imagelog)
                
                detection_confidence = 0
                
                #classify image
                if(cfg.CLASSIFY_MODE=="image" or cfg.CLASSIFY_MODE=="objects"):
                    #revert image_roi replacement to get original image for classification
                    if cfg.FRAME_DIFF_ENABLED: frame.img.replace(frame_differencer.get_original_image()) 
                    detected, detection_confidence = classifier.classify(frame.img, cfg.CLASSIFY_MODE, roi_rect=roi_temp)

                # saving picture
                if(cfg.SAVE_ROI_MODE == "all" or cfg.SAVE_ROI_MODE == "trigger" or (cfg.SAVE_ROI_MODE == "detect" and detected)):
                    print("Saving ROI or whole image...")
                    if cfg.INDICATORS_ENBLED: LED_GREEN_ON()
                    #revert image_roi replacement to get original image for classification
                    if (cfg.FRAME_DIFF_ENABLED): frame.img.replace(frame_differencer.get_original_image())
                    # Save picture with detection ID
                    frame.save(str(session.path)+"/jpegs/"+ str('_'.join(map(str,roi_temp))) + "/" + str(imagelog.picture_count) + ".jpg",quality=cfg.JPEG_QUALITY)
                    if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
               
                # copy and save compressed image to send it over wifi later
                if(wifi_enabled and cfg.UPLOAD_IMAGE_ENABLED and detection_confidence >= cfg.UPLOAD_CONFIDENCE_THRESHOLD):
                    print("Original image size :", frame.img.size()/1024,"kB")
                    cp_img = frame.img.copy(x_scale=0.1,y_scale=0.1,copy_to_fb=True,hint=image.BICUBIC)
                    print("Size of image for WiFi transfer :", cp_img.size()/1024,"kB")
                    cp_img.save("cp_img.jpg",quality=cfg.JPEG_QUALITY)
                    
            print("Frames per second: %s" % str(round(clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")
    
    #turn auto image adjustments back on if bracketing
    if (cfg.USE_EXPOSURE_BRACKETING):
        camera.reset_exposure()

    # send detection data over wifi
    if(wifi_enabled and detected):
        # conect to WiFi, this migth take while depending on the signal strength
        print("Detection confidence ", detection_confidence*100,"%")
        wifi_connected = wifi_connect(cfg.WIFI_SSID, cfg.WIFI_KEY)
        if(wifi_connected):
            # send confidence level to server
            if(cfg.UPLOAD_CONFIDENCE_ENABLED):
                data_transfer(cfg.UPLOAD_DATA_API_URL, detection_confidence)
            if(cfg.UPLOAD_IMAGE_ENABLED and detection_confidence >= cfg.UPLOAD_CONFIDENCE_THRESHOLD):
                detection_image = open("cp_img.jpg", "rb")
                image_transfer(cfg.UPLOAD_IMG_URL, detection_image)
            # disconnect from wifi asap to save energy
            wifi_disconnect()

    #if cfg.INDICATORS_ENBLED: print("Frame buffers:",sensor.get_framebuffers())
    #delay loop execution to control frame rate
    pic_delay = cfg.picture_delay_s

    if (pic_delay > 0 and pic_delay < cfg.SLEEP_THRESHOLD_S):
        print("Delaying frame capture for",pic_delay,"seconds...")
        pyb.delay(pic_delay*1000)

    if (pic_delay > cfg.SLEEP_THRESHOLD_S):
        # before deep sleep, turn off illumination LEDs if on
        illumination.off(no_cooldown=True, message="before deep sleep")
        # save variables and log status before going ot sleep
        session.save()
        session.log_status(vbat, "Delay loop - Sleeping")
        # go to sleep until next picture with blinking indicator
        indicator_dsleep(pic_delay*1000,cfg.ACTIVE_LED_INTERVAL_MS)

        # (when light sleep is used) check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        check_battery_sleep(vbat=vbat)
        session.log_status(vbat, "Delay loop - Waking")
