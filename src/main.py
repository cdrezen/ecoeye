# Blob detection and image classification with whole image, image subsets, ROI, or blob-detected bounding rectangles

# import user defined parameters
import config.settings as cfg
from config.settings import Mode
#import libraries
import sensor, image, time, os, tf, pyb, machine, sys, gc, math
from pyb import Pin, Timer
# import external functions
from ecofunctions import *
from hardware.voltage_divider import vdiv_build, is_battery_low
from hardware.led import *
from timeutil import Suntime, Rtc
from logging.session import Session
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

def take_picture(do_expose, exposure_mult = None):
    global last_exposure
    last_exposure = sensor.get_exposure_us()

    if (exposure_mult != None):#cfg.USE_EXPOSURE_BRACKETING
        #fix the gain so image is stable
        sensor.set_auto_gain(False, gain_db=sensor.get_gain_db())
        print("Exposure bracketing bias:",exposure_mult)
        sensor.set_auto_exposure(False, exposure_us=int(last_exposure*exposure_mult))
        #wait for new exposure time to be applied
        sensor.skip_frames(time = 2000)

    # at night, turn ON selected illumination LEDs if not always OFF mode
    if(illumination.can_turn_on(is_night)):
        illumination.on(message="to take the picture")

    if (do_expose):
        expose(cfg.EXPOSURE_MODE, cfg.EXPOSURE_BIAS_DAY, cfg.EXPOSURE_BIAS_NIGHT,
                cfg.GAIN_BIAS, cfg.EXPOSURE_MS, cfg.GAIN_DB, is_night)
    
    img = sensor.snapshot()

    # after picture, turn OFF selected illumination LEDs if not always ON mode
    if (illumination.can_turn_off()): 
        illumination.off(message="to save power...")

    #log time
    picture_time = "-".join(map(str,time.localtime()[0:6]))

    return img, picture_time

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

    ### SENSOR INIT ###

    #indicate initialisation with LED
    LED_WHITE_BLINK(200,3)
    # Reset and initialize the sensor
    sensor.reset()
    #we need RGB565 for frame differencing and MobileNet
    sensor_pixformat = cfg.SENSOR_PIXFORMAT
    windowing = cfg.WIN_RECT
    
    sensor.set_pixformat(sensor_pixformat)
    sensor.set_framesize(cfg.SENSOR_FRAMESIZE)

    if (cfg.USE_SENSOR_WINDOWING):
        sensor.set_windowing((windowing.x, windowing.y, windowing.w, windowing.h))

    if (cfg.USE_SENSOR_FRAMEBUFFERS): 
        sensor.set_framebuffers(cfg.NB_SENSOR_FRAMEBUFFERS)

    # Give the camera sensor time to adjust
    sensor.skip_frames(time=1000)

    #parameter validity checks
    if (windowing.y + windowing.h > sensor.height() or windowing.x + windowing.w > sensor.width()):
        print("windowing_y:", windowing.y, "windowing_h:", windowing.h, "sensor.height:", sensor.height())
        print("windowing_x:", windowing.x, "windowing_w:", windowing.w, "sensor.width:", sensor.width())
        sys.exit("Windowing dim exceeds image dim!")

    #Frame buffer memory management
    if(cfg.FRAME_DIFF_ENABLED):
        # Initialize the frame differencer
        frame_differencer = FrameDifferencer(image_width, image_height, sensor_pixformat, imagelog)
        img, picture_time = take_picture(do_expose=True)
        frame_differencer.save_reference_image(img, picture_time)

        print("Saved background image - now frame differencing!")

    #start counting time
    start_time_status_ms = pyb.millis()
    start_time_blending_ms = pyb.millis()
    start_time_active_LED_ms = pyb.millis()
    clock = time.clock()
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
            img, picture_time = take_picture(do_expose=True)
            frame_differencer.blend_background(img, picture_time, clock.fps())
            
        #reset blending time counter
        start_time_blending_ms = pyb.millis()

    # TAKING PICTURE
    #loop over exposure values
    for exposure_mult in exposure_values:

        img, picture_time = take_picture(do_expose=False, exposure_mult=exposure_mult)

        #start cycling over ROIs
        # cfg.ROIS_RECT) length==1 if cfg.USE_ROI==False
        for roi_temp in cfg.ROI_RECTS:
            img_roi = img if (not cfg.USE_ROI) else img.copy(roi=roi_temp,copy_to_fb=True)

            if(cfg.FRAME_DIFF_ENABLED):
                # Process the frame using the frame differencer
                img_roi, triggered, blobs = frame_differencer.process_frame(img_roi)

                if (triggered):
                    print(len(blobs),"blob(s) within range!")

                for blob in blobs:
                    color_statistics = img.get_statistics(roi = blob.rect(), thresholds = cfg.BLOB_COLOR_THRESHOLDS)
                    #optional marking of blobs
                    if (cfg.INDICATORS_ENBLED):
                        frame_differencer.mark_blobs(img, [blob])
                    
                    #log each detected blob
                    detectionlog.append(imagelog.picture_count, blob, color_statistics, end_line=(cfg.CLASSIFY_MODE != "blobs"))
                                        #we finish the CSV line here if not classifying

                    if (cfg.CLASSIFY_MODE == "blobs" or cfg.BLOBS_EXPORT_METHOD!="none"):
                        # Extract blob region using frame differencer
                        blob_rect, img_blob = frame_differencer.extract_blob_region(blob)
                        
                    if (cfg.BLOBS_EXPORT_METHOD!="none"):
                        #saving extracted blob rectangles/squares
                        if (cfg.INDICATORS_ENBLED): LED_GREEN_ON()
                        print("Exporting blob bounding", cfg.BLOBS_EXPORT_METHOD, "...")
                        img_blob.save("jpegs/blobs/" + str(imagelog.picture_count) + "_d" + str(detectionlog.detection_count) + "_xywh" + str("_".join(map(str,blob_rect))) + ".jpg",quality=cfg.JPEG_QUALITY)
                        if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
                    if (cfg.CLASSIFY_MODE == "blobs"):
                        output = classifier.classify(img_blob, cfg.CLASSIFY_MODE)
                        detectionlog.append(imagelog.picture_count, labels=classifier.labels, 
                                            confidences=output, rect=blob.rect(), prepend_comma=True)
                    #go to next loop if only first blob is needed
                    if (cfg.BLOB_TASK == "stop"):
                        break
            
            #log roi image data, possibly classify and save image
            if(triggered or cfg.MODE != Mode.LIVE_VIEW):#if frame differencing is disabled, every image is considered triggered and counted outside live view mode
                #save image log
                if (cfg.MODE != Mode.LIVE_VIEW):
                    imagelog.append(picture_time, clock.fps(), roi_temp)
                # init detection confidence variable
                detection_confidence = 0
                #classify image
                if(cfg.CLASSIFY_MODE=="image" or cfg.CLASSIFY_MODE=="objects"):
                    #revert image_roi replacement to get original image for classification
                    if cfg.FRAME_DIFF_ENABLED: frame_differencer.restore_original_image(img_roi)     
                    detected, detection_confidence = classifier.classify(img_roi, cfg.CLASSIFY_MODE, roi_rect=roi_temp)

                # saving picture
                if(cfg.SAVE_ROI_MODE == "all" or cfg.SAVE_ROI_MODE == "trigger" or (cfg.SAVE_ROI_MODE == "detect" and detected)):
                    print("Saving ROI or whole image...")
                    if cfg.INDICATORS_ENBLED: LED_GREEN_ON()
                    #revert image_roi replacement to get original image for classification
                    if (cfg.FRAME_DIFF_ENABLED): frame_differencer.restore_original_image(img_roi)
                    # Save picture with detection ID
                    img_roi.save(str(session.path)+"/jpegs/"+ str('_'.join(map(str,roi_temp))) + "/" + str(imagelog.picture_count) + ".jpg",quality=cfg.JPEG_QUALITY)
                    if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
               
                # copy and save compressed image to send it over wifi later
                if(wifi_enabled and cfg.UPLOAD_IMAGE_ENABLED and detection_confidence >= cfg.UPLOAD_CONFIDENCE_THRESHOLD):
                    print("Original image size :", img.size()/1024,"kB")
                    cp_img = img.copy(x_scale=0.1,y_scale=0.1,copy_to_fb=True,hint=image.BICUBIC)
                    print("Size of image for WiFi transfer :", cp_img.size()/1024,"kB")
                    cp_img.save("cp_img.jpg",quality=cfg.JPEG_QUALITY)
                    
            print("Frames per second: %s" % str(round(clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")
    
    #turn auto image adjustments back on if bracketing
    if (cfg.USE_EXPOSURE_BRACKETING):
        if(cfg.EXPOSURE_MODE=="auto"):
            #auto gain and exposure
            sensor.set_auto_gain(True)
            sensor.set_auto_exposure(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(cfg.EXPOSURE_MODE=="exposure"):
            #auto gain
            sensor.set_auto_gain(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(cfg.EXPOSURE_MODE=="bias"):
            exposure_bias = cfg.EXPOSURE_BIAS_NIGHT if is_night else cfg.EXPOSURE_BIAS_DAY
            # re-set exposure
            sensor.set_auto_exposure(False, \
                exposure_us = int(last_exposure))
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)

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
