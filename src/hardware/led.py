### LED FUNCTIONS ###
from machine import LED
import config.settings as cfg
from config.enums import LedNightMode
from util import timeutil
from micropython import const
import time
from util import timeutil

#period of blue LED indicating camera is active (in milliseconds, also works when indicators=False)
_BUSY_LED_INTERVAL_MS = const(60*1000)
#how long to turn on active LED
_BUSY_LED_DURATION_MS = const(500)

def LED_RED_ON():
    LED_RGB_OFF()
    LED(1).on()
    return
def LED_GREEN_ON():
    LED_RGB_OFF()
    LED(2).on()
    return
def LED_BLUE_ON():
    LED_RGB_OFF()
    LED(3).on()
    return
def LED_YELLOW_ON():
    LED_RGB_OFF()
    LED(1).on()
    LED(2).on()
    return
def LED_PURPLE_ON():
    LED_RGB_OFF()
    LED(1).on()
    LED(3).on()
    return
def LED_CYAN_ON():
    LED_RGB_OFF()
    LED(2).on()
    LED(3).on()
    return
def LED_WHITE_ON():
    LED_RGB_OFF()
    LED(1).on()
    LED(2).on()
    LED(3).on()
    return
def LED_IR_ON():
    LED_RGB_OFF()
    LED(4).on()
    return

def LED_RED_OFF():
    LED(1).off()
    return
def LED_GREEN_OFF():
    LED(2).off()
    return
def LED_BLUE_OFF():
    LED(3).off()
    return
def LED_YELLOW_OFF():
    LED(1).off()
    LED(2).off()
    return
def LED_PURPLE_OFF():
    LED(1).off()
    LED(3).off()
    return
def LED_CYAN_OFF():
    LED(2).off()
    LED(3).off()
    return
def LED_WHITE_OFF():
    LED(1).off()
    LED(2).off()
    LED(3).off()
    return
def LED_IR_OFF():
    LED(4).off()
    return
def LED_RGB_OFF():
    LED(1).off()
    LED(2).off()
    LED(3).off()
    return
# ⚊⚊⚊⚊⚊ LED TOGGLE ⚊⚊⚊⚊⚊
def LED_RED_TOGGLE():
    LED(2).off()
    LED(3).off()
    LED(1).toggle()
    return
def LED_GREEN_TOGGLE():
    LED(1).off()
    LED(3).off()
    LED(2).toggle()
    return
def LED_BLUE_TOGGLE():
    LED(1).off()
    LED(2).off()
    LED(3).toggle()
    return
def LED_YELLOW_TOGGLE():
    LED(3).off()
    LED(1).toggle()
    LED(2).toggle()
    return
def LED_PURPLE_TOGGLE():
    LED(2).off()
    LED(1).toggle()
    LED(3).toggle()
    return
def LED_CYAN_TOGGLE():
    LED(1).off()
    LED(4).off()
    LED(3).toggle()
    return
def LED_WHITE_TOGGLE():
    LED(1).toggle()
    LED(2).toggle()
    LED(3).toggle()
    return
def LED_IR_TOGGLE():
    LED(4).toggle()
    return
def LED_ALL_TOGGLE():
    LED(1).toggle()
    LED(2).toggle()
    LED(3).toggle()
    LED(4).toggle()
    return

def LED_RED_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(1).on()
        time.sleep_ms(blinktime)
        LED(1).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_GREEN_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(2).on()
        time.sleep_ms(blinktime)
        LED(2).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_BLUE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(3).on()
        time.sleep_ms(blinktime)
        LED(3).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_YELLOW_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(1).on()
        LED(2).on()
        time.sleep_ms(blinktime)
        LED(1).off()
        LED(2).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_PURPLE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(1).on()
        LED(3).on()
        time.sleep_ms(blinktime)
        LED(1).off()
        LED(3).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_CYAN_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(2).on()
        LED(3).on()
        time.sleep_ms(blinktime)
        LED(2).off()
        LED(3).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_WHITE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(1).on()
        LED(2).on()
        LED(3).on()
        time.sleep_ms(blinktime)
        LED(1).off()
        LED(2).off()
        LED(3).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
def LED_IR_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        LED(4).on()
        time.sleep_ms(blinktime)
        LED(4).off()
        if ((blinks-i) > 1):
            time.sleep_ms(blinktime)
    return
# ⚊⚊⚊⚊⚊ LED RAINBOW ⚊⚊⚊⚊⚊
def LED_CYCLE(blinktime=1000,blinks=1):
    LED_RED_BLINK(blinktime,blinks)
    LED_GREEN_BLINK(blinktime,blinks)
    LED_BLUE_BLINK(blinktime,blinks)
    LED_YELLOW_BLINK(blinktime,blinks)
    LED_PURPLE_BLINK(blinktime,blinks)
    LED_CYAN_BLINK(blinktime,blinks)
    LED_WHITE_BLINK(blinktime,blinks)
    LED_RGB_OFF()
    return

def led_green(func):
    """
    Decorator to turn on the green LED before and after the function call.
    """
    def wrapper(*args, **kwargs):
        LED_GREEN_ON()
        result = func(*args, **kwargs)
        LED_GREEN_OFF()
        return result
    
    return wrapper

class Illumination:

    def __init__(self, led_night_mode=cfg.LED_NIGHT_MODE):
        self.enabled = False
        self.led_night_mode = led_night_mode
        self.busy_led_start_ticks_ms = time.ticks_ms()
        return

    def on(self, message=""):
        if(self.enabled): return
        self.enabled = True
        print("Turning illumination LEDs ON", message)
        LED_IR_ON()
        return

    def off(self, message=""):
        if(not self.enabled): return
        self.enabled = False
        print("Turning illumination LEDs OFF", message)
        LED_IR_OFF()
        return

    def toggle(self):
        self.off() if self.enabled else self.on()
        
    def is_enabled(self):
        return self.enabled

    def can_turn_on(self, is_night):
        return not self.enabled and is_night \
        and (self.led_night_mode == LedNightMode.ON or self.led_night_mode != LedNightMode.OFF)

    def can_turn_off(self):
        return self.enabled and self.led_night_mode != LedNightMode.ON

    def update(self):
        is_night = not timeutil.is_daytime()
        
        if is_night:
            if self.can_turn_on(is_night):
                self.on("during nighttime")
        else:
            self.off(message="during daytime")

        #blink LED every period
        if (timeutil.elapsed_ticks_ms(self.busy_led_start_ticks_ms) > _BUSY_LED_INTERVAL_MS):
            self.busy_led_start_ticks_ms = time.ticks_ms()
            print("Blinking LED indicator after",str(_BUSY_LED_INTERVAL_MS/1000),"seconds")
            LED_BLUE_BLINK(_BUSY_LED_DURATION_MS)

        
