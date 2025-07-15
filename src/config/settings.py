import sensor
from util.rect import Rect
from vision.image_type import ImageType
from config.enums import Mode, ExposureMode, LedNightMode, TimeCoverage, BlobExportShape
from micropython import const

#operation mode:
#0: live view. Disables saving pictures, frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
#1: deploy or test (do not override settings listed below)
#2: live capture. Disables frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
MODE = Mode.DEPLOY

### POWER MANAGEMENT ###
#whether the power management system is used or not
POWER_MANAGEMENT_ENABLED = const(False)
#whether the voltage divider circuit is plugged or not
VOLTAGE_DIV_AVAILABLE = const(True)
#how often to check the battery
CHECK_BAT_PERIOD_MS = const(10*60*1000) 

#introduce delay between pictures (seconds). Otherwise with a delay of 0, the camera runs at maximum speed
PICTURE_DELAY_MS = const(0) if MODE != Mode.DEPLOY else const(0)
#threshold of PICTURE_DELAY_S above which the camera goes to sleep between pictures to save power. Below that threshold, the camera will stay on and simply wait
USE_DSLEEP_PIC_DELAY = PICTURE_DELAY_MS > 10000
# how long to stay in deep sleep by default (in milliseconds)
DEEPSLEEP_DEFAULT_DURATUION_MS = const(60000)

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
    
# saving filter for images:
# = None: save no picture
# incl default: save all picture
# incl trigger: save image-change-triggered pictures
# incl detection: save images with model-detected patterns
IMG_SAVE_FILTER = const(None) if MODE == Mode.LIVE_VIEW else const([ImageType.TRIGGER, ImageType.DETECTION])
#rectangle tuples (x,y coordinates and width and height) for digital zoom. x=0,y=0 is conventionally the upper left corner. None for no windowing.
#windowing_x=324 corresponds to the point from which a central square crop can be taken while using all the vertical resolution of the sensor
WIN_RECT = Rect(960,0,1600,1600) # None
# _____ advanced settings _____
#wether to control number of frame buffers or not (<1)
NB_SENSOR_FRAMEBUFFERS:int = const(1)
#set JPEG quality (90: ~1 MB, 95: ~2MB, 100: ~7MB). Hardly discernible improvement above 93
JPEG_QUALITY = const(93)

### EXPOSURE ###
#exposure control mode. Options:
#auto: camera continuously adjusts exposure time and gain, not compatible with frame differencing-based detection
#bias: adjusting exposure and gain automatically at regular intervals (time period can be defined below) but with a user-defined bias for exposure time and gain
#exposure: fixing exposure time, while adjusting gain at regular intervals (time period can be defined below)
#manual: fixing exposure time and gain
EXPOSURE_MODE = ExposureMode.AUTO if MODE != Mode.DEPLOY else ExposureMode.BIAS
# if > -1 start with this exposure and gain:
EXPOSURE_START_US = const(-1)
GAIN_START_DB = const(-1)
# _____ bias mode only parameters _____
#settings for bias mode: This is the user-defined multiplicative bias for the exposure time. Multiplies the automatic exposure time with this value. Values above 1 brighten the image, values below 1 darken it.
#for instance, if your subject has a bright background (e.g., sky) during the day, you may use values above 1 for the day bias
#if your subject is more strongly illuminated by the IR LEDs than the background during the night, use values below 1 for the night bias
EXPOSURE_BIAS_DAY = const(1)
EXPOSURE_BIAS_NIGHT = const(1)
#gain user-bias. Multiplies the automatically-determined gain with this value. Values above 1 brighten the image, values below 1 darken it.
GAIN_BIAS = const(1)
# _____ manual or exposure mode only parameters _____
#setting for manual and exposure mode:
EXPOSURE_US = const(100)
#setting for manual mode:
GAIN_DB = const(10)
# ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
# How often to adjust exposure, if not in manual or auto mode


### ILLUMINATION LED ###
#operation mode for onboard IR or module LEDs at night. Options:
#on: continuously ON during night time . Should be used for continuous illumination with frame differencing
#blink: power-saving intermittent powering on. Should be used to save power, but only when using models to detect targets, since illumination will be unstable
#off: always OFF
LED_NIGHT_MODE = LedNightMode.BLINK

### FRAME DIFFERENCING ###
#wether to use frame differencing. This subtracts every current image from a reference image, resulting in dark images when there is no change.
#a change will introduce a "blob" in the otherwise dark image, which can be detected, logged, and characterised
FRAME_DIFF_ENABLED = const(False) if MODE != Mode.DEPLOY else const(True)
# _____ FD enabled only parameters _____
#action for blobs. options:
# x: stop processing blobs after the x one
#-1: log all blobs in detections file
MAX_BLOB_TO_PROCESS=const(-1)
#sensitivity of the blob detection, as measured by the area (number of pixels) of the blobs. Blobs outside this min-max range will not be logged.
#Blob areas can be estimated by drawing rectangular selections on the image preview with the mouse; the area will be displayed below
MIN_BLOB_PIXELS = const(75*75)
MAX_BLOB_PIXELS = const(500*500)
#color channel thresholds for detection. Pixels with color channel values outside of these ranges will be considered to be blobs.
#requires at least one tuple with 2 values for grayscale images (for instance: [(0,5)]), with 6 values for RGB565 images (for instance: [(0,3,-3,3,-3,3)] - this corresponds to min and max values for L, A and B channels)
BLOB_COLOR_THRESHOLDS = [(0, 2, -6, 6, -6, 6)]
#rectangle: exports bounding rectangle
#square: exports bounding square with a side length of the longest side of the blob's bounding rectangle
BLOBS_CROP_METHOD = BlobExportShape.RECTANGLE

### NEURAL NETWORKS ###
#image: classify the whole image (i.e. image classification)
#objects: detect (multiple) targets within image (i.e. object detection)
#blobs: classify the blobs (extracted from their bounding rectangles)
#none: do not use neural networks
ML_MODE = const(None) if MODE != Mode.DEPLOY else const(None)
# _____ classify enabled only parameters _____
#absolute file paths to model and labels files stored on SD card. needs to start with backslash if file is in root
NET_PATH = const("/trained.tflite")
LABELS_PATH = const("/labels.txt")
# model resolution - used for re-scaling before image classification to get a better performance result
MODEL_RES = const(320)
#target confidence score above which the image is considered a detection and logged
THRESHOLD_CONFIDENCE = const(0.5)
#define non-target label names to exclude from image classification results
NON_TARGET_LABELS = const("Background")
# --- advanced settings
#minimum image scale for model input
MIN_IMAGE_SCALE = const(1)

### INDICATORS ###
#wether to show the LED signals and image markings. initialising, waking, sleeping, and regular blinking LED signals, as well as warnings are not affected
INDICATORS_ENABLED = const(True)

### TIME ###
#when the camera should work. options:
#night: during the night (between sunrise and sunset)
#day: during the day (between sunset and sunrise)
#all: all the time (24h)
TIME_COVERAGE = TimeCoverage.ALL if MODE != Mode.DEPLOY else TimeCoverage.ALL
#For internal RTC, set the current date and time manually (year, month, day, weekday, hours, minutes, seconds, subseconds).
START_DATETIME = const((2025, 5, 15, 5, 12, 12, 0, 0))
#defining operation times for camera, depending on its operation time mode
SUNRISE_HOUR = const(5)
SUNRISE_MINUTE = const(17)
SUNSET_HOUR = const(18)
SUNSET_MINUTE = const(34)