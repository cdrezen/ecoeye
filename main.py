# Blob detection and image classification with whole image, image subsets, ROI, or blob-detected bounding rectangles

# import user defined parameters
from config.settings import *
#import libraries
import sensor, image, time, os, tf, pyb, machine, sys, uos, gc, math
from pyb import Pin, Timer
# import external functions
from ecofunctions import *
# perform quick start from sleep check
start_check()
# set settings according to user defined shortcut mode
use_shortcut_mode(MODE)
from config.settings import *# reimport settings (ugly: TODO: name settings module or use object)


# ━━━━━━━━━━ 𝗩𝗢𝗟𝗧𝗔𝗚𝗘 𝗗𝗜𝗩𝗜𝗗𝗘𝗥 ━━━━━━━━━━
# resistors values on voltage divider circuits
R_1_PMS_LED = 30
R_2_PMS_LED = 8.82352941176
R_1_PMS_noLED = 30
R_2_PMS_noLED = 100
R_1_noPMS_LED = 2.88
R_2_noPMS_LED = 9.67741935484
R_1_noPMS_noLED = 200
R_2_noPMS_noLED = 680
# set the resistor values in ADC voltage divider
if(PMS):
    if (LED_module):
        R_1 = R_1_PMS_LED
        R_2 = R_2_PMS_LED
    else:
        R_1 = R_1_PMS_noLED
        R_2 = R_2_PMS_noLED
else:
    if (LED_module):
        R_1 = R_1_noPMS_LED
        R_2 = R_2_noPMS_LED
    else:
        R_1 = R_1_noPMS_noLED
        R_2 = R_2_noPMS_noLED

# create voltage divider class
vdiv_bat = vdiv(voltage_divider,voltage_readings,voltage_readings_delay,R_1,R_2)

# ━━━━━━━━━━ 𝗧𝗜𝗠𝗘 𝗦𝗘𝗧/𝗨𝗣𝗗𝗔𝗧𝗘 ━━━━━━━━━━
# create suntime class
solartime = suntime(operation_time,sunrise_hour,sunrise_minute,sunset_hour,sunset_minute)
# initialise RTC object
rtc = pyb.RTC()
# set rtc from user definedc date and time only on power on
if (machine.reset_cause() != machine.DEEPSLEEP_RESET and RTC_select == 'onboard'):
    rtc.datetime(current_date_time)
if(RTC_select == 'ds3231'):
    # import necessary librairies
    from ds3231 import DS3231
    # initialize i2c pins on P7 (SCL) and P8 (SDA) and DS3231 as ext_rtc
    i2c = machine.SoftI2C(sda=pyb.Pin('P8'), scl=pyb.Pin('P7'))
    ext_rtc = DS3231(i2c)
    ext_rtc.get_time(True)
if(RTC_select == 'pcf8563'):
    # import necessary librairies
    from pcf8563 import PCF8563
    # initialize i2c pins on P4 (SCL) and P5 (SDA) and PCF8563 as ext_rtc
    i2c = machine.SoftI2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'))
    ext_rtc = PCF8563(i2c)
    ext_rtc.get_time(True)

# print date and time from set or updated RTC
print("Current date (Y,M,D):",rtc.datetime()[0:3],"and time (H,M,S):",rtc.datetime()[4:7])

# ━━━━━━━━━━ 𝗙𝗜𝗟𝗘𝗦 𝗔𝗡𝗗 𝗙𝗢𝗟𝗗𝗘𝗥𝗦 ━━━━━━━━━━
#import mobilenet model and labels before new directory is created
if (classify_mode != "none"):
    net = net_path
    try:
        labels = [line.rstrip('\n') for line in open(labels_path)]
        print("Loaded model and labels")
        #get target label index
        target_indices = [i for i in range(len(labels)) if labels[i] not in non_target_labels]
        non_target_indices = [i for i in range(len(labels)) if labels[i] in non_target_labels]
        print("Selected target indices:",list(labels[i] for i in target_indices))
    except Exception as e:
        print(e)
        raise Exception('Failed to load "trained.tflite" or "labels.txt", make sure to add these files on the SD card (' + str(e) + ')')

# On wakeup from deep sleep, fetch variables from files
if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
    # retrieve current working folder name in VAR
    with open('/VAR/currentfolder.txt', 'r') as folderfetch:
        current_folder = folderfetch.read()
    # retrieve current picture ID in VAR
    with open('/VAR/picturecount.txt', 'r') as countfetch:
        picture_count = eval(countfetch.read())
    # retrieve current detection ID in VAR
    with open('/VAR/detectioncount.txt', 'r') as countfetch:
        detection_count = eval(countfetch.read())

    # check voltage and save status, if battery too low -> sleep until sunrise
    vbat = vdiv_bat.read_voltage()
    save_status(vbat,"Script start - Waking",current_folder)
    if (vbat!="NA" and vbat<vbat_minimum and not pyb.USB_VCP().isconnected()):
        save_variables(current_folder, picture_count, detection_count)
        save_status(vbat,"Battery low - Sleeping",current_folder)
        indicator_dsleep(solartime.time_until_sunrise()+30*60*1000,active_LED_interval_ms)

# create and initialize new folders only on powerup or soft reset
if (machine.reset_cause() != machine.DEEPSLEEP_RESET and MODE != 0):
    # if VAR folder doesnt exists,create new VAR folder
    if (not "VAR" in os.listdir()):
        os.mkdir('VAR')

    # Listing root contents to search folders
    files_jpegs_folder=os.listdir()
    folders=[files_jpegs_folder for files_jpegs_folder in files_jpegs_folder if "." not in files_jpegs_folder]
    if(len(folders)>0):
        folder_number=len(folders)
    else: folder_number=0
    #incrementing folder number (-1 because VAR folder)
    new_folder_number=int(folder_number)-1

    #create folder for new deployment to avoid overwriting images
    folder_created=False
    folder_time = rtc.datetime()
    while (not folder_created):
        try:
            current_folder=str(new_folder_number)+" "+"-".join(map(str,list(folder_time[i] for i in [0,1,2])))+"_"+"-".join(map(str,list(folder_time[i] for i in [4,5,6])))
            os.mkdir(str(current_folder))
            print("Created new deployment folder: "+str(current_folder))
            folder_created=True
        except:
            #increment by 1 if folder already exists, until it doesn't
            new_folder_number=new_folder_number+1

    # Create detection files
    if(not 'detections.csv' in os.listdir(str(current_folder))):
            with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                detectionlog.write("detection_id" + ',' + "picture_id" + ',' + "blob_pixels" + ',' + "blob_elongation" + ','
          + "blob_corner1_x" + ',' + "blob_corner1_y" + ',' + "blob_corner2_x" + ',' + "blob_corner2_y" + ',' + "blob_corner3_x" + ',' + "blob_corner3_y" + ',' + "blob_corner4_x" + ',' + "blob_corner4_y"
          + ',' + "blob_l_mode" + ',' + "blob_l_min" + ',' + "blob_l_max" + ',' + "blob_a_mode" + ',' + "blob_a_min" + ',' + "blob_a_max" + ',' + "blob_b_mode" + ',' + "blob_b_min" + ',' + "blob_b_max" + ','
          + "image_labels" + ',' "image_confidences" + ',' + "image_x" + ',' + "image_y" + ',' + "image_width" + ',' + "image_height" + '\n')
    if(not 'images.csv' in os.listdir(str(current_folder))):
        with open(str(current_folder)+'/images.csv', 'a') as imagelog:
            imagelog.write("picture_id" + ',' + "date_time" + ',' + "exposure_us" + ',' + "gain_dB" + ',' + "frames_per_second" + ','
            + "image_type" + ',' + "roi_x" + ',' + "roi_y" + ',' + "roi_width" + ',' + "roi_height" + '\n')
    #make jpeg, reference image and ROI directories if needed
    if (not "jpegs" in os.listdir(str(current_folder))): os.mkdir(str(current_folder)+"/jpegs")
    if (fd_enable and not "reference" in os.listdir(str(current_folder)+"/jpegs")): os.mkdir(str(current_folder)+"/jpegs/reference")
    if (export_blobs!="none" and not "blobs" in os.listdir(str(current_folder)+"/jpegs")): os.mkdir(str(current_folder)+"/jpegs/blobs")
    if use_roi:
        for roi_temp in rois:
            if not '_'.join(map(str,roi_temp)) in os.listdir(str(current_folder)+"/jpegs"): os.mkdir(str(current_folder)+"/jpegs/"+'_'.join(map(str,roi_temp)))
            print("Created",'_'.join(map(str,roi_temp)),"subfolder(s)")

    #start counting
    picture_count = 0
    detection_count = 0

    # check voltage and save status, if battery too low -> sleep until sunrise
    vbat = vdiv_bat.read_voltage()
    save_status(vbat,"Script start - Initialising",current_folder)
    if (vbat!="NA" and vbat<vbat_minimum and not pyb.USB_VCP().isconnected()):
        save_variables(current_folder, picture_count, detection_count)
        save_status(vbat,"Battery low - Sleeping",current_folder)
        indicator_dsleep(solartime.time_until_sunrise()+30*60*1000,active_LED_interval_ms)

# ━━━━━━━━━━ 𝗕𝗢𝗔𝗥𝗗 𝗖𝗢𝗡𝗧𝗥𝗢𝗟 ━━━━━━━━━━
# verify that wifi shield is connected when wifi is enabled
if(wifi_enable):
    wifi_enable = wifishield_isconnnected()
# 50kHz pin6 timer2 channel1
light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
# init led status variables
LED_status = False

# ━━━━━━━━━━ 𝗣𝗜𝗖𝗧𝗨𝗥𝗘 𝗩𝗔𝗥𝗜𝗔𝗕𝗟𝗘𝗦 ━━━━━━━━━━
#user setting checks
if (fd_enable and exposure_control=="auto"):
    print("ATTENTION: using automatic exposure with frame differencing can result in spurious triggers!")
#determine exposure values
if (exposure_bracketing):
    exposure_values=exposure_bracketing_values
else:
    exposure_values=[1]
# ━━━━━━━━━━ 𝗦𝗘𝗡𝗦𝗢𝗥 𝗜𝗡𝗜𝗧 ━━━━━━━━━━
#indicate initialisation with LED
LED_WHITE_BLINK(200,3)
#check night time for continuous monitoring
night_time_check = not solartime.is_daytime()
# Reset and initialize the sensor
sensor.reset()
#we need RGB565 for frame differencing and MobileNet
sensor.set_pixformat(sensor_pixformat)
# Set frame size
sensor.set_framesize(sensor_framesize)
#windowing
if (sensor_windowing):
    sensor.set_windowing(windowing_x,windowing_y,windowing_w,windowing_h)
#set number of frame buffers
if sensor_framebuffers_control: sensor.set_framebuffers(sensor_framebuffers)
# Give the camera sensor time to adjust
sensor.skip_frames(time=1000)
# get future image width and height
if (sensor_windowing):
    image_width=windowing_w
    image_height=windowing_h
else:
    image_width=sensor.width()
    image_height=sensor.height()
#parameter validity checks
if (windowing_y+windowing_h>sensor.height()):
    print(windowing_y)
    print(windowing_h)
    print("sensor height:",sensor.height())
    sys.exit("Windowing height exceeds image height!")
if (windowing_x+windowing_w>sensor.width()):
    sys.exit("Windowing width exceeds image width!")

#assign roi to entire image if we do not use them
if(not use_roi and MODE != 0):
    rois = [(0,0,sensor.width(),sensor.height())]
    if not '_'.join(map(str,rois[0])) in os.listdir(str(current_folder)+"/jpegs"): os.mkdir(str(current_folder)+"/jpegs"+"/"+'_'.join(map(str,rois[0])))
    print("Created",'_'.join(map(str,rois[0])),"subfolder")

#adjusting exposure
# at night, turn ON selected illumination LEDs if not always OFF mode
if(LED_mode_night != "off" and night_time_check and LED_status == False):
    print("Turning illumination LEDs ON for exposure adjustment")
    if(LED_select == 'module'):
        print("Warming up LED module for",LED_module_warmup/1000,"seconds.")
        light.pulse_width_percent(LED_module_PWM)
        sensor.skip_frames(time = LED_module_warmup)
    if(LED_select == 'onboard'):
        LED_IR_ON()
    LED_status = True
expose(exposure_control,exposure_bias_day,exposure_bias_night,gain_bias,exposure_ms,gain_dB,night_time_check)

#Frame buffer memory management
if(fd_enable):
    #de-allocate frame buffer just in case
    sensor.dealloc_extra_fb()
    sensor.dealloc_extra_fb()
    # Take from the main frame buffer's RAM to allocate a second frame buffer.
    img_ref_fb = sensor.alloc_extra_fb(image_width, image_height, sensor_pixformat)
    img_ori_fb = sensor.alloc_extra_fb(image_width, image_height, sensor_pixformat)

    print("Saving background image...")
    picture_count += 1
    img_ref_fb.replace(sensor.snapshot())
    picture_time = "-".join(map(str,time.localtime()[0:6]))
    img_ref_fb.save(str(current_folder)+"/jpegs/reference/"+str(picture_count)+"_reference.jpg",quality=jpeg_quality)
    with open(str(current_folder)+'/images.csv', 'a') as imagelog:
                imagelog.write(str(picture_count) + ',' + str(picture_time) + ',' + str(sensor.get_exposure_us()) +
                  ',' + str(sensor.get_gain_db()) + ',' + "NA" + ',' + "reference" + '\n')
    print("Saved background image - now frame differencing!")

# after exposure adjustment, turn OFF selected illumination LEDs if not always ON mode
if (LED_mode_night != "on" and LED_status == True):
    print("Turning illumination LEDs OFF to save power...")
    if(LED_select == 'module'):
        light.pulse_width_percent(0)
        print("Letting LED module cool down for",LED_module_cooldown,"seconds.")
        pyb.delay(LED_module_cooldown)
    if(LED_select == 'onboard'):
        LED_IR_OFF()
    LED_status = False

#start counting time
start_time_status_ms = pyb.millis()
start_time_blending_ms = pyb.millis()
start_time_active_LED_ms = pyb.millis()
#set trigger and detected state
triggered = False
detected = False
#start clock
clock = time.clock()

# ━━━━━━━━━━ 𝗠𝗔𝗜𝗡 𝗟𝗢𝗢𝗣 ━━━━━━━━━━
while(True):

    # go to deep sleep when not operation time
    if(not solartime.is_operation_time()):
        # outside of operation time
        print("Outside operation time - current time:",time.localtime()[0:6])
        # before deep sleep, turn off illumination LEDs if on
        if(LED_status == True):
            print("Turning illumination LEDs OFF before deep sleep")
            LED_IR_OFF()
            light.pulse_width_percent(0)
            LED_status = False
        #deferred analysis of images when scale is too small (not working yet)
        if(minimum_image_scale<threshold_image_scale_defer):
            print("Starting deferred analysis of images before sleeping...")
            deferred_analysis(net,minimum_image_scale,predictions_list,current_folder)

        #compute time until wake-up
        if (operation_time == "day"):
            sleep_time = solartime.time_until_sunrise()
        if (operation_time == "night"):
            sleep_time = solartime.time_until_sunset()
        save_variables(current_folder, picture_count, detection_count)
        save_status(vbat,"Outside operation time - Sleeping",current_folder)
        indicator_dsleep(sleep_time, active_LED_interval_ms)

    # continue script when operation time
    clock.tick()
    # update night time check
    night_time_check = not solartime.is_daytime()

    # turn ON illumination LED at night if always ON
    if(night_time_check and LED_mode_night == "on" and LED_status == False):
        print("Turning illumination LEDs ON during nighttime")
        if(LED_select == 'module'):
            print("Warming up LED module for",LED_module_warmup/1000,"seconds.")
            light.pulse_width_percent(LED_module_PWM)
            sensor.skip_frames(time = LED_module_warmup)
        if(LED_select == 'onboard'):
            LED_IR_ON()
        LED_status = True
    # turn OFF illumination LED at daytime
    if(not night_time_check and LED_status == True):
        print("Turning illumination LEDs OFF during daytime")
        if(LED_select == 'module'):
            light.pulse_width_percent(0)
            print("Letting LED module cool down for",LED_module_cooldown,"seconds.")
            pyb.delay(LED_module_cooldown)
        if(LED_select == 'onboard'):
            LED_IR_OFF()
        LED_status = False

    #log status and battery voltage (if possible) every period
    if (pyb.elapsed_millis(start_time_status_ms) > status_logging_period_ms):
        start_time_status_ms = pyb.millis()
        #  update internal RTC from external RTC
        if(RTC_select != 'onboard'): ext_rtc.get_time(True)
        print("Updated time (Y,M,D):",rtc.datetime()[0:3],"and time (H,M,S):",rtc.datetime()[4:7])
        # turn on OFF LED module during voltage reading
        if(LED_status == True):
            print("Turning illumination LEDs OFF during voltage reading")
            if(LED_select == 'module'):
                light.pulse_width_percent(0)
                print("Letting LED module cool down for",LED_module_cooldown,"seconds.")
                pyb.delay(LED_module_cooldown)
            if(LED_select == 'onboard'):
                LED_IR_OFF()
            LED_status = False
        # check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        if (vbat!="NA" and vbat<vbat_minimum and not pyb.USB_VCP().isconnected()):
            save_variables(current_folder, picture_count, detection_count)
            save_status(vbat,"Battery low - Sleeping",current_folder)
            indicator_dsleep(solartime.time_until_sunrise()+30*60*1000,active_LED_interval_ms)
        save_status(vbat,"Script running - Normal operation",current_folder)
        # at night, turn ON selected illumination LEDs if always ON mode
        if(LED_mode_night == "on" and night_time_check and LED_status == False):
            print("Turning illumination LEDs ON after voltage reading")
            if(LED_select == 'module'):
                print("Warming up LED module for",LED_module_warmup/1000,"seconds.")
                light.pulse_width_percent(LED_module_PWM)
                sensor.skip_frames(time = LED_module_warmup)
            if(LED_select == 'onboard'):
                LED_IR_ON()
            LED_status = True

    #blink LED every period
    if (pyb.elapsed_millis(start_time_active_LED_ms) > active_LED_interval_ms):
        start_time_active_LED_ms = pyb.millis()
        print("Blinking LED indicator after",str(active_LED_interval_ms/1000),"seconds")
        LED_BLUE_BLINK(active_LED_duration_ms)

    #auto-adjust exposure with user biases or gain, blend frame if frame differencing and no detection
    #wait up to twice expose period
    if (exposure_control!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > expose_period_s*1000) and (not triggered or not fd_enable)
    or (exposure_control!="auto" and (pyb.elapsed_millis(start_time_blending_ms) > 2*expose_period_s*1000))):
        # at night, turn ON selected illumination LEDs if not always OFF mode
        if(LED_mode_night != "off" and night_time_check and LED_status == False):
            print("Turning illumination LEDs ON for exposure adjustment")
            if(LED_select == 'module'):
                print("Warming up LED module for",LED_module_warmup/1000,"seconds.")
                light.pulse_width_percent(LED_module_PWM)
                sensor.skip_frames(time = LED_module_warmup)
            if(LED_select == 'onboard'):
                LED_IR_ON()
            LED_status = True
        expose(exposure_control,exposure_bias_day,exposure_bias_night,gain_bias,exposure_ms,gain_dB,night_time_check)
        #blend new frame only if frame differencing
        if (fd_enable):
            print("Blending new frame, saving background image after",str(round(pyb.elapsed_millis(start_time_blending_ms)/1000)),"seconds")
            #take new picture
            picture_count += 1
            img = sensor.snapshot()
            picture_time = "-".join(map(str,time.localtime()[0:6]))
            # Blend in new frame. We're doing 256-alpha here because we want to
            # blend the new frame into the background. Not the background into the
            # new frame which would be just alpha. Blend replaces each pixel by
            # ((NEW*(alpha))+(OLD*(256-alpha)))/256. So, a low alpha results in
            # low blending of the new image while a high alpha results in high
            # blending of the new image. We need to reverse that for this update.
            #blend with frame that is in buffer
            if indicators: LED_CYAN_ON()
            img_ori_fb.blend(img_ref_fb, alpha=(256-background_blend_level))
            img_ref_fb.replace(img_ori_fb)
            img_ref_fb.save(str(current_folder)+"/jpegs/reference/"+str(picture_count)+"_reference.jpg",quality=jpeg_quality)
            with open(str(current_folder)+'/images.csv', 'a') as imagelog:
                imagelog.write(str(picture_count) + ',' + str(picture_time) + ',' + str(sensor.get_exposure_us()) +
                  ',' + str(sensor.get_gain_db()) + ',' + str(clock.fps()) + ',' + "reference" + '\n')
            if indicators: LED_CYAN_OFF()
        #reset blending time counter
        start_time_blending_ms = pyb.millis()

        # after exposure adjustment, turn OFF selected illumination LEDs if not always ON mode
        if (LED_mode_night != "on" and LED_status == True):
            print("Turning illumination LEDs OFF to save power...")
            if(LED_select == 'module'):
                light.pulse_width_percent(0)
                print("Letting LED module cool down for",LED_module_cooldown,"seconds.")
                pyb.delay(LED_module_cooldown)
            if(LED_select == 'onboard'):
                LED_IR_OFF()
            LED_status = False

    # TAKING PICTURE
    #current image parameters
    current_exposure=sensor.get_exposure_us()
    current_gain=sensor.get_gain_db()
    #loop over exposure values
    for b in exposure_values:
        if (exposure_bracketing):
            #fix the gain so image is stable
            sensor.set_auto_gain(False, gain_db = current_gain)
            print("Exposure bracketing bias:",b)
            sensor.set_auto_exposure(False, \
                exposure_us = int(current_exposure*b))
            #wait for new exposure time to be applied
            sensor.skip_frames(time = 2000)
        # at night, turn ON selected illumination LEDs if not always OFF mode
        if(LED_mode_night != "off" and night_time_check and LED_status == False):
            print("Turning illumination LEDs ON for taking the picture")
            if(LED_select == 'module'):
                print("Warming up LED module for",LED_module_warmup/1000,"seconds.")
                light.pulse_width_percent(LED_module_PWM)
                sensor.skip_frames(time = LED_module_warmup)
            if(LED_select == 'onboard'):
                LED_IR_ON()
            LED_status = True

        img = sensor.snapshot()

        # after picture, turn OFF selected illumination LEDs if not always ON mode
        if (LED_mode_night != "on" and LED_status == True):
            print("Turning illumination LEDs OFF to save power...")
            if(LED_select == 'module'):
                light.pulse_width_percent(0)
                print("Letting LED module cool down for",LED_module_cooldown,"seconds.")
                pyb.delay(LED_module_cooldown)
            if(LED_select == 'onboard'):
                LED_IR_OFF()
            LED_status = False

        #log time
        picture_time = "-".join(map(str,time.localtime()[0:6]))
        #start cycling over ROIs
        for roi_temp in rois:
            if (use_roi):
                print("Extracting ROI:",roi_temp)
                img_roi=img.copy(roi=roi_temp,copy_to_fb=True)
            else: img_roi=img

            if(fd_enable):
                #save original image
                img_ori_fb.replace(img_roi)

                #compute absolute frame difference
                img_roi.difference(img_ref_fb)
                #set trigger
                triggered = False

                try:
                    blobs = img_roi.find_blobs(color_thresholds,invert = True, merge = False, pixels_threshold = minimum_blob_pixels)
                    #filter blobs with maximum pixels condition
                    blobs_filt = [item for item in blobs if item[4]<maximum_blob_pixels]

                    if (len(blobs_filt)>0):
                        print(len(blobs_filt),"blob(s) within range!")
                        triggered = True
                        picture_count += 1
                    for blob in blobs_filt:
                        detection_count += 1
                        color_statistics_temp = img.get_statistics(roi = blob.rect(),thresholds = color_thresholds)
                        #optional marking of blobs
                        if (indicators):
                            img.draw_edges(blob.corners(), color=(0,0,255), thickness=5)
                            img.draw_rectangle(blob.rect(), color=(255,0,0), thickness=5)
                        #log each detected blob
                        with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                            detectionlog.write(str(detection_count) + ',' + str(picture_count) + ',' + str(blob.pixels()) + ',' + str(blob.elongation()) +
                                ',' + str(blob.corners()[0][0]) + ',' + str(blob.corners()[0][1]) +
                                ',' + str(blob.corners()[1][0]) + ',' + str(blob.corners()[1][1]) +
                                ',' + str(blob.corners()[2][0]) + ',' + str(blob.corners()[2][1]) +
                                ',' + str(blob.corners()[3][0]) + ',' + str(blob.corners()[3][1]) +
                                ',' + str(color_statistics_temp.l_mode()) + ',' + str(color_statistics_temp.l_min()) + ',' + str(color_statistics_temp.l_max()) +
                                ',' + str(color_statistics_temp.a_mode()) + ',' + str(color_statistics_temp.a_min()) + ',' + str(color_statistics_temp.a_max()) +
                                ',' + str(color_statistics_temp.b_mode()) + ',' + str(color_statistics_temp.b_min()) + ',' + str(color_statistics_temp.b_max()))
                        if (classify_mode == "blobs" or export_blobs!="none"):
                            #set blob bounding box according to user parameters
                            if (export_blobs=="rectangle"):
                                blob_rect=blob.rect()
                            elif (export_blobs=="square"):
                                #get longest side of blob's bounding rectangle
                                if (blob.w()>=blob.h()):
                                    blob_h=blob.w()
                                else: blob_h=blob.h()
                                if (blob.h()>blob.w()):
                                    blob_w=blob.h()
                                else: blob_w=blob.w()
                                if (blob_h>image_height):
                                    if indicators: print("Cannot export blob bounding square as its height would exceed the image height! Using image height instead.")
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
                                if (indicators):
                                    img.draw_rectangle(blob_rect, color=(0,255,0), thickness=10)
                            #extract blob
                            img_blob=img_ori_fb.copy(roi=blob_rect,copy_to_fb=True)
                            #saving extracted blob rectangles/squares
                            if (export_blobs!="none"):
                                #optional: turn on LED while saving blob bounding boxes
                                if (indicators):
                                    LED_GREEN_ON()
                                print("Exporting blob bounding",export_blobs,"...")
                                img_blob.save(str(current_folder)+"/jpegs/blobs/" + str(picture_count) + "_d" + str(detection_count) + "_xywh" + str("_".join(map(str,blob_rect))) + ".jpg",quality=jpeg_quality)
                                if indicators: LED_GREEN_OFF()
                            if (classify_mode == "blobs"):
                                #optional: turn on LED while classifying
                                if indicators: LED_YELLOW_ON()
                                #rescale blob rectangle
                                img_blob_resized=img_blob.copy(x_size=model_resolution,y_size=model_resolution,copy_to_fb=True,hint=image.BICUBIC)
                                # we do not need a loop since we do not analyse blob subsets
                                obj = tf.classify(net,img_blob_resized)[0]
                                predictions_list = list(zip(labels, obj.output()))
                                print("Predictions for classified blob:",predictions_list)
                                with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                                    detectionlog.write(',' + str(";".join(map(str,labels))) + ',' + str(";".join(map(str,obj.output()))) + ',' + str(blob.rect()[0]) + ',' + str(blob.rect()[1]) + ',' + str(blob.rect()[2]) + ',' + str(blob.rect()[3]) + '\n')
                                if indicators: LED_YELLOW_OFF()
                            #we finish the CSV line here if not classifying
                            else:
                                with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                                    detectionlog.write('\n')
                        #if we only log blobs, we finish the CSV line here
                        else:
                            with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                                detectionlog.write('\n')
                        #go to next loop if only first blob is needed
                        if (blob_action == "stop"):
                            break
                except MemoryError:
                    #when there is a memory error, we assume that it is triggered because of many blobs
                    triggered = True
                    picture_count += 1
                    save_status("-","memory error",current_folder)
            #if frame differencing is disabled, every image is considered triggered and counted outside live view mode
            elif (MODE != 0):
                triggered = True
                picture_count += 1
            #log roi image data, possibly classify and save image
            if(triggered):
                #save image log
                if (MODE != 0):
                    with open(str(current_folder)+'/images.csv', 'a') as imagelog:
                        imagelog.write(str(picture_count) + ',' + str(picture_time) + ',' + str(sensor.get_exposure_us()) +
                          ',' + str(sensor.get_gain_db()) + ',' + str(clock.fps()) + ',' + "")
                        if (use_roi):
                            imagelog.write(',' + str(roi_temp[0]) + ',' + str(roi_temp[1]) + ',' + str(roi_temp[2]) + ',' + str(roi_temp[3]) + '\n')
                        else:
                            imagelog.write('\n')
                # init detection confidence variable
                detection_confidence = 0
                #classify image
                if(classify_mode=="image"):
                    if indicators: LED_YELLOW_ON()
                    print("Running image classification on ROI...")
                    detected = False
                    #revert image_roi replacement to get original image for classification
                    if fd_enable: img_roi.replace(img_ori_fb)
                    #only analyse when classification is feasible within reasonable time frame
                    if (minimum_image_scale>=threshold_image_scale_defer):
                        print("Classifying ROI or image...")
                        #rescale image to get better model results
                        img_net=img_roi.copy(x_size=model_resolution,y_size=model_resolution,copy_to_fb=True,hint=image.BICUBIC)
                        #start image classification
                        for obj in tf.classify(net, img_roi, min_scale=minimum_image_scale, scale_mul=0.5, x_overlap=0.5, y_overlap=0.5):
                            #initialise threshold check
                            threshold_exceeded =  False
                            #put predictions in readable format
                            predictions_list = list(zip(labels, obj.output()))
                            print("Predictions at [x=%d,y=%d,w=%d,h=%d]" % obj.rect(),":")
                            #check threshold for each target item
                            for i in range(len(predictions_list)):
                                print("%s = %f" % (predictions_list[i][0], predictions_list[i][1]))
                                if (i == non_target_indices): continue
                                if (predictions_list[i][1] > threshold_confidence):
                                        threshold_exceeded =  True
                            #log model scores if any target is above threshold
                            if(threshold_exceeded):
                                detected = True
                                detection_count +=1
                                print("Detected target! Logging detection...")
                                #logging detection
                                with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                                    detectionlog.write(str(detection_count) + ',' + str(picture_count) + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' +
                                    "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' +
                                    str(";".join(map(str,labels))) + ',' + str(";".join(map(str,obj.output()))) + ',' + str(roi_temp[0]) + ',' + str(roi_temp[1]) + ',' + str(roi_temp[2]) + ',' + str(roi_temp[3]) + '\n')
                    if indicators: LED_YELLOW_OFF()
                #object detection. not compatible with ROI mode
                if(classify_mode=="objects" and not use_roi):
                    if indicators: LED_YELLOW_ON()
                    print("Running object detection on ROI...")
                    detected = False
                    #revert image_roi replacement to get original image for classification
                    if fd_enable: img_roi.replace(img_ori_fb)
                    #loop through labels
                    for i, detection_list in enumerate(tf.detect(net,img_roi, thresholds=[(math.ceil(threshold_confidence * 255), 255)])):
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
                            if (indicators):
                                img.draw_rectangle(d.rect(), color=colors[i+1], thickness=2)
                            with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                                detectionlog.write(str(detection_count) + ',' + str(picture_count) + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' +
                                "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' + "NA" + ',' +
                                str(labels[i]) + ',' + str(d[4]) + ',' + str(d[0]) + ',' + str(d[1]) + ',' + str(d[2]) + ',' + str(d[3]) + '\n')
                    if indicators: LED_YELLOW_OFF()
                elif(classify_mode=="objects" and use_roi): print("Object detection skipped, as it is not compatible with using ROIs!")

                # saving picture
                if(save_roi == "all" or save_roi == "trigger" or (save_roi == "detect" and detected)):
                    print("Saving ROI or whole image...")
                    if indicators: LED_GREEN_ON()
                    #revert image_roi replacement to get original image for classification
                    if (fd_enable): img_roi.replace(img_ori_fb)
                    # Save picture with detection ID
                    img_roi.save(str(current_folder)+"/jpegs/"+ str('_'.join(map(str,roi_temp))) + "/" + str(picture_count) + ".jpg",quality=jpeg_quality)
                    if indicators: LED_GREEN_OFF()
                # copy and save compressed image to send it over wifi later
                if(wifi_enable and send_image and detection_confidence >= threshold_image):
                    print("Original image size :", img.size()/1024,"kB")
                    cp_img = img.copy(x_scale=0.1,y_scale=0.1,copy_to_fb=True,hint=image.BICUBIC)
                    print("Size of image for WiFi transfer :", cp_img.size()/1024,"kB")
                    cp_img.save("cp_img.jpg",quality=jpeg_quality)
            print("Frames per second: %s" % str(round(clock.fps(),1)),", Gain (dB): %s" % str(round(sensor.get_gain_db())),", Exposure time (ms): %s" % str(round(sensor.get_exposure_us()/1000)),"\n*****")
    #turn auto image adjustments back on if bracketing
    if (exposure_bracketing):
        if(exposure_control=="auto"):
            #auto gain and exposure
            sensor.set_auto_gain(True)
            sensor.set_auto_exposure(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(exposure_control=="exposure"):
            #auto gain
            sensor.set_auto_gain(True)
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)
        elif(exposure_control=="bias"):
            if night_time_check: exposure_bias=exposure_bias_night
            else: exposure_bias=exposure_bias_day
            # re-set exposure
            sensor.set_auto_exposure(False, \
                exposure_us = int(current_exposure))
            #wait for auto-adjustment
            sensor.skip_frames(time = 2000)

    # send detection data over wifi
    if(wifi_enable and detected):
        # conect to WiFi, this migth take while depending on the signal strength
        print("Detection confidence ", detection_confidence*100,"%")
        wifi_connected = wifi_connect(wifi_ssid,wifi_key)
        if(wifi_connected):
            # send confidence level to server
            if(send_confidence):
                data_transfer(wifi_data_url, detection_confidence)
            if(send_image and detection_confidence >= threshold_image):
                detection_image = open("cp_img.jpg", "rb")
                image_transfer(wifi_img_url, detection_image)
            # discponnect from wifi asap to save energy
            wifi_disconnect()

    #if indicators: print("Frame buffers:",sensor.get_framebuffers())
    #delay loop execution to control frame rate
    if (delay_loop_s > 0 and delay_loop_s < delay_threshold_sleep_s):
        print("Delaying frame capture for",delay_loop_s,"seconds...")
        pyb.delay(delay_loop_s*1000)

    if (delay_loop_s > delay_threshold_sleep_s):
        # before deep sleep, turn off illumination LEDs if on
        if(LED_status == True):
            print("Turning illumination LEDs OFF before deep sleep")
            LED_IR_OFF()
            light.pulse_width_percent(0)
            LED_status = False
        # save variables and log status before going ot sleep
        save_variables(current_folder, picture_count, detection_count)
        save_status(vbat,"Delay loop - Sleeping",current_folder)
        # go to sleep until next picture with blinking indicator
        indicator_dsleep(delay_loop_s*1000,active_LED_interval_ms)

        # (when light sleep is used) check voltage and save status, if battery too low -> sleep until sunrise
        vbat = vdiv_bat.read_voltage()
        if (vbat!="NA" and vbat<vbat_minimum):
            save_variables(current_folder, picture_count, detection_count)
            save_status(vbat,"Battery low - Sleeping",current_folder)
            indicator_dsleep(solartime.time_until_sunrise()+30*60*1000,active_LED_interval_ms)
        save_status(vbat,"Delay loop - waking",current_folder)
