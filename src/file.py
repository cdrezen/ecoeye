from config.settings import fd_enable, use_roi, rois, export_blobs
import os, time

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
        with open(str(folder)+'/status.csv', 'a') as statuslog:
            statuslog.write("date_time" + ',' + "status" + ',' + "battery_voltage" + ',' + "USB_connected" + ',' + "core_temperature_C" + '\n')
    with open(str(folder)+'/status.csv', 'a') as statuslog:
        statuslog.write(str("-".join(map(str,time.localtime()[0:6])))+ ',' + status + ',' + str(vbat) + ',' + str(pyb.USB_VCP().isconnected()) + ',' + str(adc.read_core_temp()) + '\n')
    return

def init_files():
        # if VAR folder doesnt exists,create new VAR folder
    if (not "VAR" in os.listdir()):
        os.mkdir('VAR')

    # Listing root contents to search folders
    files_jpegs_folder=os.listdir()
    folders=[files_jpegs_folder for files_jpegs_folder in files_jpegs_folder if "." not in files_jpegs_folder]
    if(len(folders)>0):
        folder_number=len(folders)
    else: folder_number=0
    #incrementing folder number (-1 because VAR folder)
    new_folder_number=int(folder_number)-1

    #create folder for new deployment to avoid overwriting images
    folder_created=False
    folder_time = rtc.datetime()
    while (not folder_created):
        try:
            current_folder=str(new_folder_number)+" "+"-".join(map(str,list(folder_time[i] for i in [0,1,2])))+"_"+"-".join(map(str,list(folder_time[i] for i in [4,5,6])))
            os.mkdir(str(current_folder))
            print("Created new deployment folder: "+str(current_folder))
            folder_created=True
        except:
            #increment by 1 if folder already exists, until it doesn't
            new_folder_number=new_folder_number+1

    # Create detection files
    if(not 'detections.csv' in os.listdir(str(current_folder))):
            with open(str(current_folder)+'/detections.csv', 'a') as detectionlog:
                detectionlog.write("detection_id" + ',' + "picture_id" + ',' + "blob_pixels" + ',' + "blob_elongation" + ','
          + "blob_corner1_x" + ',' + "blob_corner1_y" + ',' + "blob_corner2_x" + ',' + "blob_corner2_y" + ',' + "blob_corner3_x" + ',' + "blob_corner3_y" + ',' + "blob_corner4_x" + ',' + "blob_corner4_y"
          + ',' + "blob_l_mode" + ',' + "blob_l_min" + ',' + "blob_l_max" + ',' + "blob_a_mode" + ',' + "blob_a_min" + ',' + "blob_a_max" + ',' + "blob_b_mode" + ',' + "blob_b_min" + ',' + "blob_b_max" + ','
          + "image_labels" + ',' "image_confidences" + ',' + "image_x" + ',' + "image_y" + ',' + "image_width" + ',' + "image_height" + '\n')
    if(not 'images.csv' in os.listdir(str(current_folder))):
        with open(str(current_folder)+'/images.csv', 'a') as imagelog:
            imagelog.write("picture_id" + ',' + "date_time" + ',' + "exposure_us" + ',' + "gain_dB" + ',' + "frames_per_second" + ','
            + "image_type" + ',' + "roi_x" + ',' + "roi_y" + ',' + "roi_width" + ',' + "roi_height" + '\n')
    #make jpeg, reference image and ROI directories if needed
    if (not "jpegs" in os.listdir(str(current_folder))): os.mkdir(str(current_folder)+"/jpegs")
    if (fd_enable and not "reference" in os.listdir(str(current_folder)+"/jpegs")): os.mkdir(str(current_folder)+"/jpegs/reference")
    if (export_blobs!="none" and not "blobs" in os.listdir(str(current_folder)+"/jpegs")): os.mkdir(str(current_folder)+"/jpegs/blobs")
    if use_roi:
        for roi_temp in rois:
            if not '_'.join(map(str,roi_temp)) in os.listdir(str(current_folder)+"/jpegs"): os.mkdir(str(current_folder)+"/jpegs/"+'_'.join(map(str,roi_temp)))
            print("Created",'_'.join(map(str,roi_temp)),"subfolder(s)")