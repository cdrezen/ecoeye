### VOLTAGE DIVIDER ###
from logging.session import Session
import pyb, time, machine, sensor, os, math
from pyb import Pin, Timer
from hardware.led import LED_YELLOW_ON, LED_YELLOW_OFF, LED_RED_BLINK, Illumination

import config.settings as cfg
from config.settings import TimeCoverage
from util import timeutil
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

    def __init__(self, illumination: Illumination, session: Session|None = None, enabled=cfg.POWER_MANAGEMENT_ENABLED):
        
        self.enabled = enabled
        self.illumination = illumination
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
            deepsleep(timeutil.ms_until_sunrise() + PowerManagement.AFTER_SUNRISE_DELAY)
        else:
            print("Battery voltage is sufficient.")

        is_night = not timeutil.is_daytime()
        if(self.illumination.can_turn_on(is_night)):
            self.illumination.on(message="after voltage reading")

    def sleep_if_not_operation_time(self):
        """
        Put the system to sleep if it is not within the operation time.
        """
        if(not timeutil.is_operation_time()):
            print("Outside operation time - current time:",timeutil.datetime()[0:6])
            self.illumination.off(message="before deep sleep")     
            #compute time until wake-up
            if (cfg.TIME_COVERAGE == TimeCoverage.DAY):
                sleep_time = timeutil.ms_until_sunrise()
            elif (cfg.TIME_COVERAGE == TimeCoverage.NIGHT):
                sleep_time = timeutil.ms_until_sunset()
            self.session.save()
            self.session.log_status(self.get_battery_voltage(), "Outside operation time - Sleeping")
            deepsleep(sleep_time)
        
    def update(self):
        """
        Update the power management state.
        """

        self.sleep_if_not_operation_time()

        #check battery voltage (if possible) and log status every period
        if (pyb.elapsed_millis(self.start_time_check_battery) > cfg.CHECK_BAT_PERIOD_MS):
            self.start_time_check_battery = pyb.millis()
            datetime = timeutil.datetime()
            print_status=f"Script running - timed check (Y,M,D) {datetime[0:3]} - (H,M,S) {datetime[4:7]}"
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
                deepsleep(cfg.PICTURE_DELAY_MS)
                self.sleep_if_low_bat("Delay loop - Waking")

class SleepVar:
    """
    Class to handle file variables for hibernation.
    """

    def __init__(self, path):
        self.path = path
        
    def read(self):
        """
        Read the sleep variable from the file.
        """
        with open(self.path, 'r') as file:
            val = eval(file.read())
        return val
    
    def write(self, val):
        """
        Write the sleep variable to the file.
        """
        with open(self.path, 'w') as file:
            file.write(str(val))
        return val
    
END_EPOCH_PATH = '/sdcard/dsleepend.txt'
WAKEUP_EPOCH_PATH = '/sdcard/dsleepwakeup.txt'
SLEEP_BLINK_MS = 200
SLEEP_NB_BLINK = 2

def deepsleep(sleep_time: int):
    """
    Hibernation to disk or "deep sleep". Resets script upon wakeup. 
    Wakeup time is computed before sleep and fetched 
    upon wakeup to retrieve time and date. Blinks the the led in red before going to sleep.

    Args: 
        sleep_time: time until wakeup in ms. 0 for ongoing sleep, the function will read the wakeup time from disk.
    """
    end_epoch_filevar = SleepVar(END_EPOCH_PATH)
    wakeup_epoch_filevar = SleepVar(WAKEUP_EPOCH_PATH)
    
    # create deep sleep end time file on the initial sleep time call of tthis function
    if(sleep_time > 0):
        print(f"Going to deep sleep for {sleep_time} ms")
        LED_RED_BLINK(SLEEP_BLINK_MS, SLEEP_NB_BLINK)
        # compute deep sleep end time in epoch seconds and write it to disk as string
        end_epoch = time.mktime(time.localtime()) + math.floor(sleep_time / timeutil.MS_PER_SEC)
        end_epoch_filevar.write(end_epoch)
    else:
        # get wakeup time from file
        end_epoch = end_epoch_filevar.read()

    # compute deep sleep wakeup time in epoch seconds
    wakeup_epoch = time.mktime(time.localtime()) + math.floor(cfg.DEEPSLEEP_DEFAULT_INTERVAL_MS / timeutil.MS_PER_SEC)
    # make sure sleep doesnt surpass the sleep end time
    if(wakeup_epoch > end_epoch):
        nap_time = (end_epoch - time.mktime(time.localtime()))*timeutil.MS_PER_SEC
        wakeup_epoch = end_epoch
    else:
        nap_time = cfg.DEEPSLEEP_DEFAULT_INTERVAL_MS

    # create deep sleep wakeup file and write deep sleep wakeup epoch
    wakeup_epoch_filevar.write(wakeup_epoch)

    # schedule wakeup and hibernate
    pyb.RTC().wakeup(math.floor(nap_time/timeutil.MS_PER_SEC)*timeutil.MS_PER_SEC)
    sensor.sleep(True)
    sensor.shutdown(True)
    pyb.standby()
    return

def on_reset_wakeup():
    print("Waking up from hibernation")
    # get wakeup time from file

    end_epoch = SleepVar(END_EPOCH_PATH).read()
    wakeup_epoch = SleepVar(END_EPOCH_PATH).read()

    # get current supposed time and convert to rtc tuple
    wakeup_localtime = time.localtime(wakeup_epoch)
    print(f"Wakeup time: {wakeup_localtime[0:6]} (Y,M,D,H,M,S)\n localtime: {time.localtime()[0:6]}")
    rtc_time = timeutil.localtime_to_rtc_datetime(wakeup_localtime)
    # update RTC time
    pyb.RTC().datetime(rtc_time)

    # check if end time has not been reached
    if(wakeup_epoch < end_epoch):
        # hibernate with wakeup time previously stored in file
        deepsleep(0)


