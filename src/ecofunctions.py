import machine, pyb, time, sensor, os, math
from hardware.led import *

# DEEP SLEEP w/ indicators
# go to deep sleep, resets script upon wakeup
# wakeup time is computed before sleep and fetched
# upon wakeup to retrieve time and date
# --- Indicators ---
# RED blink 500ms when going to sleep
# BLUE active_LED_duration_ms every active_LED_interval_ms
# --- Input arguments ---
# sleep_time - time until wakeup in ms
# active_LED_interval_ms - time between indicator signal in ms
# --- Output variables ---
# none
def indicator_dsleep(sleep_time):
    # create deep sleep end time file on the initial sleep time call of tthis function
    if(sleep_time > 0):
        # print and blink deep sleep time
        print("Going to deep sleep for ", sleep_time/60000," minutes")
        LED_RED_BLINK(200,2)
        # compute deep sleep end time in epoch seconds
        dsleep_end_epoch = time.mktime(time.localtime()) + math.floor(sleep_time/1000)
        # create deep sleep end file and write epoch seconds as string
        with open('/sdcard/VAR/dsleepend.txt', 'w') as timelog:
            timelog.write(str(dsleep_end_epoch))
    else:
        # get wakeup time from file
        with open('/sdcard/VAR/dsleepend.txt', 'r') as timefetch:
            dsleep_end_epoch = eval(timefetch.read())

    # compute deep sleep interval wakeup time in epoch seconds
    dsleep_wakeup_epoch = time.mktime(time.localtime()) + math.floor(cfg.DEEPSLEEP_DEFAULT_DURATUION_MS/1000)
    # make sure sleep doesnt surpass the sleep end time
    if(dsleep_wakeup_epoch > dsleep_end_epoch):
        nap_time = (dsleep_end_epoch - time.mktime(time.localtime()))*1000
        dsleep_wakeup_epoch = dsleep_end_epoch
    else:
        nap_time = cfg.DEEPSLEEP_DEFAULT_DURATUION_MS

    # create deep sleep wakeup file and write deep sleep wakeup epoch
    with open('/sdcard/VAR/dsleepwakeup.txt', 'w') as timelog:
        timelog.write(str(dsleep_wakeup_epoch))
    # define sleep time and go
    pyb.RTC().wakeup(math.floor(nap_time/1000)*1000)
    # put camera into sleep and shut it down
    sensor.sleep(True)
    sensor.shutdown(True)
    pyb.standby()
    # camera is init on wakeup
    return

# ⚊⚊⚊⚊⚊ script start check ⚊⚊⚊⚊⚊
# for deep sleep script start
# --- Input arguments ---
# none
# --- Output variables ---
# none
def start_check():
    # get the board reset cause
    if (machine.reset_cause() == machine.DEEPSLEEP_RESET):
        print("Starting script from DEEP SLEEP")
        # get wakeup time from file
        with open('/sdcard/VAR/dsleepwakeup.txt', 'r') as timefetch:
            dsleep_wakeup_epoch = eval(timefetch.read())
        # check if woke up from indicator sleep, i.e. if dsleepend file exists
        if('dsleepend.txt' in os.listdir('VAR')):
            with open('/sdcard/VAR/dsleepend.txt', 'r') as timefetch:
                dsleep_end_epoch = eval(timefetch.read())

        # epoch seconds to time tuple to rtc tuple
        dsleep_wakeup_time = time.localtime(dsleep_wakeup_epoch)
        dsleep_wakeup_rtc = (dsleep_wakeup_time[0], dsleep_wakeup_time[1], dsleep_wakeup_time[2], 1, dsleep_wakeup_time[3], dsleep_wakeup_time[4], dsleep_wakeup_time[5], 0)
        # initialise and update RTC
        pyb.RTC().datetime(dsleep_wakeup_rtc)

        # check if end time has not been reached
        if(dsleep_wakeup_epoch < dsleep_end_epoch):
            # indicator LED : the white firmware is used as the indicator now
            #LED_BLUE_BLINK(500,1)
            # sleep time is zero for interval sleep, indicator is 60s hardcoded
            indicator_dsleep(0)
    else:
        print("Starting script from POWER ON")
    return


