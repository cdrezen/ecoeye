# Functions for EcoNect
# import libraries
import machine, pyb, time, network, sensor, os, requests, math
from pyb import Pin, Timer, ExtInt
# import library for interrupt and allocate buffer memory
import micropython
from hardware.led import *
##----- Function description -----#
## Reset and initialize the sensor
##----- Input arguments -----#
## sensor_framesize - resolution for the camera sensor
## sensor_pixformat - pixel format for the camera module
## sensor_windowing -
## sensor_framebuffers_control -
##----- Output variables -----#
## image_width, image_height
#def ecotime(RTC_select):
    #if (RTC_select == 'onboard'):
        #now = pyb.RTC().datetime()
        #return_time = (now[0],now[1],now[2],now[3],now[4],now[5],1,0)
    #if (RTC_select == 'ds3231'):
        #return_time = DS3231(machine.SoftI2C(sda=pyb.Pin('P8'), scl=pyb.Pin('P7'))).get_time()
    #if (RTC_select == 'pcf8563'):
        #from pcf8563 import PCF8563
        #return_time = PCF8563(machine.SoftI2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'))).get_time()
    #return return_time

# ━━━━━━━━━━ 𝗖𝗔𝗠𝗘𝗥𝗔 𝗦𝗘𝗡𝗦𝗢𝗥 ━━━━━━━━━━
# ⚊⚊⚊⚊⚊ sensor inititlisation ⚊⚊⚊⚊⚊
# Reset and initialize the sensor
# --- Input arguments ---
# sensor_framesize - resolution for the camera sensor
# sensor_pixformat - pixel format for the camera module
# sensor_windowing -
# sensor_framebuffers_control :
# --- Output variables ---
# image_width, image_height
def sensor_init(sensor_framesize=sensor.QVGA,sensor_pixformat=sensor.RGB565,sensor_windowing=False,sensor_framebuffers_control=False):
    sensor.reset()
    #we need RGB565 for frame differencing and mobilenet
    sensor.set_pixformat(sensor_pixformat)
    # Set frame size
    sensor.set_framesize(sensor_framesize)
    #windowing
    #rect tuples (x,y coordinates and width and height) for digital zoom
    #x=0,y=0 is conventionally the upper left corner
    windowing_x = 324
    windowing_y = 0
    windowing_w = 1944
    windowing_h = 1944
    if (sensor_windowing):
        sensor.set_windowing(windowing_x,windowing_y,windowing_w,windowing_h)
    #set number of frame buffers
    sensor_framebuffers = 1
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
    # return image width and height
    return image_width, image_height

# ⚊⚊⚊⚊⚊ Adjust exposure ⚊⚊⚊⚊⚊
# Adjust exposure
# --- Input arguments ---
# control - exposure control mode. Options: auto/bias/exposure/manual
# exposure_bias_day - automatic exposure time multiplicator at day
# exposure_bias_night - automatic exposure time multiplicator at night
# gain_bias - automatic exposure time multiplicator
# exposure_ms - manual exposure mode
# gain_dB - manual gain mode
# night_time_check - night time boolean
# LED_select - whether module or onboard LEDs are used
# LED_mode_night - LED mode : always on, always off or blink
# LED_module_warmup - LED startup time
# LED_module_PWM - brightness of the LEDs
# --- Output variables ----
# none
def expose(exposure_control,exposure_bias_day,exposure_bias_night,gain_bias,exposure_ms,gain_dB,night_time_check):
    print("Adjustment of exposure in",exposure_control,"mode...")

    if(exposure_control=="manual"):
        sensor.set_auto_exposure(False, exposure_us = exposure_ms*1000)
        sensor.set_auto_gain(False, gain_db = gain_dB)
        #wait for new exposure time to be applied (is it necessary?)
        sensor.skip_frames(time = 2000)
    elif(exposure_control=="exposure"):
        #enable auto exposure and gain
        sensor.set_auto_gain(True)
        sensor.set_auto_exposure(False, exposure_us = exposure_ms*1000)
        #wait for auto gain
        sensor.skip_frames(time = 2000)
        #fix the gain so image is stable for frame differencing
        sensor.set_auto_gain(False, gain_db = sensor.get_gain_db())
    elif(exposure_control=="bias"):
        if night_time_check: exposure_bias=exposure_bias_night
        else: exposure_bias=exposure_bias_day
        #enable auto exposure and gain
        sensor.set_auto_exposure(True)
        sensor.set_auto_gain(True)
        #wait for auto settings to kick in
        sensor.skip_frames(time = 2000)
            #apply bias
        sensor.set_auto_exposure(False, \
            exposure_us = int(sensor.get_exposure_us() * exposure_bias))
        sensor.set_auto_gain(False, \
            gain_db = sensor.get_gain_db() * gain_bias)
        #wait for bias to be applied
        sensor.skip_frames(time = 2000)
        # TODO:possibly turn off LEDs here if it works with subsequent fd function and image capture
    return

# ━━━━━━━━━━ 𝗜𝗠𝗔𝗚𝗘 𝗔𝗡𝗔𝗟𝗬𝗦𝗜𝗦 ━━━━━━━━━━
# ⚊⚊⚊⚊⚊ Deferred analysis ⚊⚊⚊⚊⚊
# deferred analysis of images when scale is too small (not working yet)
# --- Input arguments ---
# net
# minimum_image_scale
# predictions_list
# --- Output variables ---
# none
def deferred_analysis(net,minimum_image_scale,predictions_list):
    print("Starting deferred analysis of images before sleeping...")
    #scan jpegs on card
    os.sync()
    sensor.dealloc_extra_fb()
    sensor.dealloc_extra_fb()
    print("current working dir:",os.getcwd())
    files=os.listdir("jpegs")
    jpegs=[files for files in files if "jpg" in files]
    print(jpegs)
    #open and classify each jpeg
    for jpeg in jpegs:
        print("Loading:",jpeg)
        img=image.Image("jpegs/picture_1.jpg",copy_to_fb=True)
        #convert to proper format
        img.to_rgb565()
        #img=image.Image("/jpegs/picture_1.jpg"+jpeg,copy_to_fb=True)
        print("LED on: classifying image", jpeg, "with tensorflow lite...")
        for obj in tf.classify(net, img, min_scale=minimum_image_scale, scale_mul=0.5, x_overlap=0.5, y_overlap=0.5):
            with open('detections.csv', 'a') as detectionlog:
                detectionlog.write(str(jpeg) + ',' + str(predictions_list[1][0]) + ',' + str(predictions_list[1][1]) + ',' + str(obj.rect()[0]) + ',' + str(obj.rect()[1]) + ',' + str(obj.rect()[2]) + ',' + str(obj.rect()[3]) + ',' + str(predictions_list[0][0]) + ',' + str(predictions_list[0][1]) + '\n')
    return

# ━━━━━━━━━━ 𝗟𝗢𝗪 𝗣𝗢𝗪𝗘𝗥 𝗦𝗟𝗘𝗘𝗣 ━━━━━━━━━━
# ⚊⚊⚊⚊⚊ light sleep ⚊⚊⚊⚊⚊
# go to light sleep, resumes script upon wakeup
# --- Indicators ---
# RED 1000ms when going to sleep
# BLUE 1000ms when waking up
# --- Input arguments ---
# sleep_time - time until wakeup
# --- Output variables ---
# none
def light_sleep(sleep_time):
    print("Going to light sleep for ", sleep_time/60000," minutes")
    # indicate light sleep with RED LED
    LED_RED_BLINK(500,1)
    # define sleep time and go
    pyb.RTC().wakeup(math.ceil(sleep_time))
    pyb.stop()
    # wake up
    pyb.RTC().wakeup(None)
    # indicate awakening with BLUE LED
    LED_BLUE_BLINK(500,1)
    return

# ⚊⚊⚊⚊⚊ light sleep with indicator ⚊⚊⚊⚊⚊
# go to light sleep, resumes script upon wakeup
# --- Indicators ---
# RED 1000ms when going to sleep
# BLUE active_LED_duration_ms every active_LED_interval_ms
# BLUE 1000ms when waking up
# --- Input arguments ---
# sleep_time - time until wakeup in ms
# active_LED_interval_ms - time between indicator signal in ms
# active_LED_duration_ms - time indicator is on in ms
# --- Output variables ---
# none
def indicator_sleep(sleep_time,active_LED_interval_ms,active_LED_duration_ms):
    print("Going to light sleep for ", sleep_time/60000," minutes")
    # indicate light sleep with RED LED
    LED_RED_BLINK(500,1)
    for i in range(math.ceil(sleep_time/(active_LED_interval_ms+active_LED_duration_ms))):
        # define sleep time and go
        pyb.RTC().wakeup(math.floor(active_LED_interval_ms))
        pyb.stop()
        # wake up
        pyb.RTC().wakeup(None)
        LED_BLUE_BLINK(active_LED_duration_ms,1)
    # indicate awakening with BLUE LED
    LED_BLUE_BLINK(500,1)
    return

# ⚊⚊⚊⚊⚊ deep sleep ⚊⚊⚊⚊⚊
# go to deep sleep, resets script upon wakeup
# wakeup time is computed before sleep and fetched
# upon wakeup to retrieve time and date
# --- Indicators ---
# RED blink 500ms when going to sleep
# --- Input arguments ---
# sleep_time - time until wakeup
# --- Output variables ---
# none
def deep_sleep(sleep_time):
    print("Going to deep sleep for ", sleep_time/60000," minutes")
    # indicate deep sleep with blinking RED LED
    LED_RED_BLINK(200,2)
    # compute deep sleep end time in epoch seconds
    dsleep_wakeup_epoch = time.mktime(time.localtime()) + math.floor(sleep_time/1000)
    # create deep sleep wakeup file and write epoch seconds as string
    with open('/sdcard/VAR/dsleepwakeup.txt', 'w') as timelog:
        timelog.write(str(dsleep_wakeup_epoch))
    # define sleep time and go to sleep
    pyb.RTC().wakeup(math.floor(sleep_time/1000)*1000)
    # put camera into sleep and shut it down
    sensor.sleep(True)
    sensor.shutdown(True)
    pyb.standby()
    # camera is init on wakeup
    return

# ⚊⚊⚊⚊⚊ deep sleep with indicator ⚊⚊⚊⚊⚊
# go to deep sleep, resets script upon wakeup
# wakeup time is computed before sleep and fetched
# upon wakeup to retrieve time and date
# --- Indicators ---
# RED blink 500ms when going to sleep
# BLUE active_LED_duration_ms every active_LED_interval_ms
# --- Input arguments ---
# sleep_time - time until wakeup in ms
# active_LED_interval_ms - time between indicator signal in ms
# --- Output variables ---
# none
def indicator_dsleep(sleep_time):
    # create deep sleep end time file on the initial sleep time call of tthis function
    if(sleep_time > 0):
        # print and blink deep sleep time
        print("Going to deep sleep for ", sleep_time/60000," minutes")
        LED_RED_BLINK(200,2)
        # compute deep sleep end time in epoch seconds
        dsleep_end_epoch = time.mktime(time.localtime()) + math.floor(sleep_time/1000)
        # create deep sleep end file and write epoch seconds as string
        with open('/sdcard/VAR/dsleepend.txt', 'w') as timelog:
            timelog.write(str(dsleep_end_epoch))
    else:
        # get wakeup time from file
        with open('/sdcard/VAR/dsleepend.txt', 'r') as timefetch:
            dsleep_end_epoch = eval(timefetch.read())

    # compute deep sleep interval wakeup time in epoch seconds
    dsleep_wakeup_epoch = time.mktime(time.localtime()) + math.floor(cfg.DEEPSLEEP_DEFAULT_DURATUION_MS/1000)
    # make sure sleep doesnt surpass the sleep end time
    if(dsleep_wakeup_epoch > dsleep_end_epoch):
        nap_time = (dsleep_end_epoch - time.mktime(time.localtime()))*1000
        dsleep_wakeup_epoch = dsleep_end_epoch
    else:
        nap_time = cfg.DEEPSLEEP_DEFAULT_DURATUION_MS

    # create deep sleep wakeup file and write deep sleep wakeup epoch
    with open('/sdcard/VAR/dsleepwakeup.txt', 'w') as timelog:
        timelog.write(str(dsleep_wakeup_epoch))
    # define sleep time and go
    pyb.RTC().wakeup(math.floor(nap_time/1000)*1000)
    # put camera into sleep and shut it down
    sensor.sleep(True)
    sensor.shutdown(True)
    pyb.standby()
    # camera is init on wakeup
    return

# ⚊⚊⚊⚊⚊ script start check ⚊⚊⚊⚊⚊
# for deep sleep script start
# --- Input arguments ---
# none
# --- Output variables ---
# none
def start_check():
    # get the board reset cause
    if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
        print("Starting script from DEEP SLEEP")
        # get wakeup time from file
        with open('/sdcard/VAR/dsleepwakeup.txt', 'r') as timefetch:
            dsleep_wakeup_epoch = eval(timefetch.read())
        # check if woke up from indicator sleep, i.e. if dsleepend file exists
        if('dsleepend.txt' in os.listdir('VAR')):
            with open('/sdcard/VAR/dsleepend.txt', 'r') as timefetch:
                dsleep_end_epoch = eval(timefetch.read())

        # epoch seconds to time tuple to rtc tuple
        dsleep_wakeup_time = time.localtime(dsleep_wakeup_epoch)
        dsleep_wakeup_rtc = (dsleep_wakeup_time[0], dsleep_wakeup_time[1], dsleep_wakeup_time[2], 1, dsleep_wakeup_time[3], dsleep_wakeup_time[4], dsleep_wakeup_time[5], 0)
        # initialise and update RTC
        pyb.RTC().datetime(dsleep_wakeup_rtc)

        # check if end time has not been reached
        if(dsleep_wakeup_epoch < dsleep_end_epoch):
            # indicator LED : the white firmware is used as the indicator now
            #LED_BLUE_BLINK(500,1)
            # sleep time is zero for interval sleep, indicator is 60s hardcoded
            indicator_dsleep(0)
    else:
        print("Starting script from POWER ON")
    return

# ━━━━━━━━━━ 𝗪𝗜𝗙𝗜 𝗙𝗨𝗡𝗖𝗧𝗜𝗢𝗡𝗦 ━━━━━━━━━━
# ⚊⚊⚊⚊⚊ wifi shield check ⚊⚊⚊⚊⚊
# check if wifi shield is connected
# --- Input arguments ---
# none
# --- Output variables ---
# wifishield - wifi shield is connected boolean
def wifishield_isconnnected():
    wlan = None
    try:
        wlan = network.WINC()
    except OSError:
        pass

    #checking object content
    if wlan:
        print("WiFi shield installed")
        wifishield = True
    else:
        print("No WiFi shield installed")
        wifishield = False
    # reset ADC pin P6
    Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
    return wifishield

# ⚊⚊⚊⚊⚊ connect to wifi ⚊⚊⚊⚊⚊
# connect to WiFi
# --- Indicators ---
# CYAN while trying to connect to WiFi
# BLUE while connected to WiFi
# CYAN blink 100ms when connection failed
# --- Input arguments ---
# ssid - WiFi name
# key - WiFi password
# --- Output variables ---
# wifi_connected - wifi is connected boolean
def wifi_connect(ssid,key):
    # create a winc driver object and connect to WiFi shield
    wlan = network.WINC()
    print("Connecting to WiFi")
    # LED cyan color while connecting to wifi
    LED_CYAN_ON()
    # connect to WiFi, timeout is hardcoded to 2 seconds
    wlan.connect(ssid, key, security=wlan.WPA_PSK)
    if (wlan.isconnected()):
        wifi_connected = True
        print("Succesfully connected to WiFi")
        # LED blue color while connected to wifi
        LED_CYAN_OFF()
        LED_BLUE_ON()
        # print the IP adresses and Signal strength
        print(wlan.ifconfig())
    else:
        wifi_connected = False
        print("WiFi Connection failed")
        LED_CYAN_BLINK(100,2)
    return wifi_connected

# ⚊⚊⚊⚊⚊ Function description ⚊⚊⚊⚊⚊
# disconnect from WiFi
# --- Input arguments ---
# none
# --- Indicators ---
# BLUE turns off
# --- Output variables ---
# none
def wifi_disconnect():
    network.WINC().disconnect()
    print("Disconnected from WiFi")
    LED_BLUE_OFF()
    # reset ADC pin P6
    Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
    return

# ⚊⚊⚊⚊⚊ send data over wifi ⚊⚊⚊⚊⚊
# transfer json data to server
# --- Indicators ---
# BLUE blink when data was sent
# RED blink when data sending failed
# --- Input arguments ---
# url - server upload link, with API if necessary
# data1 - data for first field
# data2 - optional, data for second field
# data3 - optional, data for third field
# data4 - optional, data for fourth field
# --- Output variables ---
# data_transferred - data was transferred boolean
def data_transfer(url, data1, data2=None, data3=None, data4=None):
    headers = {'Content-Type': 'application/json'}
    if (data2 is None and data3 is None and data4 is None):
        data = {'field1':str(data1)}
    elif (data3 is None and data4 is None):
        data = {'field1':str(data1),'field2':str(data2)}
    elif (data4 is None):
        data = {'field1':str(data1),'field2':str(data2),'field3':str(data3)}
    else:
        data = {'field1':str(data1),'field2':str(data2),'field3':str(data3),'field4':str(data4)}

    print("Sending data to server")
    try:
        request_data = requests.post(url, json=data, headers=headers)
        LED_BLUE_BLINK(300,2)
        print("Data sucessfully sent")
        data_transferred = True
    except:
        print("Data send failed")
        #print(request_data.status_code, request_data.reason)
        LED_BLUE_OFF()
        LED_RED_BLINK(300,2)
        LED_BLUE_ON()
        data_transferred = False
    return data_transferred

# ⚊⚊⚊⚊⚊ send image over wifi ⚊⚊⚊⚊⚊
# transfer image file to server
# --- Indictors ---
# BLUE blink when data was sent
# RED blink when data sending failed
# --- Input arguments ---
# url - server upload link, with API if necessary
# img1 - image file to be posted
# --- Output variables ---
# file_transferred - file was transferred boolean
def image_transfer(url, img1):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
    files = {'imageFile': ("img.jpg", open(img1, "rb"))}
    # send the file
    print("Sending file to server")
    try:
        request_image = requests.post(url, files=files, headers=headers)
        LED_BLUE_BLINK(300,2)
        # print some post request parameters
        print("Image sent to Server")
        file_transferred = True
    except Exception as e:
        print("File send failed")
        print(e)
        #print(request_image.status_code, request_image.reason)
        LED_BLUE_OFF()
        LED_RED_BLINK(300,2)
        LED_BLUE_ON()
        file_transferred = False
    return file_transferred

# ━━━━━━━━━━ 𝗦𝗪𝗜𝗧𝗖𝗛 𝗦𝗜𝗚𝗡𝗔𝗟 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 ━━━━━━━━━━
# ⚊⚊⚊⚊⚊ external interrupt initialization ⚊⚊⚊⚊⚊
# initialize interrupts for soft off switch
# --- Input arguments ---
# pin_switch - pin object for switch signal
# --- Output variables ---
# none
def switch_init(pin_switch):
    # allocate memory buffer for interrupt
    micropython.alloc_emergency_exception_buf(100)
    # create global variables so they are used everywhere
    global press_time
    global press_count
    global switch_timer
    global poweroff
    press_time = False
    press_count = 0
    switch_timer = Timer(7)
    poweroff = False
    # create interrupt on that pin
    ExtInt(pin_switch, ExtInt.IRQ_FALLING, Pin.PULL_UP, callback_switch)
    return

# ⚊⚊⚊⚊⚊ timer callback ⚊⚊⚊⚊⚊
# callback function for button press and timer callback
def callback_timer(timer):
    global press_count
    global press_time
    # check how many times button was pressed in 1 sec
    if (press_count==1):
        single_press()
    elif (press_count==2):
        double_press()
    elif (press_count==3):
        triple_press()
    # reset alarm variable
    switch_timer.deinit()
    press_time = False
    return

# ⚊⚊⚊⚊⚊ ext. interrupt callback ⚊⚊⚊⚊⚊
def callback_switch(line):
    # get global variables to change their value
    global press_time
    global press_count
    #  count for how long the switch stays in the pressed position
    active = 0
    while (not pin_switch.value()):
        active += 1
        pyb.delay(1)
    # to avoid debaounce, id needs to be stable for more than 10 ms (to be fine tuned)
    if(active > 10):
        # if first button press, init timer and press counter
        if (not press_time):
            switch_timer.init(period=1000, callback=callback_timer)
            press_time = True
            press_count = 1
            print("Button pressed first time")
        else:
            # increment the switch presss counter
            press_count += 1
            print("Button pressed again")
    return

# ⚊⚊⚊⚊⚊ switch functions ⚊⚊⚊⚊⚊
# function for switch double press and tripple press
def single_press():
    global poweroff
    poweroff = True
    return

def double_press():
    LED_PURPLE_BLINK(200,3)
    return

def triple_press():
    LED_CYAN_BLINK(200,3)
    return

# ⚊⚊⚊⚊⚊ soft poweroff check ⚊⚊⚊⚊⚊
# checks if a power off is requested
# --- Indictors ---
# fast blinking RED while draining hold-OFF capacitor
# --- Input arguments ---
# pin_switch - pin object for switch signal
def check_poweroff(pin_switch):
    if(poweroff):
        LED_RED_BLINK(500,1)
        if (pyb.USB_VCP().isconnected()):
            machine.reset()
        Pin(pin_switch,Pin.OUT_PP)
        pin_switch.low()
        while(True):
            LED_RED_BLINK(100,1)
            pyb.delay(100)
    return
