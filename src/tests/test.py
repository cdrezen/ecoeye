### test settings moved to config/settings.py and use_shortcut_mode()
from config.settings import *
MODE = 0
apply_mode(MODE)
from config.settings import *
print(frame_differencing_enabled, classify_mode, operation_time, exposure_mode, delay_loop_s, use_exposure_bracketing, RTC_select, save_roi)

assert (frame_differencing_enabled == False and classify_mode == "none" and operation_time == "24h" and exposure_mode == "auto" 
        and delay_loop_s == 0 and use_exposure_bracketing == False and RTC_select == 'onboard' and save_roi == "none")

MODE = 2
apply_mode(MODE)
from config.settings import *
print(frame_differencing_enabled, classify_mode, operation_time, exposure_mode, delay_loop_s, use_exposure_bracketing, RTC_select, save_roi)
assert save_roi == "all"
###

### test voltage divider
from hardware.voltage_divider import vdiv_build
vbat = vdiv_build()
print(vbat.read_voltage())
if voltage_divider == False:
    assert vbat.read_voltage() == "NA" 
else:
   assert vbat.read_voltage() > 0
###

from hardware.led import *
import time


### test led

### test illumination
sensor.reset()
sensor.set_pixformat(sensor_pixformat)
sensor.set_framesize(sensor_framesize)
illumination = Illumination()
illumination.on()
time.sleep(2)
illumination.off()
time.sleep(2)
illumination.toggle()
time.sleep(2)
illumination.update(True)
time.sleep(2)
illumination.update(False)
time.sleep(2)
illumination.off()

### test timeutil
from timeutil import *

solartime = suntime(operation_time,sunrise_hour,sunrise_minute,sunset_hour,sunset_minute)
rtc = rtc()
# print date and time from set or updated RTC
start = rtc.datetime()[4:7]
print("start date (H,M,S):", start)
time.sleep(2)
end = rtc.datetime()[4:7]
print("end date (H,M,S):", end)
assert start != end
###