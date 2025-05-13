from config.settings import frame_differencing_enabled, use_roi, rois_rects, export_blobs
import os, time
import pyb
from logging.csv import Csv

def read_filevars():
    # retrieve current working folder name in VAR
    with open('/VAR/currentfolder.txt', 'r') as folderfetch:
        current_folder = folderfetch.read()
    # retrieve current picture ID in VAR
    with open('/VAR/picturecount.txt', 'r') as countfetch:
        picture_count = eval(countfetch.read())
    # retrieve current detection ID in VAR
    with open('/VAR/detectioncount.txt', 'r') as countfetch:
        detection_count = eval(countfetch.read())
    return current_folder, picture_count, detection_count

# ⚊⚊⚊⚊⚊ save variables ⚊⚊⚊⚊⚊
# save the dynamic variables in the VAR folder
# --- Input arguments ----
# current_folder - name of the current folder
# picture_count - name/number of the current picture
# detection_count - name/number of the current detection
# --- Output variables ---
# none
def write_filevars(current_folder, picture_count, detection_count):
    # create file in VAR folder and write current folder name
    with open('/VAR/currentfolder.txt', 'w') as folderlog:
        folderlog.write(str(current_folder))
    # create file on root and write current picture ID
    with open('/VAR/picturecount.txt', 'w') as countlog:
        countlog.write(str(picture_count))
    # create file on root and write current detection ID
    with open('/VAR/detectioncount.txt', 'w') as countlog:
        countlog.write(str(detection_count))
    return

# ⚊⚊⚊⚊⚊ save status log ⚊⚊⚊⚊⚊
# Save status log
# --- Input arguments ---
# vbat - voltage of batteries
# status - user-defined string describing the status to save in the log
# pathstr - path of the folder, string type
# --- Output variables ---
# none
def write_status(vbat,status="NA",folder='/'):

    print("Saving '",status,"' into status log.")

    adc  = pyb.ADCAll(12)

    if(not 'status.csv' in os.listdir(str(folder))):
        statuslog = Csv(str(folder)+'/status.csv', "date_time", "status", "battery_voltage", 
                        "USB_connected", "core_temperature_C")

    statuslog.append(str("-".join(map(str,time.localtime()[0:6]))), status, str(vbat), 
                    str(pyb.USB_VCP().isconnected()), str(adc.read_core_temp()))
    return

def init_files(rtc):
    
    # if VAR folder doesnt exists,create new VAR folder
    if (not "VAR" in os.listdir()):
        os.mkdir('VAR')

    # Listing root contents to search folders
    foldernames=[name for name in os.listdir() if "." not in name]
    new_folder_number=len(foldernames)-1 #(-1 to not count VAR folder)

    #create folder for new deployment to avoid overwriting images
    folder_created=False
    date = rtc.datetime()
    # format from date (YYYY-M-D and HH-MM-SS)
    date_part = f"{date[0]}-{date[1]}-{date[2]}_{date[4]}-{date[5]}-{date[6]}"
    new_folder_name = f"{new_folder_number} {date_part}"

    while (new_folder_name in foldernames):
        new_folder_name = f"{new_folder_number} {date_part}"
        new_folder_number += 1 # assumes no overflow because of the changing date
 
    os.mkdir(str(new_folder_name))
    print("Created new deployment folder:", new_folder_name)

    filenames = os.listdir(str(new_folder_name))

    if(not 'detections.csv' in filenames):
        detectionlog = Csv(new_folder_name+'/detections.csv', "detection_id", "picture_id", 
                        "blob_pixels", "blob_elongation", 
                        "blob_corner1_x", "blob_corner1_y", "blob_corner2_x", "blob_corner2_y", 
                        "blob_corner3_x","blob_corner3_y", "blob_corner4_x", "blob_corner4_y", 
                        "blob_l_mode", "blob_l_min", "blob_l_max", 
                        "blob_a_mode", "blob_a_min", "blob_a_max", 
                        "blob_b_mode", "blob_b_min",  "blob_b_max", 
                        "image_labels", "image_confidences", 
                        "image_x", "image_y", "image_width", "image_height")

    if(not 'images.csv' in filenames):
        imagelog = Csv(new_folder_name+'/images.csv', "picture_id", "date_time", 
                    "exposure_us", "gain_dB", "frames_per_second", "image_type", 
                    "roi_x", "roi_y", "roi_width", "roi_height")

    #make jpeg, reference image and ROI directories if needed
    if (not "jpegs" in filenames): 
        os.mkdir(str(new_folder_name)+"/jpegs")

    filenames = os.listdir(str(new_folder_name)+"/jpegs")

    if (frame_differencing_enabled and not "reference" in filenames): 
        os.mkdir(str(new_folder_name)+"/jpegs/reference")
    
    if (export_blobs!="none" and not "blobs" in filenames): 
        os.mkdir(str(new_folder_name)+"/jpegs/blobs")

    for roi_temp in rois_rects:
        subfolder_name = '_'.join(map(str,roi_temp))
        if (not subfolder_name in filenames): 
            os.mkdir(str(new_folder_name)+"/jpegs/"+subfolder_name)
            print("Created ROI",subfolder_name,"subfolder.")

    ### tests ###

    # name1 = "-".join(map(str,list(date[i] for i in [0,1,2])))+"_"+"-".join(map(str,list(date[i] for i in [4,5,6])))
    # assert new_folder_name == name1

    return new_folder_name
