import machine, pyb, time
import config.settings as cfg
from config.settings import TimeCoverage

# Time conversion constants
MIN_PER_HOUR = 60
SEC_PER_MIN = 60
MS_PER_SEC = 1000
SEC_PER_HOUR = MIN_PER_HOUR * SEC_PER_MIN
MS_PER_MIN = SEC_PER_MIN * MS_PER_SEC
MS_PER_HOUR = MIN_PER_HOUR * MS_PER_MIN
MS_PER_DAY = 24 * MS_PER_HOUR

HOUR_IDX = 3
MINUTE_IDX = 4
SECONDS_IDX = 5
SUNRISE_MS = cfg.SUNRISE_HOUR * MS_PER_HOUR + cfg.SUNRISE_MINUTE * MS_PER_MIN
SUNSET_MS = cfg.SUNSET_HOUR * MS_PER_HOUR + cfg.SUNSET_MINUTE * MS_PER_MIN

### deprecated ###
class Suntime:

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
###

class Rtc:
    def __init__(self):
        # initialise RTC object
        self.rtc = pyb.RTC()
        # set rtc from user defined date and time only on power on
        if (machine.reset_cause() != machine.DEEPSLEEP_RESET):
            self.rtc.datetime(cfg.START_DATETIME)
        
    def datetime(self):
        return self.rtc.datetime() # returns a tuple (year, month, day, weekday, hours, minutes, seconds, subseconds)

    
rtc = Rtc()

clock = time.clock()

def datetime():
    return rtc.datetime()

def ms_since_midnight():
    """
    Returns the current time in milliseconds since midnight. ingores subseconds (0-255).
    """
    t = datetime()
    return (t[HOUR_IDX] * MS_PER_HOUR) + (t[MINUTE_IDX] * MS_PER_MIN) + (t[SECONDS_IDX] * MS_PER_SEC)

def is_ms_in_daytime(ms):
    """
    Checks if the given time in milliseconds is between sunrise and sunset milliseconds since midnight.
    """
    return SUNRISE_MS <= ms < SUNSET_MS

def is_daytime():
    """
    Checks if the current time is between sunrise and sunset.
    """
    return is_ms_in_daytime(ms_since_midnight())

def is_operation_time():
        #check time operation mode in day/night operation time modes
        return True if cfg.TIME_COVERAGE == TimeCoverage.ALL \
            else is_daytime() if cfg.TIME_COVERAGE == TimeCoverage.DAY \
            else not is_daytime() # if cfg.TIME_COVERAGE == TimeCoverage.NIGHT

def ms_until_sunrise():
    """
    Returns the time until sunrise in milliseconds based on RTC time.
    If it's already daytime, returns 0.
    """

    # Current time in ms since midnight
    current_ms = ms_since_midnight()

    if is_ms_in_daytime(current_ms):
        # Already daytime: no time until sunrise
        return 0

    if current_ms > SUNSET_MS:
        # After sunset => before midnight: time until next day's sunrise
        ms_until_midnight = MS_PER_DAY - current_ms
        return ms_until_midnight + SUNRISE_MS

    # Before sunrise
    return SUNRISE_MS - current_ms

def ms_until_sunset():
    """
    Returns the time until sunset in milliseconds based on RTC time.
    If it's already nighttime, returns 0.
    """
    current_ms = ms_since_midnight()

    if not is_ms_in_daytime(current_ms):
        # Already nighttime: no time until sunset
        return 0
    
    # Between sunrise and sunset
    return SUNSET_MS - current_ms