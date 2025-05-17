import config.settings as cfg
import os, time
import pyb
import json
from logging.csv import Csv
from logging.detection_logger import DetectionLogger
from logging.image_logger import ImageLogger


class Session:
    """
    A class to handle session management, including file operations and logging.
    """

    DATA_FOLDER = 'DATA'
    SESSION_FILENAME = 'session.json'
    DETECTIONLOG_FILENAME = 'detections.csv'
    IMAGELOG_FILENAME = 'images.csv'
    STATUSLOG_FILENAME = 'status.csv'

    def __init__(self, path, detectionlog, imagelog, statuslog):
        self.path = path
        self.detectionlog = detectionlog
        self.imagelog = imagelog
        self.statuslog = statuslog

    def create(self, rtc):
        """
        Create a new session and initialize the necessary files and folders.
        """
        if (not self.DATA_FOLDER in os.listdir()):
            os.mkdir(self.DATA_FOLDER)

        os.chdir(self.DATA_FOLDER)
        
        self.path = f"{self.DATA_FOLDER}/{self._find_new_folder_name(rtc)}"
    
        os.mkdir(str(self.path))
        os.chdir(str(self.path))
        print("Created new deployment folder:", self.path)

        filenames = os.listdir()

        self.detectionlog = DetectionLogger(self.DETECTIONLOG_FILENAME, 0)
        self.imagelog = ImageLogger(self.IMAGELOG_FILENAME, 0)
        self.statuslog = Csv(self.STATUSLOG_FILENAME, "date_time", "status", "battery_voltage", 
                            "USB_connected", "core_temperature_C")

        #make jpeg, reference image and ROI directories if needed
        if (not "jpegs" in filenames): 
            os.mkdir("jpegs")

        filenames = os.listdir("jpegs")

        if (cfg.FRAME_DIFF_ENABLED and not "reference" in filenames): 
            os.mkdir("jpegs/reference")
        
        if (cfg.BLOBS_EXPORT_METHOD!="none" and not "blobs" in filenames): 
            os.mkdir("jpegs/blobs")

        for roi_temp in cfg.ROI_RECTS:
            subfolder_name = '_'.join(map(str,roi_temp))
            if (not subfolder_name in filenames): 
                os.mkdir("jpegs/"+subfolder_name)
                print("Created ROI",subfolder_name,"subfolder.")
 
        self.save()
        return self(self.path, self.detectionlog, self.imagelog, self.statuslog)
    
    def _find_new_folder_name(self, rtc):
        """
        Find the new folder name based on the current date and time and current folders count.
        """
        # Listing root contents to search folders
        foldernames=[name for name in os.listdir() if "." not in name]
        new_folder_number=len(foldernames)

        #create folder for new deployment to avoid overwriting images
        date = rtc.datetime()
        # format from date (YYYY-M-D and HH-MM-SS)
        date_part = f"{date[0]}-{date[1]}-{date[2]}_{date[4]}-{date[5]}-{date[6]}"
        new_folder_name = f"{new_folder_number} {date_part}"

        while (new_folder_name in foldernames):
            new_folder_name = f"{new_folder_number} {date_part}"
            new_folder_number += 1 # assumes no overflow because of the changing date

        return new_folder_name

    def load(self):
        """
        Load the current session data from json file
        """
        # Check if the session file exists

        if self.SESSION_FILENAME in os.listdir('/'):
            with open(f'/{self.SESSION_FILENAME}', 'r') as file:
                data = json.load(file)
                self.path = data['path']
                detection_count = data['detection_count']
                picture_count = data['picture_count']
                ### ....
            
            os.chdir(self.path)
            self.detectionlog = DetectionLogger(self.DETECTIONLOG_FILENAME, detection_count)
            self.imagelog = ImageLogger(self.IMAGELOG_FILENAME, picture_count)
            self.statuslog = Csv(self.STATUSLOG_FILENAME, "date_time", "status", "battery_voltage", 
                                "USB_connected", "core_temperature_C")
            
            return self(self.path, self.detectionlog, self.imagelog, self.statuslog)
        
        return None

    def save(self):
        """
        Save the current session data to json file
        """
        data = {
            'path': self.path,
            'picture_count': self.imagelog.picture_count,
            'detection_count': self.detectionlog.detection_count
        }

        try:

            with open(f'/{self.SESSION_FILENAME}', 'w') as file:
                json.dump(data, file)

        except Exception as e:
            print(f"Error saving session data: {e}")
            return False
        
        return True


    def log_status(self, vbat, status="NA"):

        adc  = pyb.ADCAll(12)

        date = str("-".join(map(str,time.localtime()[0:6])))
        usb_connected = str(pyb.USB_VCP().isconnected())
        core_temperature_C = str(adc.read_core_temp())

        print(f"Status: [datetime: {date}, status: {status}, voltage: {vbat}, USB_connected: {usb_connected}, core_temperature_C: {core_temperature_C}]")

        self.statuslog.append(date, status, vbat, usb_connected, core_temperature_C)
        return
