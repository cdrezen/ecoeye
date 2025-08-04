### VOLTAGE DIVIDER ###
from logging.session import Session
import time, machine
from machine import Pin, Timer, ADC
from hardware.led import LED_YELLOW_ON, LED_YELLOW_OFF, Illumination
import config.settings as cfg
from config.enums import TimeCoverage
from util import timeutil
from micropython import const

#how many voltage readings to average over to obtain the value that will be logged
VOLTAGE_AVG_SAMPLE_COUNT = const(10)
#how much delay between voltage readings (in milliseconds)
VOLTAGE_READINGS_DELAY_MS = const(10)
#minimum voltage for image sensor operation. theoretically, when voltage is below 2.7 V, the image sensor stops working
VBAT_MINIMUM_VOLT = const(0)
#how often to check the battery
CHECK_BAT_PERIOD_MS = const(10*60*1000) 
#threshold of PICTURE_DELAY_S above which the camera goes to sleep between pictures to save power. Below that threshold, the camera will stay on and simply wait
USE_DSLEEP_THRESHOLD = const(10000)

# resistors values on voltage divider circuits
R_1_PMS_NOLED = const(30)
R_2_PMS_NOLED = const(100)
R_1_NOPMS_NOLED = const(200)
R_2_NOPMS_NOLED = const(680)
VOLT_CONV_MULT = 3.3/65535 # voltage on the pin, 3.3V / 16-bit ADC, 0-65535

### VOLTAGE DIVIDER READING CLASS
class Battery:

    def __init__(self, r1, r2, vdiv_available=cfg.VOLTAGE_DIV_AVAILABLE, nb_read=VOLTAGE_AVG_SAMPLE_COUNT, read_delay=VOLTAGE_READINGS_DELAY_MS):
        """
        Initialize the Battery class with voltage divider parameters.
        
        Args:
            r1: Resistance of r1 in the voltage divider
            r1: Resistance of r2 in the voltage divider
            vdiv_available: Flag indicating if the voltage divider is available
            nb_read: Number of readings to average
            read_delay: Delay between readings in milliseconds
        """
        self.r1 = r1
        self.r2 = r2
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
        adc = ADC(Pin('P6'))
        #  yellow LED during measure
        LED_YELLOW_ON()
        # read adc value and convert into volts
        voltage = 0
        # create and set high the volatge divider enable pin
        adcen = Pin('P1', Pin.OUT)
        adcen.high()
        for i in range(self.nb_read):
            time.sleep_ms(self.read_delay)
            voltage = voltage + (adc.read_u16() * VOLT_CONV_MULT *(1+self.r1/self.r2))
        # disconnect voltage divider from ADC pin
        adcen.low()
        adc_voltage = voltage/self.nb_read
        LED_YELLOW_OFF()
        
        print("Voltage: %f V" % adc_voltage) # read value, 0-65535
        
        # re-assign pin to something neutral with low frequency
        # Timer(-1, freq=50000).channel(1, Timer.PWM, pin=Pin("P6")).pulse_width_percent(0)
            
        return adc_voltage

    def is_low(self, v=None):
        if v is None:
            v = self.read_voltage()
        return (v!=-1 and v < VBAT_MINIMUM_VOLT)# and not pyb.USB_VCP().isconnected())

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
        r1 = R_1_PMS_NOLED if self.enabled else R_1_NOPMS_NOLED
        r2 = R_2_PMS_NOLED if self.enabled else R_2_NOPMS_NOLED
        self.battery = Battery(r1, r2)
        self.check_battery_start_ticks_ms = time.ticks_ms()

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
        if (timeutil.elapsed_ticks_ms(self.check_battery_start_ticks_ms) > CHECK_BAT_PERIOD_MS):
            self.check_battery_start_ticks_ms = time.ticks_ms()
            datetime = timeutil.datetime()
            print_status=f"Script running - timed check (Y,M,D) {datetime[0:3]} - (H,M,S) {datetime[4:7]}"
            self.sleep_if_low_bat(print_status)

         ### delay to decrease frame rate: ###
        if (cfg.PICTURE_DELAY_MS):
            if (cfg.PICTURE_DELAY_MS < USE_DSLEEP_THRESHOLD):
                print("Delaying frame capture for", cfg.PICTURE_DELAY_MS, "seconds...")
                time.sleep_ms(cfg.PICTURE_DELAY_MS)   
            else:
                self.illumination.off(no_cooldown=True, message="before deep sleep")
                self.session.save()
                self.session.log_status(self.get_battery_voltage(), "Delay loop - Sleeping")
                # go to sleep until next picture with blinking indicator
                deepsleep(cfg.PICTURE_DELAY_MS)
                self.sleep_if_low_bat("Delay loop - Waking")

SLEEP_BLINK_MS = 200
SLEEP_NB_BLINK = 2

def deepsleep(sleep_time: int):
    """
    Shut almost everything down and wakeup with rtc timeout, aka. "deep sleep". Resets script upon wakeup. 
    Blinks the the led in red before going to sleep.

    Args: 
        sleep_time: time until wakeup in ms.
    """

    print(f"Going to deep sleep for {sleep_time} ms at (Y,M,D,H,M,S): {timeutil.datetime()[0:6]}")
    # schedule wakeup and hibernate
    machine.deepsleep(sleep_time)
    return

def on_reset_wakeup():
    print(f"Waking up at: {timeutil.datetime()[0:6]} (Y,M,D,H,M,S)")


