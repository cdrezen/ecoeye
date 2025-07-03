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

clock = time.clock()

def reset_rtc(datetime: tuple[int, int, int, int, int, int, int, int] = cfg.START_DATETIME):
    pyb.RTC().datetime(datetime)

### TODO: move to appropriate module or class
# set rtc from user defined date and time only on power on
if (machine.reset_cause() != machine.DEEPSLEEP_RESET):
    reset_rtc()
###

def datetime():
    # returns a tuple (year, month, day, weekday, hours, minutes, seconds, subseconds)
    # https://forums.openmv.io/t/using-time-localtime-vs-rtc-datetime/11190/2
    return time.localtime()

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