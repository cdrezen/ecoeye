### VOLTAGE DIVIDER ###
from ecofunctions import indicator_dsleep
from logging.session import Session
import pyb, time
from pyb import Pin, Timer, ExtInt
from hardware.led import LED_YELLOW_ON, LED_YELLOW_OFF, Illumination

import config.settings as cfg
from util.timeutil import Rtc, Suntime

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
class Battery:

    def __init__(self, R_1, R_2, vdiv_available=cfg.VOLTAGE_DIV_AVAILABLE, nb_read=cfg.VOLTAGE_AVG_SAMPLE_COUNT, read_delay=cfg.VOLTAGE_READINGS_DELAY_MS):
        """
        Initialize the Battery class with voltage divider parameters.
        
        Args:
            R_1: Resistance of R1 in the voltage divider
            R_2: Resistance of R2 in the voltage divider
            vdiv_available: Flag indicating if the voltage divider is available
            nb_read: Number of readings to average
            read_delay: Delay between readings in milliseconds
        """
        self.R_1 = R_1
        self.R_2 = R_2
        self.vdiv_available = vdiv_available
        self.nb_read = nb_read
        self.read_delay = read_delay

    # ⚊⚊⚊⚊⚊ ADC voltage reading ⚊⚊⚊⚊⚊
    # Read ADC voltage
    # ---- Indicators ---
    # YELLOW while adc measuring
    # --- Input arguments ---
    # voltage divider parameters
    # --- Output variables ---
    # adc_voltage - ADC value converted into volts
    def read_voltage(self):
        if (not self.vdiv_available):
            return -1
        # adc pin needs to be defined after wifi shield used it
        adc = pyb.ADC(pyb.Pin('P6'))
        #  yellow LED during measure
        LED_YELLOW_ON()
        # read adc value and convert into volts
        voltage = 0
        # create and set high the volatge divider enable pin
        ADCEN = Pin('P1', pyb.Pin.OUT_PP)
        ADCEN.high()
        for i in range(self.nb_read):
            pyb.delay(self.read_delay)
            voltage = voltage + (adc.read() * (3.3/4095) *(1+self.R_1/self.R_2))
        # disconnect voltage divider from ADC pin
        ADCEN.low()
        adc_voltage = voltage/self.nb_read
        LED_YELLOW_OFF()
        # print the adc voltage on terminal
        if(pyb.USB_VCP().isconnected()):
            print("USB supply voltage: %f V" % adc_voltage) # read value, 0-4095+
        else : print("Battery voltage: %f V" % adc_voltage) # read value, 0-4095+
        #re-assign pin to something neutral with low frequency
        Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
            
        return adc_voltage

    def is_low(self, v=None):
        if v is None:
            v = self.read_voltage()
        return (v!=-1 and v < cfg.VBAT_MINIMUM_VOLT and not pyb.USB_VCP().isconnected())

class PowerManagement:
    """
    Power management class to handle power-saving features and battery monitoring.
    """

    BATTERY_LOW_STR = "Battery low - Sleeping"
    AFTER_SUNRISE_DELAY = 30*60*1000 # 30 minutes

    def __init__(self, illumination: Illumination, suntime: Suntime, rtc: Rtc, session: Session|None = None, enabled=cfg.POWER_MANAGEMENT_ENABLED):
        
        self.enabled = enabled
        self.illumination = illumination
        self.suntime = suntime
        self.rtc = rtc
        self.session = session
        if self.enabled:
            r1 = R_1_PMS_LED if cfg.LED_MODULE_AVAILABLE else R_1_PMS_noLED
            r2 = R_2_PMS_LED if cfg.LED_MODULE_AVAILABLE else R_2_PMS_noLED
        else:
            r1 = R_1_noPMS_LED if cfg.LED_MODULE_AVAILABLE else R_1_noPMS_noLED
            r2 = R_2_noPMS_LED if cfg.LED_MODULE_AVAILABLE else R_2_noPMS_noLED
        self.battery = Battery(r1, r2)
        self.start_time_check_battery = pyb.millis()

    def get_battery_voltage(self):
       return self.battery.read_voltage()

    def sleep_if_low_bat(self, print_status=""):
        """
        Put the system to sleep if the battery voltage is below the minimum threshold.
        """
        if print_status:
            print("Checking battery:", print_status)
        
        self.illumination.off(message="during voltage reading")
        v = self.battery.read_voltage()

        if self.battery.is_low(v):
            print(v, PowerManagement.BATTERY_LOW_STR)
            if self.session: 
                self.session.save()
                self.session.log_status(v, PowerManagement.BATTERY_LOW_STR)
            indicator_dsleep(self.suntime.time_until_sunrise() + PowerManagement.AFTER_SUNRISE_DELAY, cfg.ACTIVE_LED_INTERVAL_MS)
        else:
            print("Battery voltage is sufficient.")

        is_night = not self.suntime.is_daytime()
        if(self.illumination.can_turn_on(is_night)):
            self.illumination.on(message="after voltage reading")

    def sleep_if_not_operation_time(self):
        """
        Put the system to sleep if it is not within the operation time.
        """
        if(not self.suntime.is_operation_time()):
            print("Outside operation time - current time:",time.localtime()[0:6])
            self.illumination.off(message="before deep sleep")     
            #compute time until wake-up
            if (cfg.TIME_COVERAGE == "day"):
                sleep_time = self.suntime.time_until_sunrise()
            elif (cfg.TIME_COVERAGE == "night"):
                sleep_time = self.suntime.time_until_sunset()
            self.session.save()
            self.session.log_status(self.get_battery_voltage(), "Outside operation time - Sleeping")
            indicator_dsleep(sleep_time, cfg.ACTIVE_LED_INTERVAL_MS)
        
    def update(self):
        """
        Update the power management state.
        """

        self.sleep_if_not_operation_time()

        #check battery voltage (if possible) and log status every period
        if (pyb.elapsed_millis(self.start_time_check_battery) > cfg.CHECK_BAT_PERIOD_MS):
            self.start_time_check_battery = pyb.millis()
            print_status=f"Script running - timed check (Y,M,D) {self.rtc.datetime()[0:3]} - (H,M,S) {self.rtc.datetime()[4:7]}"
            self.sleep_if_low_bat(print_status)

         ### delay to decrease frame rate: ###
        if (cfg.PICTURE_DELAY_MS):
            if (not cfg.USE_DSLEEP_PIC_DELAY):
                print("Delaying frame capture for", cfg.PICTURE_DELAY_MS, "seconds...")
                pyb.delay(cfg.PICTURE_DELAY_MS)   
            else:
                self.illumination.off(no_cooldown=True, message="before deep sleep")
                self.session.save()
                self.session.log_status(self.get_battery_voltage(), "Delay loop - Sleeping")
                # go to sleep until next picture with blinking indicator
                indicator_dsleep(cfg.PICTURE_DELAY_MS, cfg.ACTIVE_LED_INTERVAL_MS)
                self.sleep_if_low_bat("Delay loop - Waking")

