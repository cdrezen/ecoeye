
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