import sensor
from util.rect import Rect

class Mode:
    """
    "enum" for operation modes.
    (py enums not inluded in micropython)
    """
    LIVE_VIEW:int = 0
    DEPLOY:int = 1
    LIVE_CAPTURE:int = 2
    
    @staticmethod
    def to_str(val:int):
        return ("LIVE_VIEW" if val == Mode.LIVE_VIEW else
                "DEPLOY" if val == Mode.DEPLOY else
                "LIVE_CAPTURE")

#operation mode:
#0: live view. Disables saving pictures, frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
#1: deploy or test (do not override settings listed below)
#2: live capture. Disables frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
MODE = Mode.DEPLOY

### POWER MANAGEMENT ###
#whether the power management system is used or not
POWER_MANAGEMENT_ENABLED = False
#whether the voltage divider circuit is plugged or not
VOLTAGE_DIV_AVAILABLE = True
#how often to check the battery
CHECK_BAT_PERIOD_MS = 10*60*1000 
#how many voltage readings to average over to obtain the value that will be logged
VOLTAGE_AVG_SAMPLE_COUNT = 10
#how much delay between voltage readings (in milliseconds)
VOLTAGE_READINGS_DELAY_MS = 10
#minimum voltage for image sensor operation. theoretically, when voltage is below 2.7 V, the image sensor stops working
VBAT_MINIMUM_VOLT = 0
#introduce delay between pictures (seconds). Otherwise with a delay of 0, the camera runs at maximum speed
PICTURE_DELAY_MS = 0 if MODE != Mode.DEPLOY else 0
#threshold of PICTURE_DELAY_S above which the camera goes to sleep between pictures to save power. Below that threshold, the camera will stay on and simply wait
USE_DSLEEP_PIC_DELAY = PICTURE_DELAY_MS > 10000
# how long to stay in deep sleep by default (in milliseconds)
DEEPSLEEP_DEFAULT_DURATUION_MS = 60000


### IMAGE ###
#what resolution to use
# sensor.FHD: 1920x1080 
# sensor.QHD: 2560x1440 
# sensor.QXGA: 2048x1536 
# sensor.WQXGA: 2560x1600 
# sensor.WQXGA2: 2592x1944 
SENSOR_FRAMESIZE = sensor.WQXGA
#sensor image format. Options:
#RGB565 = color
#GRAYSCALE = black & white)
SENSOR_PIXFORMAT = sensor.RGB565
#for saving whole images or regions of interest (ROIs). Options:
#none: save no picture
#all: save all pictures (fd_enable must be False)
#trigger: save image-change-triggered pictures
#detect: save images with model-detected patterns
SAVE_ROI_MODE = "none" if MODE == Mode.LIVE_VIEW else "trigger"
# _____ windowing mode only parameters _____
#whether to digitally zoom into image
USE_SENSOR_WINDOWING = True
#rectangle tuples (x,y coordinates and width and height) for digital zoom. x=0,y=0 is conventionally the upper left corner.
#windowing_x=324 corresponds to the point from which a central square crop can be taken while using all the vertical resolution of the sensor
WIN_RECT = Rect(960,0,1600,1600)
# _____ advanced settings _____
#wether to control number of frame buffers or not (<1)
NB_SENSOR_FRAMEBUFFERS = 1
#set JPEG quality (90: ~1 MB, 95: ~2MB, 100: ~7MB). Hardly discernible improvement above 93
#0: minimum
#100: maximum
JPEG_QUALITY = 93

### EXPOSURE ###
#exposure control mode. Options:
#auto: camera continuously adjusts exposure time and gain, not compatible with frame differencing-based detection
#bias: adjusting exposure and gain automatically at regular intervals (time period can be defined below) but with a user-defined bias for exposure time and gain
#exposure: fixing exposure time, while adjusting gain at regular intervals (time period can be defined below)
#manual: fixing exposure time and gain
EXPOSURE_MODE = "auto" if MODE != Mode.DEPLOY else "bias"
# if > -1 start with this exposure an gain:
EXPOSURE_START_US = -1
GAIN_START_DB = -1
# _____ bias mode only parameters _____
#settings for bias mode: This is the user-defined multiplicative bias for the exposure time. Multiplies the automatic exposure time with this value. Values above 1 brighten the image, values below 1 darken it.
#for instance, if your subject has a bright background (e.g., sky) during the day, you may use values above 1 for the day bias
#if your subject is more strongly illuminated by the IR LEDs than the background during the night, use values below 1 for the night bias
EXPOSURE_BIAS_DAY = 1
EXPOSURE_BIAS_NIGHT = 1
#gain user-bias. Multiplies the automatically-determined gain with this value. Values above 1 brighten the image, values below 1 darken it.
GAIN_BIAS = 1
# _____ manual or exposure mode only parameters _____
#setting for manual and exposure mode:
EXPOSURE_US = 100
#setting for manual mode:
GAIN_DB = 10
# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
# How often to adjust exposure, if not in manual or auto mode


### ILLUMINATION LED ###
#wether the light shield or IR LED module is installed
#this parameter is only used to determine the voltage divider values
LED_MODULE_AVAILABLE = False
# which LEDs to use
# module : installed LED module, can be IR or White LEDs
# onboard : use onboard IR LEDs
LED_MODE = "onboard"
#operation mode for onboard IR or module LEDs at night. Options:
#on: continuously ON during night time . Should be used for continuous illumination with frame differencing
#blink: power-saving intermittent powering on. Should be used to save power, but only when using models to detect targets, since illumination will be unstable
#off: always OFF
LED_NIGHT_MODE = "blink"
# ______ LED module only parameters ______
#PWM (brightness) of the plug-in LED module
LED_MODULE_BRIGHTNESS_PWM = 100
#how long to turn the LED module on (milliseconds) - should possibly not be longer than 3 seconds for IR module
LED_MODULE_WARMUP_MS = 3000
#how long to turn the LED module off (milliseconds) - should possibly be longer than 5 seconds for IR module
LED_MODULE_COOLDOWN_MS = 0

### FRAME DIFFERENCING ###
#wether to use frame differencing. This subtracts every current image from a reference image, resulting in dark images when there is no change.
#a change will introduce a "blob" in the otherwise dark image, which can be detected, logged, and characterised
FRAME_DIFF_ENABLED = False if MODE != Mode.DEPLOY else True
# _____ FD enabled only parameters _____
#action for blobs. options:
# x: stop processing blobs after the x one
#-1: log all blobs in detections file
MAX_BLOB_TO_PROCESS=-1
#sensitivity of the blob detection, as measured by the area (number of pixels) of the blobs. Blobs outside this min-max range will not be logged.
#Blob areas can be estimated by drawing rectangular selections on the image preview with the mouse; the area will be displayed below
MIN_BLOB_PIXELS = 75*75
MAX_BLOB_PIXELS = 500*500
#color channel thresholds for detection. Pixels with color channel values outside of these ranges will be considered to be blobs.
#requires at least one tuple with 2 values for grayscale images (for instance: [(0,5)]), with 6 values for RGB565 images (for instance: [(0,3,-3,3,-3,3)] - this corresponds to min and max values for L, A and B channels)
BLOB_COLOR_THRESHOLDS = [(0, 2, -6, 6, -6, 6)]

class BlobExportShape:
    RECTANGLE = 0
    SQUARE = 1
# _____ advanced settings _____
#wether to export the detected blobs as jpegs (e.g., for gathering training images). options:
#rectangle: exports bounding rectangle
#square: exports bounding square with a side length of the longest side of the blob's bounding rectangle
#None: does not export blobs

BLOBS_EXPORT_METHOD = BlobExportShape.RECTANGLE
# How much to blend by ([0-256]==[0.0-1.0]). NOTE that blending happens every time exposure is adjusted
BACKGROUND_BLEND_LEVEL = 128
# How long to wait for auto blending frame in reference image (in milliseconds)
BLEND_TIMEOUT_MS = 10000

### NEURAL NETWORKS ###
#wether to us neural networks to analyse the image. options:
#image: classify the whole image (i.e. image classification)
#objects: detect (multiple) targets within image (i.e. object detection)
#blobs: classify the blobs (extracted from their bounding rectangles)
#none: do not use neural networks
CLASSIFY_MODE = "none" if MODE != Mode.DEPLOY else "none"
# _____ classify enabled only parameters _____
#absolute file paths to model and labels files stored on SD card. needs to start with backslash if file is in root
NET_PATH = "/trained.tflite"
LABELS_PATH = "/labels.txt"
# model resolution - used for re-scaling before image classification to get a better performance result
MODEL_RES = 320
#target confidence score above which the image is considered a detection and logged
THRESHOLD_CONFIDENCE = 0.2
#define non-target label names to exclude from image classification results
NON_TARGET_LABELS = "Background"
# Add more colors if you are detecting more than 7 types of classes at once
CLASS_COLORS = [(255,0,0),(0,255,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255)]
# --- advanced settings
#minimum image scale for model input
MIN_IMAGE_SCALE = 1
#under which image scale image analysis should be deferred after sunset (with 0.5 overlapping windows in both directions, scale 0.5 takes 8 s, 0.25 takes 40 s, 0.125 takes 3 min)
THRESHOLD_IMAGE_SCALE_DEFER = 0.5

### INDICATORS ###
#wether to show the LED signals and image markings. initialising, waking, sleeping, and regular blinking LED signals, as well as warnings are not affected
INDICATORS_ENABLED = True
#period of blue LED indicating camera is active (in milliseconds, also works when indicators=False)
BUSY_LED_INTERVAL_MS = 60*1000
#how long to turn on active LED
BUSY_LED_DURATION_MS = 500

### TIME ###
#when the camera should work. options:
#night: during the night (between sunrise and sunset)
#day: during the day (between sunset and sunrise)
#24h: all the time
TIME_COVERAGE = "24h" if MODE != Mode.DEPLOY else "24h"
# select which RTC to use
# onboard : internal STM32 RTC (10 min offset every 6 hours)
# ds3231 : IR shield v3 shield (green) with ML621 coin cell battery
# pcf8563 : WUV shield (red) with CR1220 coin cell battery
RTC_MODE = 'onboard' if MODE != Mode.DEPLOY else 'onboard'
#For internal RTC, set the current date and time manually (year, month, day, weekday, hours, minutes, seconds, subseconds).
START_DATETIME = (2025, 5, 15, 5, 12, 12, 0, 0)
#defining operation times for camera, depending on its operation time mode
SUNRISE_HOUR = 5
SUNRISE_MINUTE = 17
SUNSET_HOUR = 18
SUNSET_MINUTE = 34

### CONNECTIVITY ###
# whether to use WiFi, WiFi shield needs to be installed
WIFI_ENABLED = False
# _____ wifi enabled only parameters _____
# Wifi name and password
WIFI_SSID = ""
WIFI_KEY = ""
# url link to image/data/notification hosting website
UPLOAD_DATA_API_URL = ""
UPLOAD_IMG_URL = ""
# which data to transfer (ATM only send_confidence is implemented)
UPLOAD_CONFIDENCE_ENABLED = False
UPLOAD_IMAGE_ENABLED = False
UPLOAD_DIFFERENCING_ENABLED = False
UPLOAD_VOLTAGE_ENABLED = False
#  _____ advanced setting _____
#confidence above which the image is sent over wifi
UPLOAD_CONFIDENCE_THRESHOLD = 0.5