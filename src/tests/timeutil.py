### test timeutil
from util import timeutil
import pyb
from config import settings as cfg


# rtc datetime tuples for testing obvious night datetimes and edge cases around sunrise and sunset.
# rtc tuple:        (year,     month,      day,    weekday,    hours,              minutes,                    seconds,    subseconds)
NIGHT_DATES =      [(2025,     6,          30,     0,          2,                  0,                          0,          0),
                    (2025,     7,          1,      1,          cfg.SUNRISE_HOUR,   cfg.SUNRISE_MINUTE - 1,     59,         0),
                    (2025,     7,          1,      1,          cfg.SUNSET_HOUR,    cfg.SUNSET_MINUTE,          1,          0)]

DAY_DATES =        [(2025,     7,          1,      1,          12,                 0,                          0,          0),
                    (2025,     7,          1,      1,          cfg.SUNSET_HOUR,    cfg.SUNSET_MINUTE - 1,      59,         0),
                    (2025,     7,          1,      1,          cfg.SUNRISE_HOUR,   cfg.SUNRISE_MINUTE,         1,          0)]

MIDNIGHT =          (2025,     6,          30,     0,          0,                  0,                          0,          0)
MIDNIGHT_EDGE_MAX = (2025,     6,          30,     0,         23,                 59,                         59,          0)
MIDNIGHT_EDGE_LOW = (2025,     6,          30,     0,          0,                  0,                          1,          0)


def test_ms_since_midnight():
    """
    Test if the milliseconds since midnight are correctly calculated.
    """
    # set the RTC to midnight
    pyb.RTC().datetime(MIDNIGHT)

    assert timeutil.ms_since_midnight() == 0

    pyb.RTC().datetime(MIDNIGHT_EDGE_LOW)

    assert timeutil.ms_since_midnight() == timeutil.MS_PER_SEC

    pyb.RTC().datetime(MIDNIGHT_EDGE_MAX)

    assert timeutil.ms_since_midnight() == timeutil.MS_PER_DAY - timeutil.MS_PER_SEC

def test_date(date, day_expected: bool):
    """
    Test if the current date is correctly identified as night or day.
    """

    day_night_str = "day" if day_expected else "night"
    
    # set the RTC to the test date
    pyb.RTC().datetime(date)

    assert timeutil.is_daytime() == day_expected
    assert timeutil.ms_until_sunrise() == 0 if day_expected else timeutil.ms_until_sunrise() > 0
    assert timeutil.ms_until_sunset() > 0 if day_expected else timeutil.ms_until_sunset() == 0
    
# save current date
original_date = pyb.RTC().datetime()

test_ms_since_midnight()

for date in DAY_DATES:
    test_date(date, day_expected=True)

for date in NIGHT_DATES:
    test_date(date, day_expected=False)


# set rtc date back to original date (assume processing time is negligible)
pyb.RTC().datetime(original_date)