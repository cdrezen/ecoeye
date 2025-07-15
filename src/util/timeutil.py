import machine, pyb, time
import config.settings as cfg
from config.enums import TimeCoverage
from micropython import const

# Time conversion constants
MIN_PER_HOUR:int = const(60)
SEC_PER_MIN:int = const(60)
MS_PER_SEC:int = const(1000)
SEC_PER_HOUR:int = const(MIN_PER_HOUR * SEC_PER_MIN)
MS_PER_MIN:int = const(SEC_PER_MIN * MS_PER_SEC)
MS_PER_HOUR:int = const(MIN_PER_HOUR * MS_PER_MIN)
MS_PER_DAY:int = const(24 * MS_PER_HOUR)

class LTimeIdx:
    """
    Class to hold indices for time.localtime tuple elements.
    This is used to avoid confusion between RTC and localtime indices.
    """
    YEAR:int = const(0)
    MONTH:int = const(1)
    DAY:int = const(2)
    HOURS:int = const(3)
    MINUTES:int = const(4)
    SECONDS:int = const(5)
    WEEKDAY:int = const(6)
    YEARDAY:int = const(7)

class RTCTimeIdx():
    """
    Class to hold indices for RTC.datetime tuple elements.
    This is used to avoid confusion between RTC and localtime indices.
    """
    YEAR:int = const(LTimeIdx.YEAR)
    MONTH:int = const(LTimeIdx.MONTH)
    DAY:int = const(LTimeIdx.DAY)
    HOURS:int = const(LTimeIdx.HOURS + 1)
    MINUTES:int = const(LTimeIdx.MINUTES + 1)
    SECONDS:int = const(LTimeIdx.SECONDS + 1)
    WEEKDAY:int = const(LTimeIdx.WEEKDAY - 3)
    SUBSECONDS:int = const(7)

SUNRISE_MS = cfg.SUNRISE_HOUR * MS_PER_HOUR + cfg.SUNRISE_MINUTE * MS_PER_MIN
SUNSET_MS = cfg.SUNSET_HOUR * MS_PER_HOUR + cfg.SUNSET_MINUTE * MS_PER_MIN

clock = time.clock()

def reset_rtc(datetime: tuple[int, int, int, int, int, int, int, int] = cfg.START_DATETIME):
    pyb.RTC().datetime(datetime)

def datetime():
    """
    returns time.localtime(), a tuple (year, month, mday, hour, minute, second, weekday, yearday)
    """
    # https://forums.openmv.io/t/using-time-localtime-vs-rtc-datetime/11190/2
    return time.localtime()

def localtime_to_rtc_datetime(localtime: tuple[int, int, int, int, int, int, int, int]) -> tuple[int, int, int, int, int, int, int, int]:
    """
    Converts a localtime tuple to an RTC datetime tuple. Loss of yearday value and subseconds set to 0.
    Localtime: (year, month, day, hours, minutes, seconds, weekday, yearday)
    RTC: (year, month, day, weekday, hours, minutes, seconds, subseconds)
    """
    return (
        localtime[LTimeIdx.YEAR],
        localtime[LTimeIdx.MONTH],
        localtime[LTimeIdx.DAY],
        localtime[LTimeIdx.WEEKDAY],
        localtime[LTimeIdx.HOURS],
        localtime[LTimeIdx.MINUTES],
        localtime[LTimeIdx.SECONDS],
        0  # subseconds are ignored
    )

def ms_since_midnight():
    """
    Returns the current time in milliseconds since midnight. ingores subseconds (0-255).
    """
    t = datetime()
    return (t[LTimeIdx.HOURS] * MS_PER_HOUR) + (t[LTimeIdx.MINUTES] * MS_PER_MIN) + (t[LTimeIdx.SECONDS] * MS_PER_SEC)

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