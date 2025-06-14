import config.settings as cfg

from hardware.led import *
import hardware.power as hpw

import time


### test led

### test illumination
sensor.reset()
sensor.set_pixformat(cfg.SENSOR_PIXFORMAT)
sensor.set_framesize(cfg.SENSOR_FRAMESIZE)
illumination = Illumination()
illumination.on()
# time.sleep(2)
# illumination.off()
# time.sleep(2)
# illumination.toggle()
# time.sleep(2)
# illumination.update(True)
# time.sleep(2)
# illumination.update(False)
# time.sleep(2)
# illumination.off()

### test timeutil
from util.timeutil import *

solartime = Suntime(cfg.TIME_COVERAGE, cfg.SUNRISE_HOUR, cfg.SUNRISE_MINUTE, cfg.SUNSET_HOUR, cfg.SUNSET_MINUTE)
rtc = Rtc()
# print date and time from set or updated RTC
start = rtc.datetime()[4:7]
print("start date (H,M,S):", start)
time.sleep(2)
end = rtc.datetime()[4:7]
print("end date (H,M,S):", end)
assert start != end

### test session

from logging.session import *

session = Session().load()
if not session:
    session = Session().create(rtc)

assert session is not None

### test voltage divider
pw = hpw.PowerManagement(illumination, session)
print(pw.get_battery_voltage())
if cfg.VOLTAGE_DIV_AVAILABLE == False:
    assert pw.get_battery_voltage() == "NA" 
else:
   assert pw.get_battery_voltage() > 0

pw.sleep_if_low_bat(solartime, "test")
###`

### test file
from logging.session import *

new_folder_name, imagelog, detectionlog = session.path, session.imagelog, session.detectionlog

os.chdir('/sdcard')
print(os.listdir(), "current directory:", os.getcwd(), "new_folder_name:", new_folder_name)

with open(str(new_folder_name)+'/detections1.csv', 'w') as detectionlog1:
        detectionlog1.write("detection_id" + ',' + "picture_id" + ',' + "blob_pixels" + ',' + "blob_elongation" + ','
    + "blob_corner1_x" + ',' + "blob_corner1_y" + ',' + "blob_corner2_x" + ',' + "blob_corner2_y" + ',' + "blob_corner3_x" + ',' + "blob_corner3_y" + ',' + "blob_corner4_x" + ',' + "blob_corner4_y"
    + ',' + "blob_l_mode" + ',' + "blob_l_min" + ',' + "blob_l_max" + ',' + "blob_a_mode" + ',' + "blob_a_min" + ',' + "blob_a_max" + ',' + "blob_b_mode" + ',' + "blob_b_min" + ',' + "blob_b_max" + ','
    + "image_labels" + ',' "image_confidences" + ',' + "image_x" + ',' + "image_y" + ',' + "image_width" + ',' + "image_height" + '\n')

with open(str(new_folder_name)+'/images1.csv', 'w') as imagelog1:
        imagelog1.write("picture_id" + ',' + "date_time" + ',' + "exposure_us" + ',' + "gain_dB" + ',' + "frames_per_second" + ','
        + "image_type" + ',' + "roi_x" + ',' + "roi_y" + ',' + "roi_width" + ',' + "roi_height" + '\n')

with open(str(new_folder_name)+'/detections.csv', 'r') as log:
    log_lines = log.readlines()
    print("log_lines", log_lines)

with open(str(new_folder_name)+'/detections1.csv', 'r') as log:
    log1_lines = log.readlines()
    print("log1_lines", log1_lines)

assert log_lines == log1_lines

csv_test = Csv(new_folder_name+'/detections2.csv', "detection_id", "picture_id",
                "blob_pixels", "blob_elongation", 
                "blob_corner1_x", "blob_corner1_y", "blob_corner2_x", "blob_corner2_y", 
                "blob_corner3_x","blob_corner3_y", "blob_corner4_x", "blob_corner4_y", 
                "blob_l_mode", "blob_l_min", "blob_l_max", 
                "blob_a_mode", "blob_a_min", "blob_a_max", 
                "blob_b_mode", "blob_b_min",  "blob_b_max", 
                "image_labels", "image_confidences", 
                "image_x", "image_y", "image_width", "image_height")

log1_content = [line.strip().split(',') for line in log1_lines]
print("log1_content", log1_content)
print(csv_test.read())
assert csv_test.read() == log1_content

with open(str(new_folder_name)+'/images.csv', 'r') as log:
    log_lines = log.readlines()
    print("log_lines", log_lines)

with open(str(new_folder_name)+'/images1.csv', 'r') as log:
    log1_lines = log.readlines()
    print("log1_lines", log1_lines)

assert log_lines == log1_lines

###