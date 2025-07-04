import machine, os, pyb, sensor, time
from hardware.led import LED_BLUE_BLINK, LED_RED_BLINK

## To use as main script since it will cause reset:
def deepsleep(sleep_time: int):
    """
    Hibernation to disk or "deep sleep". Resets script upon wakeup.
    Wakeup time is computed before sleep and fetched
    upon wakeup to retrieve time and date. Blinks the the led in red before going to sleep.

    Args:
        sleep_time: time until wakeup in ms. 0 for ongoing sleep, the function will read the wakeup time from disk.
    """
    LED_RED_BLINK(300, 2)

    with open('log.txt', 'a') as log:
        log.write(f"Going to sleep for {sleep_time} ms at (Y,M,D,H,M,S): {time.localtime()[0:6]}\n")

    pyb.RTC().wakeup(sleep_time)
    sensor.sleep(True)
    sensor.shutdown(True)
    pyb.standby()
    return

def on_reset_wakeup():
    with open('log.txt', 'a') as log:
        log.write("Waking up from hibernation\n")
        log.write(f"Wakeup time (Y,M,D,H,M,S): localtime: {time.localtime()[0:6]}\n")

first_run = ("log.txt" not in os.listdir())

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    LED_BLUE_BLINK(300, 2)
    on_reset_wakeup()

if not first_run:
    while True:
        pass

deepsleep(10000)
