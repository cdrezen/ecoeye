from micropython import const

#operation mode:
#0: live view. Disables saving pictures, frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
#1: deploy or test (do not override settings listed below)
#2: live capture. Disables frame differencing, classifying, sleeping, bracketing, delay between pictures. Uses auto-exposure.
class Mode:
    """
    "enum" for operation modes.
    (py enums not inluded in micropython)
    """
    LIVE_VIEW:int = const(0)
    DEPLOY:int = const(1)
    LIVE_CAPTURE:int = const(2)
    
    @staticmethod
    def to_str(val:int):
        return ("LIVE_VIEW" if val == Mode.LIVE_VIEW else
                "DEPLOY" if val == Mode.DEPLOY else
                "LIVE_CAPTURE")
    
#exposure control mode. Options:
#auto: camera continuously adjusts exposure time and gain, not compatible with frame differencing-based detection
#bias: adjusting exposure and gain automatically at regular intervals (time period can be defined below) but with a user-defined bias for exposure time and gain
#exposure: fixing exposure time, while adjusting gain at regular intervals (time period can be defined below)
#manual: fixing exposure time and gain
class ExposureMode:
    """
    "enum" for exposure modes.
    (py enums not included in micropython)
    """
    AUTO:int = const(0)
    BIAS:int = const(1)
    EXPOSURE:int = const(2)
    MANUAL:int = const(3)

#operation mode for onboard IR or module LEDs at night. Options:
#on: continuously ON during night time . Should be used for continuous illumination with frame differencing
#blink: power-saving intermittent powering on. Should be used to save power, but only when using models to detect targets, since illumination will be unstable
#off: always OFF
class LedNightMode:
    """
    "enum" for LED night modes.
    """
    ON:int = const(0)
    BLINK:int = const(1)
    OFF:int = const(2)

class BlobExportShape:
    RECTANGLE:int = const(0)
    SQUARE:int = const(1)

#image: classify the whole image (i.e. image classification)
#objects: detect (multiple) targets within image (i.e. object detection)
#blobs: classify the blobs (extracted from their bounding rectangles)
#none: do not use neural networks
class ML_Mode:
    """
    "enum" for classify modes.
    """
    FRAME_CLASS:int = const(0)
    OBJECT_DETECT:int = const(1)
    BLOB_CLASS:int = const(2)

#when the camera should work. options:
#night: during the night (between sunrise and sunset)
#day: during the day (between sunset and sunrise)
#all: all the time (24h)
class TimeCoverage:
    """
    "enum" for classify modes.
    (py enums not inluded in micropython)
    """
    ALL:int = const(0)
    DAY:int = const(1)
    NIGHT:int = const(2)