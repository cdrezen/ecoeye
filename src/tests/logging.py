### test session

from logging.session import Session

session = Session().load()
if not session:
    session = Session().create()

assert session is not None

### test file io
from logging.session import *

new_folder_name, imagelog, detectionlog = session.path, session.imagelog, session.detectionlog

os.chdir('/sdcard')
print(os.listdir(), "current directory:", os.getcwd(), "new_folder_name:", new_folder_name)

# original code 
with open(str(new_folder_name)+'/detections1.csv', 'w') as detectionlog1:
        detectionlog1.write("detection_id" + ',' + "picture_id" + ',' + "blob_pixels" + ',' + "blob_elongation" + ','
    + "blob_corner1_x" + ',' + "blob_corner1_y" + ',' + "blob_corner2_x" + ',' + "blob_corner2_y" + ',' + "blob_corner3_x" + ',' + "blob_corner3_y" + ',' + "blob_corner4_x" + ',' + "blob_corner4_y"
    + ',' + "blob_l_mode" + ',' + "blob_l_min" + ',' + "blob_l_max" + ',' + "blob_a_mode" + ',' + "blob_a_min" + ',' + "blob_a_max" + ',' + "blob_b_mode" + ',' + "blob_b_min" + ',' + "blob_b_max" + ','
    + "image_labels" + ',' "image_confidences" + ',' + "image_x" + ',' + "image_y" + ',' + "image_width" + ',' + "image_height" + '\n')

with open(str(new_folder_name)+'/images1.csv', 'w') as imagelog1:
        imagelog1.write("picture_id" + ',' + "date_time" + ',' + "exposure_us" + ',' + "gain_dB" + ',' + "frames_per_second" + ','
        + "image_type" + ',' + "roi_x" + ',' + "roi_y" + ',' + "roi_width" + ',' + "roi_height" + '\n')
#

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
