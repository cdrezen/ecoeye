### LED FUNCTIONS ###
import pyb
from pyb import Pin, Timer
import sensor
import config.settings as cfg

# ⚊⚊⚊⚊⚊ LED ON ⚊⚊⚊⚊⚊
def LED_RED_ON():
    LED_RGB_OFF()
    pyb.LED(1).on()
    return
def LED_GREEN_ON():
    LED_RGB_OFF()
    pyb.LED(2).on()
    return
def LED_BLUE_ON():
    LED_RGB_OFF()
    pyb.LED(3).on()
    return
def LED_YELLOW_ON():
    LED_RGB_OFF()
    pyb.LED(1).on()
    pyb.LED(2).on()
    return
def LED_PURPLE_ON():
    LED_RGB_OFF()
    pyb.LED(1).on()
    pyb.LED(3).on()
    return
def LED_CYAN_ON():
    LED_RGB_OFF()
    pyb.LED(2).on()
    pyb.LED(3).on()
    return
def LED_WHITE_ON():
    LED_RGB_OFF()
    pyb.LED(1).on()
    pyb.LED(2).on()
    pyb.LED(3).on()
    return
def LED_IR_ON():
    LED_RGB_OFF()
    pyb.LED(4).on()
    return
# ⚊⚊⚊⚊⚊ LED OFF ⚊⚊⚊⚊⚊
def LED_RED_OFF():
    pyb.LED(1).off()
    return
def LED_GREEN_OFF():
    pyb.LED(2).off()
    return
def LED_BLUE_OFF():
    pyb.LED(3).off()
    return
def LED_YELLOW_OFF():
    pyb.LED(1).off()
    pyb.LED(2).off()
    return
def LED_PURPLE_OFF():
    pyb.LED(1).off()
    pyb.LED(3).off()
    return
def LED_CYAN_OFF():
    pyb.LED(2).off()
    pyb.LED(3).off()
    return
def LED_WHITE_OFF():
    pyb.LED(1).off()
    pyb.LED(2).off()
    pyb.LED(3).off()
    return
def LED_IR_OFF():
    pyb.LED(4).off()
    return
def LED_RGB_OFF():
    pyb.LED(1).off()
    pyb.LED(2).off()
    pyb.LED(3).off()
    return
# ⚊⚊⚊⚊⚊ LED TOGGLE ⚊⚊⚊⚊⚊
def LED_RED_TOGGLE():
    pyb.LED(2).off()
    pyb.LED(3).off()
    pyb.LED(1).toggle()
    return
def LED_GREEN_TOGGLE():
    pyb.LED(1).off()
    pyb.LED(3).off()
    pyb.LED(2).toggle()
    return
def LED_BLUE_TOGGLE():
    pyb.LED(1).off()
    pyb.LED(2).off()
    pyb.LED(3).toggle()
    return
def LED_YELLOW_TOGGLE():
    pyb.LED(3).off()
    pyb.LED(1).toggle()
    pyb.LED(2).toggle()
    return
def LED_PURPLE_TOGGLE():
    pyb.LED(2).off()
    pyb.LED(1).toggle()
    pyb.LED(3).toggle()
    return
def LED_CYAN_TOGGLE():
    pyb.LED(1).off()
    pyb.LED(4).off()
    pyb.LED(3).toggle()
    return
def LED_WHITE_TOGGLE():
    pyb.LED(1).toggle()
    pyb.LED(2).toggle()
    pyb.LED(3).toggle()
    return
def LED_IR_TOGGLE():
    pyb.LED(4).toggle()
    return
def LED_ALL_TOGGLE():
    pyb.LED(1).toggle()
    pyb.LED(2).toggle()
    pyb.LED(3).toggle()
    pyb.LED(4).toggle()
    return
# ⚊⚊⚊⚊⚊ LED BLINK ⚊⚊⚊⚊⚊
def LED_RED_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(1).on()
        pyb.delay(blinktime)
        pyb.LED(1).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_GREEN_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(2).on()
        pyb.delay(blinktime)
        pyb.LED(2).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_BLUE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(3).on()
        pyb.delay(blinktime)
        pyb.LED(3).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_YELLOW_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(1).on()
        pyb.LED(2).on()
        pyb.delay(blinktime)
        pyb.LED(1).off()
        pyb.LED(2).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_PURPLE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(1).on()
        pyb.LED(3).on()
        pyb.delay(blinktime)
        pyb.LED(1).off()
        pyb.LED(3).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_CYAN_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(2).on()
        pyb.LED(3).on()
        pyb.delay(blinktime)
        pyb.LED(2).off()
        pyb.LED(3).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_WHITE_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(1).on()
        pyb.LED(2).on()
        pyb.LED(3).on()
        pyb.delay(blinktime)
        pyb.LED(1).off()
        pyb.LED(2).off()
        pyb.LED(3).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
    return
def LED_IR_BLINK(blinktime=1000,blinks=1):
    LED_RGB_OFF()
    for i in range(blinks):
        pyb.LED(4).on()
        pyb.delay(blinktime)
        pyb.LED(4).off()
        if ((blinks-i) > 1):
            pyb.delay(blinktime)
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

class Illumination:

    def __init__(self, mode=cfg.LED_MODE, led_night_mode=cfg.LED_NIGHT_MODE, brightness=cfg.LED_MODULE_BRIGHTNESS_PWM, warmup_ms=cfg.LED_MODULE_WARMUP_MS, cooldown_ms=cfg.LED_MODULE_COOLDOWN_MS):
        self.light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
        self.enabled = False
        self.mode = mode
        self.led_night_mode = led_night_mode
        self.brightness = brightness
        self.warmup_ms = warmup_ms
        self.cooldown_ms = cooldown_ms
        return

    def on(self, message=""):
        if(self.enabled): return
        self.enabled = True
        print("Turning illumination LEDs ON", message)
        if(self.mode == 'module'):
            print("Warming up LED module for",self.warmup_ms/1000,"seconds.")
            self.light.pulse_width_percent(self.brightness)
            sensor.skip_frames(time = self.warmup_ms)
        elif(self.mode == 'onboard'):
            LED_IR_ON()
        return

    def off(self, no_cooldown=False, message=""):
        if(not self.enabled): return
        self.enabled = False
        print("Turning illumination LEDs OFF", message)
        if(self.mode == 'module'):
            self.light.pulse_width_percent(0)
            if(no_cooldown): return
            print("Letting LED module cool down for",self.cooldown_ms,"seconds.")
            pyb.delay(self.cooldown_ms)
        elif(self.mode == 'onboard'):
            LED_IR_OFF()
        return

    def toggle(self, no_cooldown=False):
        self.off(no_cooldown) if self.enabled else self.on()
        
    def is_enabled(self):
        return self.enabled

    def can_turn_on(self, is_night):
        return not self.enabled and is_night and (self.led_night_mode == "on" or self.led_night_mode != 'off')

    def can_turn_off(self):
        return self.enabled and self.led_night_mode != 'on'

    def update(self, is_night):
        if is_night:
            if self.can_turn_on(is_night):
                self.on("during nighttime")
                
        else:
            self.off(message="during daytime")
