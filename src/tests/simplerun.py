from main import App
from util import timeutil
from config import settings as cfg
from config.enums import ML_Mode

NB_RUN = 10

app = App()

for i in range(NB_RUN):
    app.update()
