### test settings moved to config/settings.py and use_shortcut_mode()
from config.settings import *
MODE = 0
use_shortcut_mode(MODE)
from config.settings import *
print(fd_enable, classify_mode, operation_time, exposure_control, delay_loop_s, exposure_bracketing, RTC_select, save_roi)

assert (fd_enable == False and classify_mode == "none" and operation_time == "24h" and exposure_control == "auto" 
        and delay_loop_s == 0 and exposure_bracketing == False and RTC_select == 'onboard' and save_roi == "none")

MODE = 2
use_shortcut_mode(MODE)
from config.settings import *
print(fd_enable, classify_mode, operation_time, exposure_control, delay_loop_s, exposure_bracketing, RTC_select, save_roi)
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

### test led

### test timeutil
from timeutil import suntime, rtc
import time

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