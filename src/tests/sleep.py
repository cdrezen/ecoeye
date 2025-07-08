import machine, os, time
from hardware.led import LED_BLUE_BLINK, LED_RED_BLINK
from hardware import power
from util import timeutil

## To use as "main.py" script as its depending on "reset" mechanism

SLEEP_TIME = 10000  # Sleep time in milliseconds
SLEEP_TIME_SEC = SLEEP_TIME / timeutil.MS_PER_SEC
ACC_TOLERANCE_SEC = 1 # Tolerance for sleep time accuracy in seconds

first_run = ("start" not in os.listdir())

if first_run:
    LED_RED_BLINK(300, 2)

    with open('log.txt', 'a') as log:
        log.write(f"Going to sleep for {SLEEP_TIME} ms at (Y,M,D,H,M,S): {time.localtime()[0:6]}\n")

    start_time_sec = time.time()
    with open('start', 'w') as f:
        f.write(str(start_time_sec))

    power.deepsleep(SLEEP_TIME)

elif machine.reset_cause() == machine.DEEPSLEEP_RESET:

    end_time_sec = time.time()

    LED_BLUE_BLINK(300, 2)

    with open('start', 'r') as f:
        start_time_sec = int(f.read())

    sleep_sec = end_time_sec - start_time_sec

    with open('log.txt', 'a') as log:
        log.write(f"Wakeup time (Y,M,D,H,M,S): localtime: {time.localtime()[0:6]}, slept for {sleep_sec} seconds\n")

    assert SLEEP_TIME_SEC - ACC_TOLERANCE_SEC <= sleep_sec >= SLEEP_TIME_SEC + ACC_TOLERANCE_SEC, "Sleep time mismatch"


else:
    while True:
        pass

