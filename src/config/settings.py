# ╋╋╋╋╋╋╋╋╋╋ 𝙐𝙎𝙀𝙍-𝘿𝙀𝙁𝙄𝙉𝙀𝘿 𝙋𝘼𝙍𝘼𝙈𝙀𝙏𝙀𝙍𝙎 ╋╋╋╋╋╋╋╋╋╋

import sensor

# ━━━━━━━━━━ 𝗦𝗛𝗢𝗥𝗧𝗖𝗨𝗧 𝗠𝗢𝗗𝗘𝗦 ━━━━━━━━━━
#operation mode:
#0: live view. Disables saving pictures, frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
#1: deploy or test (do not override settings listed below)
#2: live capture. Disables frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
MODE = 1

# ━━━━━━━━━━ 𝗚𝗘𝗡𝗘𝗥𝗔𝗟 ━━━━━━━━━━
#camera ID: enter the ID written on the H7+ board's QR code sticker
camera_ID = "00000"
#whether the power management system is used or not
PMS = False
#whether the voltage divider circuit is plugged or not
voltage_divider = False

# ━━━━━━━━━━ 𝗜𝗠𝗔𝗚𝗘 ━━━━━━━━━━
#what resolution to use
sensor_framesize = sensor.WQXGA2
#sensor image format. Options:
#RGB565 = color
#GRAYSCALE = black & white)
sensor_pixformat = sensor.RGB565
#whether to digitally zoom into image
sensor_windowing = False
#introduce delay between pictures (seconds). Otherwise with a delay of 0, the camera runs at maximum speed
delay_loop_s = 0
#for saving whole images or regions of interest (ROIs). Options:
#none: save no picture
#all: save all pictures (fd_enable must be False)
#trigger: save image-change-triggered pictures
#detect: save images with model-detected patterns
save_roi = "all"

# ⚊⚊⚊⚊⚊ windowing mode only parameters ⚊⚊⚊⚊⚊
#rectangle tuples (x,y coordinates and width and height) for digital zoom. x=0,y=0 is conventionally the upper left corner.
#windowing_x=324 corresponds to the point from which a central square crop can be taken while using all the vertical resolution of the sensor
windowing_x = 324
windowing_y = 0
windowing_w = 1944
windowing_h = 1944

# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
#whether to use user-defined rois (regions of interest)
use_roi = False
rois = [(197,742,782,753),(1309,1320,560,460)]
#whether to control number of frame buffers
sensor_framebuffers_control = False
sensor_framebuffers = 1
#threshold above which the camera goes to sleep between pictures to save power. Below that threshold, the camera will stay on and simply wait
delay_threshold_sleep_s = 10
#set JPEG quality (90: ~1 MB, 95: ~2MB, 100: ~7MB). Hardly discernible improvement above 93
#0: minimum
#100: maximum
jpeg_quality = 93

# ━━━━━━━━━━ 𝗘𝗫𝗣𝗢𝗦𝗨𝗥𝗘 ━━━━━━━━━━
#exposure control mode. Options:
#auto: camera continuously adjusts exposure time and gain, not compatible with frame differencing-based detection
#bias: adjusting exposure and gain automatically at regular intervals (time period can be defined below) but with a user-defined bias for exposure time and gain
#exposure: fixing exposure time, while adjusting gain at regular intervals (time period can be defined below)
#manual: fixing exposure time and gain
exposure_control = "auto"
#whether to use exposure bracketing
exposure_bracketing = False

# ⚊⚊⚊⚊⚊ bias mode only parameters ⚊⚊⚊⚊⚊
#settings for bias mode: This is the user-defined multiplicative bias for the exposure time. Multiplies the automatic exposure time with this value. Values above 1 brighten the image, values below 1 darken it.
#for instance, if your subject has a bright background (e.g., sky) during the day, you may use values above 1 for the day bias
#if your subject is more strongly illuminated by the IR LEDs than the background during the night, use values below 1 for the night bias
exposure_bias_day = 1
exposure_bias_night = 1
#gain user-bias. Multiplies the automatically-determined gain with this value. Values above 1 brighten the image, values below 1 darken it.
gain_bias = 1
# ⚊⚊⚊⚊⚊ manual or exposure mode only parameters ⚊⚊⚊⚊⚊
#setting for manual and exposure mode:
exposure_ms = 20
#setting for manual mode:
gain_dB = 24

# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
# How often to adjust exposure, if not in manual or auto mode
expose_period_s = 60
# multiplicative exposure factors used for exposure bracketing, given in tuple. Sequence matters. Lowers frames per second.
exposure_bracketing_values = [1,0.5,2]

# ━━━━━━━━━━ 𝗜𝗟𝗟𝗨𝗠𝗜𝗡𝗔𝗧𝗜𝗢𝗡 𝗟𝗘𝗗 ━━━━━━━━━━
#whether the light shield or IR LED module is installed
#this parameter is only used to determine the voltage divider values
LED_module = False
# which LEDs to use
# module : installed LED module, can be IR or White LEDs
# onboard : use onboard IR LEDs
LED_select = "onboard"
#operation mode for onboard IR or module LEDs at night. Options:
#on: continuously ON during night time . Should be used for continuous illumination with frame differencing
#blink: power-saving intermittent powering on. Should be used to save power, but only when using models to detect targets, since illumination will be unstable
#off: always OFF
LED_mode_night = "off"

# ⚊⚊⚊⚊⚊ LED module only parameters ⚊⚊⚊⚊⚊
#PWM (brightness) of the plug-in LED module
LED_module_PWM = 100
#how long to turn the LED module on (milliseconds) - should possibly not be longer than 3 seconds for IR module
LED_module_warmup = 3000
#how long to turn the LED module off (milliseconds) - should possibly be longer than 5 seconds for IR module
LED_module_cooldown = 0

# ━━━━━━━━━━ 𝗙𝗥𝗔𝗠𝗘 𝗗𝗜𝗙𝗙𝗘𝗥𝗘𝗡𝗖𝗜𝗡𝗚 ━━━━━━━━━━
#whether to use frame differencing. This subtracts every current image from a reference image, resulting in dark images when there is no change.
#a change will introduce a "blob" in the otherwise dark image, which can be detected, logged, and characterised
fd_enable = False

# ⚊⚊⚊⚊⚊ FD enabled only parameters ⚊⚊⚊⚊⚊
#action for blobs. options:
#stop: stop detecting blobs after the first one
#log: log all blobs in detections file
blob_action = "log"
#sensitivity of the blob detection, as measured by the area (number of pixels) of the blobs. Blobs outside this min-max range will not be logged.
#Blob areas can be estimated by drawing rectangular selections on the image preview with the mouse; the area will be displayed below
minimum_blob_pixels = 3000
maximum_blob_pixels = 500000
#color channel thresholds for detection. Pixels with color channel values outside of these ranges will be considered to be blobs.
#requires at least one tuple for grayscale images (for instance: [(0,5)]), three tuples for RGB565 images (for instance: [(0,3),(-3,3),(-3,3)] - this corresponds to LAB channels)
color_thresholds = [(0,5)]

# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
#whether to export the detected blobs as jpegs (e.g., for gathering training images). options:
#rectangle: exports bounding rectangle
#square: exports bounding square with a side length of the longest side of the blob's bounding rectangle
#none: does not export blobs
export_blobs = "none"
# How much to blend by ([0-256]==[0.0-1.0]). NOTE that blending happens every time exposure is adjusted
background_blend_level = 128

# ━━━━━━━━━━ 𝗡𝗘𝗨𝗥𝗔𝗟 𝗡𝗘𝗧𝗪𝗢𝗥𝗞𝗦 ━━━━━━━━━━
#whether to us neural networks to analyse the image. options:
#image: classify the whole image (i.e. image classification)
#objects: detect (multiple) targets within image (i.e. object detection)
#blobs: classify the blobs (extracted from their bounding rectangles)
#none: do not use neural networks
# TODO give new variable name
classify_mode = "none"

# ⚊⚊⚊⚊⚊ classify enabled only parameters ⚊⚊⚊⚊⚊
#absolute file paths to model and labels files stored on SD card. needs to start with backslash if file is in root
net_path = "/trained.tflite"
labels_path = "/labels.txt"
# model resolution - used for re-scaling before image classification to get a better performance result
model_resolution = 320
#target confidence score above which the image is considered a detection and logged
threshold_confidence = 0.2
#define non-target label names to exclude from image classification results
non_target_labels = "Background"
# --- advanced settings
#minimum image scale for model input
minimum_image_scale = 1
#under which image scale image analysis should be deferred after sunset (with 0.5 overlapping windows in both directions, scale 0.5 takes 8 s, 0.25 takes 40 s, 0.125 takes 3 min)
threshold_image_scale_defer = 0.5

# ━━━━━━━━━━ 𝗜𝗡𝗗𝗜𝗖𝗔𝗧𝗢𝗥𝗦 ━━━━━━━━━━
#whether to show the LED signals and image markings. initialising, waking, sleeping, and regular blinking LED signals, as well as warnings are not affected
indicators = True
#how often to save status log
status_logging_period_ms = 10*60*1000

# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
#period of blue LED indicating camera is active (in milliseconds, also works when indicators=False)
active_LED_interval_ms = 60*1000
#how long to turn on active LED
active_LED_duration_ms = 500
#how many voltage readings to average over to obtain the value that will be logged
voltage_readings = 10
#how much delay between voltage readings (in milliseconds)
voltage_readings_delay = 10
#minimum voltage for image sensor operation. theoretically, when voltage is below 2.7 V, the image sensor stops working
vbat_minimum = 0
# Add more colors if you are detecting more than 7 types of classes at once
colors = [(255,0,0),(0,255,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255)]

# ━━━━━━━━━━ 𝗧𝗜𝗠𝗘 𝗔𝗡𝗗 𝗣𝗢𝗪𝗘𝗥 ━━━━━━━━━━
#when the camera should work. options:
#night: during the night (between sunrise and sunset)
#day: during the day (between sunset and sunrise)
#24h: all the time
operation_time = "24h"
# select which RTC to use
# onboard : internal STM32 RTC (10 min offset every 6 hours)
# ds3231 : IR shield v3 shield (green) with ML621 coin cell battery
# pcf8563 : WUV shield (red) with CR1220 coin cell battery
RTC_select = 'onboard'
# For internal RTC, set the current date and time manually (year, month, day, weekday, hours, minutes, seconds, subseconds).
current_date_time = (2022, 9, 15, 0, 18, 33, 35, 0)
#defining operation times for camera, depending on its operation time mode
sunrise_hour = 5
sunrise_minute = 17
sunset_hour = 18
sunset_minute = 34

# ━━━━━━━━━━ 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗩𝗧𝗬 ━━━━━━━━━━
# whether to use WiFi, WiFi shield needs to be installed
wifi_enable = False

# ⚊⚊⚊⚊⚊ wifi enabled only parameters ⚊⚊⚊⚊⚊
# Wifi name and password
wifi_ssid = "MiFiC14646"
wifi_key = "12345678"
# url link to image/data/notification hosting website
wifi_data_url = "https://api.thingspeak.com/update?api_key=WZRWZLO9PRNLY6Y7"
wifi_img_url = "http://potblitd.com/upload.php"
# which data to transfer (ATM only send_confidence is implemented)
send_confidence = False
send_image = False
send_differencing = False
send_voltage = False
#  ⚊⚊⚊⚊⚊ advanced setting ⚊⚊⚊⚊⚊
# confidence above which the image is sent over wifi
threshold_image = 0.5

# ╋╋╋╋╋╋╋╋╋╋ 𝙀𝙉𝘿 𝙊𝙁 𝙐𝙎𝙀𝙍-𝘿𝙀𝙁𝙄𝙉𝙀𝘿 𝙋𝘼𝙍𝘼𝙈𝙀𝙏𝙀𝙍𝙎 ╋╋╋╋╋╋╋╋╋╋

# ━━━━━━━━━━ 𝗦𝗛𝗢𝗥𝗧𝗖𝗨𝗧 𝗠𝗢𝗗𝗘𝗦 ━━━━━━━━━━
def use_shortcut_mode(mode: int = MODE):
    """
    Override settings in ine of the shortcut modes/
    Changes settings according to shortcut mode
    :param mode: shortcut mode
    """
    if (mode == 0 or mode == 2):
        global fd_enable, classify_mode, operation_time, exposure_control, delay_loop_s, exposure_bracketing, RTC_select, save_roi
        fd_enable = False
        classify_mode = "none"
        operation_time = "24h"
        exposure_control = "auto"
        delay_loop_s = 0
        exposure_bracketing = False
        RTC_select = 'onboard'
        if (mode == 0):
            save_roi = "none"
            print("*** Live view enabled! *** ")
        if (mode == 2):
            save_roi = "all"
            print("*** Live capture enabled! ***")
    # or not in normal mode
    elif (mode == 1): print("*** Deployment started! ***")
