from hardware.led import *
import sensor
### test led

### test illumination
sensor.reset()
sensor.set_pixformat(cfg.SENSOR_PIXFORMAT)
sensor.set_framesize(cfg.SENSOR_FRAMESIZE)
illumination = Illumination()
illumination.on()
# time.sleep(2)
# illumination.off()
# time.sleep(2)
# illumination.toggle()
# time.sleep(2)
# illumination.update(True)
# time.sleep(2)
# illumination.update(False)
# time.sleep(2)
# illumination.off()
