import sensor
from util.rect import Rect

class Mode:
    """
    "enum" for operation modes.
    (py enums not inluded in micropython)
    """
    LIVE_VIEW = 0
    DEPLOY = 1
    LIVE_CAPTURE = 2

class Settings():
    """
    Singleton class to handle application settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):  # Prevent re-initialization
            return

        self._initialized = True

        #operation mode:
        #0: live view. Disables saving pictures, frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
        #1: deploy or test (do not override settings listed below)
        #2: live capture. Disables frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
        self.MODE = Mode.DEPLOY

        #whether the power management system is used or not
        self.POWER_MANAGEMENT_ENABLED = False
        #whether the voltage divider circuit is plugged or not
        self.VOLTAGE_DIV_AVAILABLE = False
        
        ### IMAGE ###
        #what resolution to use
        self.SENSOR_FRAMESIZE = sensor.WQXGA2
        #sensor image format. Options:
        #RGB565 = color
        #GRAYSCALE = black & white)
        self.SENSOR_PIXFORMAT = sensor.RGB565
        #whether to digitally zoom into image
        self.USE_SENSOR_WINDOWING = False
        #introduce delay between pictures (seconds). Otherwise with a delay of 0, the camera runs at maximum speed
        self.picture_delay_s = 0
        #threshold above which the camera goes to sleep between pictures to save power. Below that threshold, the camera will stay on and simply wait
        self.SLEEP_THRESHOLD_S = 10
        #for saving whole images or regions of interest (ROIs). Options:
        #none: save no picture
        #all: save all pictures (fd_enable must be False)
        #trigger: save image-change-triggered pictures
        #detect: save images with model-detected patterns
        self.save_roi_mode = "all"
        # _____ windowing mode only parameters _____
        #rectangle tuples (x,y coordinates and width and height) for digital zoom. x=0,y=0 is conventionally the upper left corner.
        #windowing_x=324 corresponds to the point from which a central square crop can be taken while using all the vertical resolution of the sensor
        self.WIN_RECT = Rect(324,0,1944,1944)
        # _____ advanced settings _____
        #wether to use user-defined rois (regions of interest)
        self.USE_ROI = False
        self.roi_rects = [(197,742,782,753),(1309,1320,560,460)]
        #wether to control number of frame buffers
        self.USE_SENSOR_FRAMEBUFFERS = False
        self.NB_SENSOR_FRAMEBUFFERS = 1
        #set JPEG quality (90: ~1 MB, 95: ~2MB, 100: ~7MB). Hardly discernible improvement above 93
        #0: minimum
        #100: maximum
        self.JPEG_QUALITY = 93

        ### EXPOSURE ###
        #exposure control mode. Options:
        #auto: camera continuously adjusts exposure time and gain, not compatible with frame differencing-based detection
        #bias: adjusting exposure and gain automatically at regular intervals (time period can be defined below) but with a user-defined bias for exposure time and gain
        #exposure: fixing exposure time, while adjusting gain at regular intervals (time period can be defined below)
        #manual: fixing exposure time and gain
        self.exposure_mode = "auto"
        #wether to use exposure bracketing
        self.use_exposure_bracketing = False
        # _____ bias mode only parameters _____
        #settings for bias mode: This is the user-defined multiplicative bias for the exposure time. Multiplies the automatic exposure time with this value. Values above 1 brighten the image, values below 1 darken it.
        #for instance, if your subject has a bright background (e.g., sky) during the day, you may use values above 1 for the day bias
        #if your subject is more strongly illuminated by the IR LEDs than the background during the night, use values below 1 for the night bias
        self.EXPOSURE_BIAS_DAY = 1
        self.EXPOSURE_BIAS_NIGHT = 1
        #gain user-bias. Multiplies the automatically-determined gain with this value. Values above 1 brighten the image, values below 1 darken it.
        self.GAIN_BIAS = 1
        # _____ manual or exposure mode only parameters _____
        #setting for manual and exposure mode:
        self.EXPOSURE_MS = 20
        #setting for manual mode:
        self.GAIN_DB = 24
        # ⚊⚊⚊⚊⚊ advanced settings ⚊⚊⚊⚊⚊
        # How often to adjust exposure, if not in manual or auto mode
        self.EXPOSE_PERIOD_S = 60
        # multiplicative exposure factors used for exposure bracketing, given in tuple. Sequence matters. Lowers frames per second.
        self.EXPOSURE_BRACKETING_VALUES = [1,0.5,2]

        ### ILLUMINATION LED ###
        #wether the light shield or IR LED module is installed
        #this parameter is only used to determine the voltage divider values
        self.LED_MODULE_AVAILABLE = False
        # which LEDs to use
        # module : installed LED module, can be IR or White LEDs
        # onboard : use onboard IR LEDs
        self.LED_MODE = "onboard"
        #operation mode for onboard IR or module LEDs at night. Options:
        #on: continuously ON during night time . Should be used for continuous illumination with frame differencing
        #blink: power-saving intermittent powering on. Should be used to save power, but only when using models to detect targets, since illumination will be unstable
        #off: always OFF
        self.LED_NIGHT_MODE = "off"
        # ______ LED module only parameters ______
        #PWM (brightness) of the plug-in LED module
        self.LED_MODULE_BRIGHTNESS_PWM = 100
        #how long to turn the LED module on (milliseconds) - should possibly not be longer than 3 seconds for IR module
        self.LED_MODULE_WARMUP_MS = 3000
        #how long to turn the LED module off (milliseconds) - should possibly be longer than 5 seconds for IR module
        self.LED_MODULE_COOLDOWN_MS = 0

        ### FRAME DIFFERENCING ###
        #wether to use frame differencing. This subtracts every current image from a reference image, resulting in dark images when there is no change.
        #a change will introduce a "blob" in the otherwise dark image, which can be detected, logged, and characterised
        self.frame_differencing_enabled = False
        # _____ FD enabled only parameters _____
        #action for blobs. options:
        #stop: stop detecting blobs after the first one
        #log: log all blobs in detections file
        self.BLOB_TASK = "log"
        #sensitivity of the blob detection, as measured by the area (number of pixels) of the blobs. Blobs outside this min-max range will not be logged.
        #Blob areas can be estimated by drawing rectangular selections on the image preview with the mouse; the area will be displayed below
        self.MIN_BLOB_PIXELS = 3000
        self.MAX_BLOB_PIXELS = 500000
        #color channel thresholds for detection. Pixels with color channel values outside of these ranges will be considered to be blobs.
        #requires at least one tuple for grayscale images (for instance: [(0,5)]), three tuples for RGB565 images (for instance: [(0,3),(-3,3),(-3,3)] - this corresponds to LAB channels)
        self.BLOB_COLOR_THRESHOLDS = [(0,5)]
        # _____ advanced settings _____
        #wether to export the detected blobs as jpegs (e.g., for gathering training images). options:
        #rectangle: exports bounding rectangle
        #square: exports bounding square with a side length of the longest side of the blob's bounding rectangle
        #none: does not export blobs
        self.BLOBS_EXPORT_METHOD = "none"
        # How much to blend by ([0-256]==[0.0-1.0]). NOTE that blending happens every time exposure is adjusted
        self.BACKGROUND_BLEND_LEVEL = 128

        ### NEURAL NETWORKS ###
        #wether to us neural networks to analyse the image. options:
        #image: classify the whole image (i.e. image classification)
        #objects: detect (multiple) targets within image (i.e. object detection)
        #blobs: classify the blobs (extracted from their bounding rectangles)
        #none: do not use neural networks
        self.classify_mode = "none"
        # _____ classify enabled only parameters _____
        #absolute file paths to model and labels files stored on SD card. needs to start with backslash if file is in root
        self.NET_PATH = "/trained.tflite"
        self.LABELS_PATH = "/labels.txt"
        # model resolution - used for re-scaling before image classification to get a better performance result
        self.MODEL_RES = 320
        #target confidence score above which the image is considered a detection and logged
        self.THRESHOLD_CONFIDENCE = 0.2
        #define non-target label names to exclude from image classification results
        self.NON_TARGET_LABELS = "Background"
        # Add more colors if you are detecting more than 7 types of classes at once
        self.CLASS_COLORS = [(255,0,0),(0,255,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255)]
        # --- advanced settings
        #minimum image scale for model input
        self.MIN_IMAGE_SCALE = 1
        #under which image scale image analysis should be deferred after sunset (with 0.5 overlapping windows in both directions, scale 0.5 takes 8 s, 0.25 takes 40 s, 0.125 takes 3 min)
        self.THRESHOLD_IMAGE_SCALE_DEFER = 0.5

        ### INDICATORS ###
        #wether to show the LED signals and image markings. initialising, waking, sleeping, and regular blinking LED signals, as well as warnings are not affected
        self.INDICATORS_ENBLED = True
        #how often to save status log
        self.LOG_STATUS_PERIOD_MS = 10*60*1000 
        # ______ advanced settings _____
        #period of blue LED indicating camera is active (in milliseconds, also works when indicators=False)
        self.ACTIVE_LED_INTERVAL_MS = 60*1000
        #how long to turn on active LED
        self.ACTIVE_LED_DURATION_MS = 500
        #how many voltage readings to average over to obtain the value that will be logged
        self.VOLTAGE_AVG_SAMPLE_COUNT = 10
        #how much delay between voltage readings (in milliseconds)
        self.VOLTAGE_READINGS_DELAY_MS = 10
        #minimum voltage for image sensor operation. theoretically, when voltage is below 2.7 V, the image sensor stops working
        self.VBAT_MINIMUM_VOLT = 0
        
        ### TIME AND POWER ###
        #when the camera should work. options:
        #night: during the night (between sunrise and sunset)
        #day: during the day (between sunset and sunrise)
        #24h: all the time
        self.operation_coverage = "24h"
        # select which RTC to use
        # onboard : internal STM32 RTC (10 min offset every 6 hours)
        # ds3231 : IR shield v3 shield (green) with ML621 coin cell battery
        # pcf8563 : WUV shield (red) with CR1220 coin cell battery
        self.rtc_mode = 'onboard'
        #For internal RTC, set the current date and time manually (year, month, day, weekday, hours, minutes, seconds, subseconds).
        self.START_DATETIME = (2022, 9, 15, 0, 18, 33, 35, 0)
        #defining operation times for camera, depending on its operation time mode
        self.SUNRISE_HOUR = 5
        self.SUNRISE_MINUTE = 17
        self.SUNSET_HOUR = 18
        self.SUNSET_MINUTE = 34

        ### CONNECTIVITY ###
        # whether to use WiFi, WiFi shield needs to be installed
        self.WIFI_ENABLED = False
        # _____ wifi enabled only parameters _____
        # Wifi name and password
        self.WIFI_SSID = ""
        self.WIFI_KEY = ""
        # url link to image/data/notification hosting website
        self.UPLOAD_DATA_API_URL = ""
        self.UPLOAD_IMG_URL = ""
        # which data to transfer (ATM only send_confidence is implemented)
        self.UPLOAD_CONFIDENCE_ENABLED = False
        self.UPLOAD_IMAGE_ENABLED = False
        self.UPLOAD_DIFFERENCING_ENABLED = False
        self.UPLOAD_VOLTAGE_ENABLED = False
        #  _____ advanced setting _____
        #confidence above which the image is sent over wifi
        self.UPLOAD_CONFIDENCE_THRESHOLD = 0.5

        # Apply the shortcut mode on settings
        if (self.MODE == Mode.LIVE_VIEW or self.MODE == Mode.LIVE_CAPTURE):
            self.frame_differencing_enabled = False
            self.classify_mode = "none"
            self.operation_coverage = "24h"
            self.exposure_mode = "auto"
            self.picture_delay_s = 0
            self.use_exposure_bracketing = False
            self.rtc_mode = 'onboard'
            if (self.MODE == Mode.LIVE_VIEW):
                self.save_roi_mode = "none"
                print("*** Live view enabled! *** ")
            if (mode == 2):
                self.save_roi_mode = "all"
                print("*** Live capture enabled! ***")
        elif (self.MODE == Mode.DEPLOY): print("*** Deployment started! ***")

        if(self.MODE != Mode.LIVE_VIEW and not self.USE_ROI):
            #assign roi to entire image if we do not use them
            self.roi_rects = [(0,0,sensor.width(),sensor.height())]