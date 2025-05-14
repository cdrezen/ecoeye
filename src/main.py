# Blob detection and image classification with whole image, image subsets, ROI, or blob-detected bounding rectangles

# import user defined parameters
from config.settings import Settings, Mode
#import libraries
import sensor, image, time, os, tf, pyb, machine, sys, uos, gc, math
from pyb import Pin, Timer
# import external functions
from ecofunctions import *
from hardware.voltage_divider import vdiv_build, is_battery_low
from hardware.led import *
from timeutil import suntime, rtc
from classify import load_model
from logging.file import read_filevars, write_filevars, write_status, init_files


cfg = Settings()

AFTER_SUNRISE_DELAY = 30*60*1000 # 30 minutes
# create voltage divider class instance
vdiv_bat = vdiv_build()
# initialise time objects & print date and time from set or updated RTC
solartime = suntime(cfg.operation_coverage, cfg.SUNRISE_HOUR, cfg.SUNRISE_MINUTE, cfg.SUNSET_HOUR, cfg.SUNSET_MINUTE)
rtc = rtc()
exposure_values = cfg.EXPOSURE_BRACKETING_VALUES if cfg.use_exposure_bracketing else [1]
last_exposure = 0
illumination = Illumination()
current_folder, picture_count, detection_count = None, 0, 0
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
img_ref_fb, img_ori_fb = None, None

def check_battery_sleep(vbat=None, print_status=""):
    # check voltage and save status, if battery too low -> sleep until sunrise
    if(vbat == None):
        vbat = vdiv_bat.read_voltage()
    if(print_status != ""):
        write_status(vbat, print_status, current_folder)
    if is_battery_low(vbat):
        write_filevars(current_folder, picture_count, detection_count)
        write_status(vbat,"Battery low - Sleeping", current_folder)
        indicator_dsleep(solartime.time_until_sunrise() + AFTER_SUNRISE_DELAY, cfg.ACTIVE_LED_INTERVAL_MS)

def take_picture(do_expose, exposure_mult = None):
    global last_exposure
    last_exposure = sensor.get_exposure_us()

    if (exposure_mult != None):#cfg.use_exposure_bracketing
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
        expose(cfg.exposure_mode, cfg.EXPOSURE_BIAS_DAY, cfg.EXPOSURE_BIAS_NIGHT,
                cfg.GAIN_BIAS, cfg.EXPOSURE_MS, cfg.GAIN_DB, is_night)
    
    img = sensor.snapshot()

    # after picture, turn OFF selected illumination LEDs if not always ON mode
    if (illumination.can_turn_off()): 
        illumination.off(message="to save power...")

    #log time
    picture_time = "-".join(map(str,time.localtime()[0:6]))

    return img, picture_time

def init():
    global current_folder, picture_count, detection_count, imagelog, detectionlog
    global start_time_status_ms, start_time_blending_ms, start_time_active_LED_ms, clock
    global labels, non_target_indices, wifi_enabled, img_ref_fb, img_ori_fb
    
    # perform quick start from sleep check
    start_check()

    # On wakeup from deep sleep, fetch variables from files
    if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
        current_folder, picture_count, detection_count = read_filevars()
        check_battery_sleep(print_status="Script start - Waking")

    # create and initialize new folders only on powerup or soft reset
    if (machine.reset_cause() != machine.DEEPSLEEP_RESET and cfg.MODE != Mode.LIVE_VIEW):

        # create necessary files & folders
        current_folder, imagelog, detectionlog = init_files(rtc)

        check_battery_sleep(print_status="Script start - Initialising")

    #import mobilenet model and labels
    if(cfg.classify_mode != "none"):
        labels, non_target_indices = load_model()

    # verify that wifi shield is connected when wifi is enabled
    wifi_enabled = cfg.WIFI_ENABLED and wifishield_isconnnected()

    if (cfg.frame_differencing_enabled and cfg.exposure_mode=="auto"): 
        print("ATTENTION: using automatic exposure with frame differencing can result in spurious triggers!")

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
        sensor.set_windowing(windowing.x, windowing.y, windowing.w, windowing.h)

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
    if(cfg.frame_differencing_enabled):
        #de-allocate frame buffer just in case
        sensor.dealloc_extra_fb()
        sensor.dealloc_extra_fb()
        # Take from the main frame buffer's RAM to allocate a second frame buffer.
        img_ref_fb = sensor.alloc_extra_fb(image_width, image_height, sensor_pixformat)
        img_ori_fb = sensor.alloc_extra_fb(image_width, image_height, sensor_pixformat)

        print("Saving background image...")
        picture_count += 1

        img, picture_time = take_picture(do_expose=True)
        img_ref_fb.replace(img)

        img_ref_fb.save(str(current_folder)+"/jpegs/reference/"+str(picture_count)+"_reference.jpg",
                        quality=cfg.JPEG_QUALITY)

        imagelog.append(picture_count, picture_time, 
                        sensor.get_exposure_us(), sensor.get_gain_db(), 
                        "NA", "reference")

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
        if(cfg.MIN_IMAGE_SCALE < cfg.THRESHOLD_IMAGE_SCALE_DEFER):
            print("Starting deferred analysis of images before sleeping...")
            deferred_analysis(net, cfg.MIN_IMAGE_SCALE, predictions_list, current_folder)

        #compute time until wake-up
        if (cfg.operation_coverage == "day"):
            sleep_time = solartime.time_until_sunrise()
        if (cfg.operation_coverage == "night"):
            sleep_time = solartime.time_until_sunset()
        write_filevars(current_folder, picture_count, detection_count)
        write_status(vbat,"Outside operation time - Sleeping",current_folder)
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
        #  update internal RTC from external RTC
        if(cfg.rtc_mode != 'onboard'): ext_rtc.get_time(True)
        print("Updated time (Y,M,D):",rtc.datetime()[0:3],"and time (H,M,S):",rtc.datetime()[4:7])
        # turn on OFF LED module during voltage reading
        illumination.off(message="during voltage reading")
        # check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        check_battery_sleep(vbat=vbat)
        write_status(vbat,"Script running - Normal operation",current_folder)
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
    if (cfg.exposure_mode!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > cfg.EXPOSE_PERIOD_S * 1000) and (not triggered or not cfg.frame_differencing_enabled)
    or (cfg.exposure_mode!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > 2 * cfg.EXPOSE_PERIOD_S * 1000))):
        
        #blend new frame only if frame differencing
        if (cfg.frame_differencing_enabled):
            print("Blending new frame, saving background image after",str(round(pyb.elapsed_millis(start_time_blending_ms)/1000)),"seconds")
            #take new picture
            picture_count += 1
            img, picture_time = take_picture(do_expose=True)
            # Blend in new frame. We're doing 256-alpha here because we want to
            # blend the new frame into the background. Not the background into the
            # new frame which would be just alpha. Blend replaces each pixel by
            # ((NEW*(alpha))+(OLD*(256-alpha)))/256. So, a low alpha results in
            # low blending of the new image while a high alpha results in high
            # blending of the new image. We need to reverse that for this update.
            #blend with frame that is in buffer
            if cfg.INDICATORS_ENBLED: LED_CYAN_ON()
            
            img_ori_fb.blend(img_ref_fb, alpha=(256-cfg.BACKGROUND_BLEND_LEVEL))
            img_ref_fb.replace(img_ori_fb)

            img_ref_fb.save(str(current_folder)+"/jpegs/reference/"+str(picture_count)+"_reference.jpg",
                            quality=cfg.JPEG_QUALITY)

            imagelog.append(picture_count, picture_time, 
                            sensor.get_exposure_us(), sensor.get_gain_db(), 
                            clock.fps(), "reference")
            
            if cfg.INDICATORS_ENBLED: LED_CYAN_OFF()
        #reset blending time counter
        start_time_blending_ms = pyb.millis()

    # TAKING PICTURE
    #loop over exposure values
    for exposure_mult in exposure_values:

        img, picture_time = take_picture(do_expose=False, exposure_mult=exposure_mult)

        #start cycling over ROIs
        # cfg.ROIS_RECT) length==1 if cfg.USE_ROI==False
        for roi_temp in cfg.roi_rects:
            if (cfg.USE_ROI):
                print("Extracting ROI:",roi_temp)
                img_roi=img.copy(roi=roi_temp,copy_to_fb=True)
            else: img_roi=img

            if(cfg.frame_differencing_enabled):
                #save original image
                img_ori_fb.replace(img_roi)

                #compute absolute frame difference
                img_roi.difference(img_ref_fb)
                #set trigger
                triggered = False

                try:
                    blobs = img_roi.find_blobs(cfg.BLOB_COLOR_THRESHOLDS, invert = True, merge = False, pixels_threshold = cfg.MIN_BLOB_PIXELS)
                    #filter blobs with maximum pixels condition
                    blobs_filt = [item for item in blobs if item[4]< cfg.MAX_BLOB_PIXELS]

                    if (len(blobs_filt)>0):
                        print(len(blobs_filt),"blob(s) within range!")
                        triggered = True
                        picture_count += 1

                    for blob in blobs_filt:
                        detection_count += 1
                        color_statistics_temp = img.get_statistics(roi = blob.rect(), thresholds = cfg.BLOB_COLOR_THRESHOLDS)
                        #optional marking of blobs
                        if (cfg.INDICATORS_ENBLED):
                            img.draw_edges(blob.corners(), color=(0,0,255), thickness=5)
                            img.draw_rectangle(blob.rect(), color=(255,0,0), thickness=5)
                        
                        #log each detected blob
                        detectionlog.append(detection_count, picture_count, 
                                            blob.pixels(), blob.elongation(),
                                            blob.corners()[0][0], blob.corners()[0][1], 
                                            blob.corners()[1][0], blob.corners()[1][1],
                                            blob.corners()[2][0], blob.corners()[2][1], 
                                            blob.corners()[3][0], blob.corners()[3][1],
                                            color_statistics_temp.l_mode(), color_statistics_temp.l_min(), color_statistics_temp.l_max(),
                                            color_statistics_temp.a_mode(), color_statistics_temp.a_min(), color_statistics_temp.a_max(),
                                            color_statistics_temp.b_mode(), color_statistics_temp.b_min(), color_statistics_temp.b_max(),
                                            end_line=(cfg.classify_mode != "blobs"))
                                            #we finish the CSV line here if not classifying

                        if (cfg.classify_mode == "blobs" or cfg.BLOBS_EXPORT_METHOD!="none"):
                            #set blob bounding box according to user parameters
                            if (cfg.BLOBS_EXPORT_METHOD=="rectangle"):
                                blob_rect=blob.rect()
                            elif (cfg.BLOBS_EXPORT_METHOD=="square"):
                                #get longest side of blob's bounding rectangle
                                if (blob.w()>=blob.h()):
                                    blob_h=blob.w()
                                else: blob_h=blob.h()
                                if (blob.h()>blob.w()):
                                    blob_w=blob.h()
                                else: blob_w=blob.w()
                                if (blob_h>image_height):
                                    if cfg.INDICATORS_ENBLED: print("Cannot export blob bounding square as its height would exceed the image height! Using image height instead.")
                                    blob_h=image_height
                                #get new coordinates depending on location of blob relative to border
                                if (blob.x()+blob_w>=image_width):
                                    blob_x=image_width-blob_w
                                else: blob_x=blob.x()
                                if (blob.y()+blob_h>=image_height):
                                    blob_y=image_height-blob_w
                                else: blob_y=blob.y()
                                #set blob
                                blob_rect=(blob_x,blob_y,blob_w,blob_h)
                                #draw square
                                if (cfg.INDICATORS_ENBLED):
                                    img.draw_rectangle(blob_rect, color=(0,255,0), thickness=10)
                            #extract blob
                            img_blob=img_ori_fb.copy(roi=blob_rect,copy_to_fb=True)
                            #saving extracted blob rectangles/squares
                            if (cfg.BLOBS_EXPORT_METHOD!="none"):
                                #optional: turn on LED while saving blob bounding boxes
                                if (cfg.INDICATORS_ENBLED):
                                    LED_GREEN_ON()
                                print("Exporting blob bounding", cfg.BLOBS_EXPORT_METHOD, "...")
                                img_blob.save(str(current_folder)+"/jpegs/blobs/" + str(picture_count) + "_d" + str(detection_count) + "_xywh" + str("_".join(map(str,blob_rect))) + ".jpg",quality=cfg.JPEG_QUALITY)
                                if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
                            if (cfg.classify_mode == "blobs"):
                                #optional: turn on LED while classifying
                                if cfg.INDICATORS_ENBLED: LED_YELLOW_ON()
                                #rescale blob rectangle
                                img_blob_resized=img_blob.copy(x_size=cfg.MODEL_RES,y_size=cfg.MODEL_RES,copy_to_fb=True,hint=image.BICUBIC)
                                # we do not need a loop since we do not analyse blob subsets
                                obj = tf.classify(net,img_blob_resized)[0]
                                predictions_list = list(zip(labels, obj.output()))
                                print("Predictions for classified blob:", predictions_list)

                                detectionlog.append(";".join(map(str,labels)), 
                                                    ";".join(map(str,obj.output())), 
                                                    blob.rect()[0], blob.rect()[1], 
                                                    blob.rect()[2], blob.rect()[3], 
                                                    prepend_comma=True)

                                if cfg.INDICATORS_ENBLED: LED_YELLOW_OFF()

                        #go to next loop if only first blob is needed
                        if (cfg.BLOB_TASK == "stop"):
                            break

                except MemoryError:
                    #when there is a memory error, we assume that it is triggered because of many blobs
                    triggered = True
                    picture_count += 1
                    write_status("-","memory error",current_folder)
            #if frame differencing is disabled, every image is considered triggered and counted outside live view mode
            elif (cfg.MODE != Mode.LIVE_VIEW):
                triggered = True
                picture_count += 1
            #log roi image data, possibly classify and save image
            if(triggered):
                #save image log
                if (cfg.MODE != Mode.LIVE_VIEW):
                    if (not cfg.USE_ROI):
                        imagelog.append(picture_count, picture_time, 
                                        sensor.get_exposure_us(), sensor.get_gain_db(), 
                                        clock.fps())
                    else:
                        imagelog.append(picture_count, picture_time, 
                                        sensor.get_exposure_us(), sensor.get_gain_db(), 
                                        clock.fps(), roi_temp[0], roi_temp[1], 
                                        roi_temp[2], roi_temp[3])
                # init detection confidence variable
                detection_confidence = 0
                #classify image
                if(cfg.classify_mode=="image"):
                    if cfg.INDICATORS_ENBLED: LED_YELLOW_ON()
                    print("Running image classification on ROI...")
                    detected = False
                    #revert image_roi replacement to get original image for classification
                    if cfg.frame_differencing_enabled: img_roi.replace(img_ori_fb)
                    #only analyse when classification is feasible within reasonable time frame
                    if (cfg.MIN_IMAGE_SCALE >= cfg.THRESHOLD_IMAGE_SCALE_DEFER):
                        print("Classifying ROI or image...")
                        #rescale image to get better model results
                        img_net=img_roi.copy(x_size=cfg.MODEL_RES,y_size=cfg.MODEL_RES,copy_to_fb=True,hint=image.BICUBIC)
                        #start image classification
                        for obj in tf.classify(net, img_roi, min_scale=cfg.MIN_IMAGE_SCALE, scale_mul=0.5, x_overlap=0.5, y_overlap=0.5):
                            #initialise threshold check
                            threshold_exceeded =  False
                            #put predictions in readable format
                            predictions_list = list(zip(labels, obj.output()))
                            print("Predictions at [x=%d,y=%d,w=%d,h=%d]" % obj.rect(),":")
                            #check threshold for each target item
                            for i in range(len(predictions_list)):
                                print("%s = %f" % (predictions_list[i][0], predictions_list[i][1]))
                                if (i == non_target_indices): continue
                                if (predictions_list[i][1] > cfg.THRESHOLD_CONFIDENCE):
                                        threshold_exceeded =  True
                            #log model scores if any target is above threshold
                            if(threshold_exceeded):
                                detected = True
                                detection_count +=1
                                print("Detected target! Logging detection...")
                                #logging detection
                                detectionlog.append(detection_count, picture_count, 
                                                    "NA", "NA", "NA", "NA", 
                                                    "NA", "NA", "NA", "NA", 
                                                    "NA", "NA", "NA", "NA", 
                                                    "NA", "NA", "NA", "NA", 
                                                    "NA", "NA", "NA",
                                                    ";".join(map(str,labels)), 
                                                    ";".join(map(str,obj.output())), 
                                                    roi_temp[0], roi_temp[1], 
                                                    roi_temp[2], roi_temp[3])

                    if cfg.INDICATORS_ENBLED: LED_YELLOW_OFF()
                #object detection. not compatible with ROI mode
                if(cfg.classify_mode=="objects" and not cfg.USE_ROI):
                    if cfg.INDICATORS_ENBLED: LED_YELLOW_ON()
                    print("Running object detection on ROI...")
                    detected = False
                    #revert image_roi replacement to get original image for classification
                    if cfg.frame_differencing_enabled: img_roi.replace(img_ori_fb)
                    #loop through labels
                    for i, detection_list in enumerate(tf.detect(net,img_roi, thresholds=[(math.ceil(cfg.THRESHOLD_CONFIDENCE * 255), 255)])):
                        if (i == 0): continue # background class
                        if (len(detection_list) == 0): continue # no detections for this class?
                        detected = True
                        print("********** %s **********" % labels[i])
                        #print([j for m in detection_list for j in m])
                        print("whole list",detection_list)
                        for d in detection_list:
                            if(detection_confidence < d[4]): detection_confidence = d[4]
                            detection_count +=1
                            [x, y, w, h] = d.rect()
                            
                            #optional: display bounding box
                            if (cfg.INDICATORS_ENBLED):
                                img.draw_rectangle(d.rect(), color=cfg.CLASS_COLORS[i+1], thickness=2)
                            
                            detectionlog.append(detection_count, picture_count, 
                                                "NA", "NA", "NA", "NA", 
                                                "NA", "NA", "NA", "NA",
                                                "NA", "NA", "NA", "NA", 
                                                "NA", "NA", "NA", "NA", 
                                                "NA", "NA", "NA",
                                                labels[i], d[4], d[0], d[1], d[2], d[3])
                    if cfg.INDICATORS_ENBLED: LED_YELLOW_OFF()
                elif(cfg.classify_mode=="objects" and cfg.USE_ROI): print("Object detection skipped, as it is not compatible with using ROIs!")

                # saving picture
                if(cfg.save_roi_mode == "all" or cfg.save_roi_mode == "trigger" or (cfg.save_roi_mode == "detect" and detected)):
                    print("Saving ROI or whole image...")
                    if cfg.INDICATORS_ENBLED: LED_GREEN_ON()
                    #revert image_roi replacement to get original image for classification
                    if (cfg.frame_differencing_enabled): img_roi.replace(img_ori_fb)
                    # Save picture with detection ID
                    img_roi.save(str(current_folder)+"/jpegs/"+ str('_'.join(map(str,roi_temp))) + "/" + str(picture_count) + ".jpg",quality=cfg.JPEG_QUALITY)
                    if cfg.INDICATORS_ENBLED: LED_GREEN_OFF()
                # copy and save compressed image to send it over wifi later
                if(wifi_enabled and cfg.UPLOAD_IMAGE_ENABLED and detection_confidence >= cfg.UPLOAD_CONFIDENCE_THRESHOLD):
                    print("Original image size :", img.size()/1024,"kB")
                    cp_img = img.copy(x_scale=0.1,y_scale=0.1,copy_to_fb=True,hint=image.BICUBIC)
                    print("Size of image for WiFi transfer :", cp_img.size()/1024,"kB")
                    cp_img.save("cp_img.jpg",quality=cfg.JPEG_QUALITY)
                    
            print("Frames per second: %s" % str(round(clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")
    
    #turn auto image adjustments back on if bracketing
    if (cfg.use_exposure_bracketing):
        if(cfg.exposure_mode=="auto"):
            #auto gain and exposure
            sensor.set_auto_gain(True)
            sensor.set_auto_exposure(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(cfg.exposure_mode=="exposure"):
            #auto gain
            sensor.set_auto_gain(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(cfg.exposure_mode=="bias"):
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
        write_filevars(current_folder, picture_count, detection_count)
        write_status(vbat,"Delay loop - Sleeping",current_folder)
        # go to sleep until next picture with blinking indicator
        indicator_dsleep(pic_delay*1000,cfg.ACTIVE_LED_INTERVAL_MS)

        # (when light sleep is used) check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        check_battery_sleep(vbat=vbat)
        write_status(vbat,"Delay loop - waking",current_folder)
