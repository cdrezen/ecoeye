### VOLTAGE DIVIDER ###
import pyb
from pyb import Pin, Timer, ExtInt
from hardware.led import LED_YELLOW_ON, LED_YELLOW_OFF

from config.settings import PMS, LED_module, voltage_divider, voltage_readings, voltage_readings_delay, vbat_minimum
# resistors values on voltage divider circuits
R_1_PMS_LED = 30
R_2_PMS_LED = 8.82352941176
R_1_PMS_noLED = 30
R_2_PMS_noLED = 100
R_1_noPMS_LED = 2.88
R_2_noPMS_LED = 9.67741935484
R_1_noPMS_noLED = 200
R_2_noPMS_noLED = 680

### VOLTAGE DIVIDER READING CLASS
class vdiv:

    def __init__(self, vdiv_en, nread, dread, R_1, R_2):
        self.vdiv_en = vdiv_en
        self.nread = nread
        self.dread = dread
        self.R_1 = R_1
        self.R_2 = R_2

    # ⚊⚊⚊⚊⚊ ADC voltage reading ⚊⚊⚊⚊⚊
    # Read ADC voltage
    # ---- Indicators ---
    # YELLOW while adc measuring
    # --- Input arguments ---
    # voltage divider parameters
    # --- Output variables ---
    # adc_voltage - ADC value converted into volts
    def read_voltage(self):
        #check voltage
        if (self.vdiv_en):
            # adc pin needs to be defined after wifi shield used it
            adc = pyb.ADC(pyb.Pin('P6'))
            #  yellow LED during measure
            LED_YELLOW_ON()
            # read adc value and convert into volts
            voltage = 0
            # create and set high the volatge divider enable pin
            ADCEN = Pin('P1', pyb.Pin.OUT_PP)
            ADCEN.high()
            for i in range(self.nread):
                pyb.delay(self.dread)
                voltage = voltage + (adc.read() * (3.3/4095) *(1+self.R_1/self.R_2))
            # disconnect voltage divider from ADC pin
            ADCEN.low()
            adc_voltage = voltage/self.nread
            LED_YELLOW_OFF()
            # print the adc voltage on terminal
            if(pyb.USB_VCP().isconnected()):
                print("USB supply voltage: %f V" % adc_voltage) # read value, 0-4095+
            else : print("Battery voltage: %f V" % adc_voltage) # read value, 0-4095+
            #re-assign pin to something neutral with low frequency
            Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
        else:
            adc_voltage="NA"
        return adc_voltage

    def is_battery_low():
        vbat = vdiv.read_voltage()
        return (vbat!="NA" and vbat<vbat_minimum and not pyb.USB_VCP().isconnected())

def is_battery_low(vbat):
    return (vbat!="NA" and vbat<vbat_minimum and not pyb.USB_VCP().isconnected())

def vdiv_build():
    # set the resistor values in ADC voltage divider
    if PMS:
        R_1 = R_1_PMS_LED if LED_module else R_1_PMS_noLED
        R_2 = R_2_PMS_LED if LED_module else R_2_PMS_noLED
    else:
        R_1 = R_1_noPMS_LED if LED_module else R_1_noPMS_noLED
        R_2 = R_2_noPMS_LED if LED_module else R_2_noPMS_noLED
    # return voltage divider class instance
    return vdiv(voltage_divider, voltage_readings, voltage_readings_delay, R_1,R_2)

