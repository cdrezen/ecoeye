import config.settings as cfg
from hardware import power
from tests.illumination import illumination
from tests.logging import session

### test voltage divider
pw = power.PowerManagement(illumination, session)
print(pw.get_battery_voltage())
if cfg.VOLTAGE_DIV_AVAILABLE == False:
    assert pw.get_battery_voltage() == -1 
else:
   assert pw.get_battery_voltage() > 0

pw.sleep_if_low_bat()
###`
