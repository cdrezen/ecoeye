import os, sys

running_on_camera = False

print(os.environ['HOME'])

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)
if(not running_on_camera):
    # allow imports such as "sensor" in linux
    headers_path = os.path.join(os.environ['HOME'], ".config/OpenMV/openmvide/micropython-headers/")
    sys.path.append(headers_path)

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
if(running_on_camera):
    from hardware.voltage_divider import vdiv_build
    vdiv_build()
###

### test led