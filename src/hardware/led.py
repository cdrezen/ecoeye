### LED FUNCTIONS ###
import pyb
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

class illumination:
    
    def __init__(self):
        
        return

    def on(self):
        
        return

    def off(self):

        return
        
    def off_cooldown(self):
        
        return