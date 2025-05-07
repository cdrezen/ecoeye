import machine, pyb, time
from config.settings import RTC_select, current_date_time
### Sunrise and sunset class ###
class suntime:

    def __init__(self, op_t, sr_h, sr_m, ss_h, ss_m):
        self.op_t = op_t
        self.sr_h = sr_h
        self.sr_m = sr_m
        self.ss_h = ss_h
        self.ss_m = ss_m

    # ⚊⚊⚊⚊⚊ daytime check ⚊⚊⚊⚊⚊
    # checks if its daytime or nightime
    # --- Input arguments ---
    # sunrise and sunset times
    # --- Output variables ---
    # daytime - boolean whever its day or not
    def is_daytime(self):
        # get current time in milliseconds
        nowms = ((time.localtime()[3]*60+time.localtime()[4])*60+time.localtime()[5])*1000
        # now is daytime
        if ( nowms >= (self.sr_h*60+self.sr_m)*60*1000 and nowms < (self.ss_h*60+self.ss_m)*60*1000 ):
            daytime = True
        else:
            daytime = False
        return daytime

    # ⚊⚊⚊⚊⚊ Time until sunrise ⚊⚊⚊⚊⚊
    # calculates time until sunrise
    # --- Input arguments ---
    # sunrise and sunset times
    # --- Output variables ---
    # time_to_sunrise - in milliseconds
    def time_until_sunrise(self):
        # get current time in milliseconds
        nowms = ((time.localtime()[3]*60+time.localtime()[4])*60+time.localtime()[5])*1000
        daytime = self.is_daytime()
        if (daytime):
            time_to_sunrise = 0
        else:
            # get ms until sunrise
            # calculation for before midnight
            if(nowms >= (self.ss_h*60+self.ss_m)*60*1000 ):
                time_to_sunrise = (24*60+self.sr_h*60+self.sr_m)*60*1000 - nowms
            # calculation for after midnight
            else:
                time_to_sunrise = (self.sr_h*60+self.sr_m)*60*1000 - nowms
        return time_to_sunrise

    # ⚊⚊⚊⚊⚊ Time until sunset ⚊⚊⚊⚊⚊
    # calculate time until sunset
    # --- Input arguments ---
    # sunrise and sunset times
    # --- Output variables ---
    # time_to_sunset - in milliseconds
    def time_until_sunset(self):
        # get current time in milliseconds
        nowms = ((time.localtime()[3]*60+time.localtime()[4])*60+time.localtime()[5])*1000
        daytime = self.is_daytime()
        if (daytime):
            time_to_sunset = (self.ss_h*60+self.ss_m)*60*1000 - nowms
        else:
            time_to_sunset = 0
        return time_to_sunset

    # ⚊⚊⚊⚊⚊ operation time check ⚊⚊⚊⚊⚊
    # check if operation time
    # --- Input arguments ---
    # sunrise and sunset times
    # operationt time string
    # --- Output variables ---
    # operation_time_check - boolean
    def is_operation_time(self):
        #check time operation mode in day/night operation time modes
        night_time_check = not self.is_daytime()
        if(self.op_t=="day"):
            operation_time_check = not night_time_check
        if(self.op_t=="night"):
            operation_time_check = night_time_check
        if(self.op_t=="24h"):
            operation_time_check = True
        return operation_time_check


class rtc:
    def __init__(self):
        # initialise RTC object
        self.pyb_rtc = pyb.RTC()
        # set rtc from user definedc date and time only on power on
        if (machine.reset_cause() != machine.DEEPSLEEP_RESET and RTC_select == 'onboard'):
            self.pyb_rtc.datetime(current_date_time)
        if(RTC_select == 'ds3231'):
            # import necessary librairies
            from ds3231 import DS3231
            # initialize i2c pins on P7 (SCL) and P8 (SDA) and DS3231 as ext_rtc
            i2c = machine.SoftI2C(sda=pyb.Pin('P8'), scl=pyb.Pin('P7'))
            ext_rtc = DS3231(i2c)
            ext_rtc.get_time(True)
        if(RTC_select == 'pcf8563'):
            # import necessary librairies
            from pcf8563 import PCF8563
            # initialize i2c pins on P4 (SCL) and P5 (SDA) and PCF8563 as ext_rtc
            i2c = machine.SoftI2C(sda=pyb.Pin('P5'), scl=pyb.Pin('P4'))
            ext_rtc = PCF8563(i2c)
            ext_rtc.get_time(True)
        
    def datetime(self):
        return self.pyb_rtc.datetime()
