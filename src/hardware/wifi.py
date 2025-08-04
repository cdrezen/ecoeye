import network, requests
from machine import Pin, Timer
from hardware.led import *

### WIFI & upload functions ###
# from orignial ecofunctions.py


# - wifi shield check -
# check if wifi shield is connected
# --- Input arguments ---
# none
# --- Output variables ---
# wifishield - wifi shield is connected boolean
def wifishield_isconnnected():
    wlan = None
    try:
        wlan = network.WINC()
    except OSError:
        pass

    #checking object content
    if wlan:
        print("WiFi shield installed")
        wifishield = True
    else:
        print("No WiFi shield installed")
        wifishield = False
    # reset ADC pin P6
    Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
    return wifishield

# ⚊⚊⚊⚊⚊ connect to wifi ⚊⚊⚊⚊⚊
# connect to WiFi
# --- Indicators ---
# CYAN while trying to connect to WiFi
# BLUE while connected to WiFi
# CYAN blink 100ms when connection failed
# --- Input arguments ---
# ssid - WiFi name
# key - WiFi password
# --- Output variables ---
# wifi_connected - wifi is connected boolean
def wifi_connect(ssid,key):
    # create a winc driver object and connect to WiFi shield
    wlan = network.WINC()
    print("Connecting to WiFi")
    # LED cyan color while connecting to wifi
    LED_CYAN_ON()
    # connect to WiFi, timeout is hardcoded to 2 seconds
    wlan.connect(ssid, key, security=wlan.WPA_PSK)
    if (wlan.isconnected()):
        wifi_connected = True
        print("Succesfully connected to WiFi")
        # LED blue color while connected to wifi
        LED_CYAN_OFF()
        LED_BLUE_ON()
        # print the IP adresses and Signal strength
        print(wlan.ifconfig())
    else:
        wifi_connected = False
        print("WiFi Connection failed")
        LED_CYAN_BLINK(100,2)
    return wifi_connected

# ⚊⚊⚊⚊⚊ Function description ⚊⚊⚊⚊⚊
# disconnect from WiFi
# --- Input arguments ---
# none
# --- Indicators ---
# BLUE turns off
# --- Output variables ---
# none
def wifi_disconnect():
    network.WINC().disconnect()
    print("Disconnected from WiFi")
    LED_BLUE_OFF()
    # reset ADC pin P6
    Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
    return

# ⚊⚊⚊⚊⚊ send data over wifi ⚊⚊⚊⚊⚊
# transfer json data to server
# --- Indicators ---
# BLUE blink when data was sent
# RED blink when data sending failed
# --- Input arguments ---
# url - server upload link, with API if necessary
# data1 - data for first field
# data2 - optional, data for second field
# data3 - optional, data for third field
# data4 - optional, data for fourth field
# --- Output variables ---
# data_transferred - data was transferred boolean
def data_transfer(url, data1, data2=None, data3=None, data4=None):
    headers = {'Content-Type': 'application/json'}
    if (data2 is None and data3 is None and data4 is None):
        data = {'field1':str(data1)}
    elif (data3 is None and data4 is None):
        data = {'field1':str(data1),'field2':str(data2)}
    elif (data4 is None):
        data = {'field1':str(data1),'field2':str(data2),'field3':str(data3)}
    else:
        data = {'field1':str(data1),'field2':str(data2),'field3':str(data3),'field4':str(data4)}

    print("Sending data to server")
    try:
        request_data = requests.post(url, json=data, headers=headers)
        LED_BLUE_BLINK(300,2)
        print("Data sucessfully sent")
        data_transferred = True
    except:
        print("Data send failed")
        #print(request_data.status_code, request_data.reason)
        LED_BLUE_OFF()
        LED_RED_BLINK(300,2)
        LED_BLUE_ON()
        data_transferred = False
    return data_transferred

# ⚊⚊⚊⚊⚊ send image over wifi ⚊⚊⚊⚊⚊
# transfer image file to server
# --- Indictors ---
# BLUE blink when data was sent
# RED blink when data sending failed
# --- Input arguments ---
# url - server upload link, with API if necessary
# img1 - image file to be posted
# --- Output variables ---
# file_transferred - file was transferred boolean
def image_transfer(url, img1):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
    files = {'imageFile': ("img.jpg", open(img1, "rb"))}
    # send the file
    print("Sending file to server")
    try:
        request_image = requests.post(url, files=files, headers=headers)
        LED_BLUE_BLINK(300,2)
        # print some post request parameters
        print("Image sent to Server")
        file_transferred = True
    except Exception as e:
        print("File send failed")
        print(e)
        #print(request_image.status_code, request_image.reason)
        LED_BLUE_OFF()
        LED_RED_BLINK(300,2)
        LED_BLUE_ON()
        file_transferred = False
    return file_transferred
