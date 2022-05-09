import logging
import os

DEBUG = True
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(filename="sample.log", level=logging.INFO)
LOG = logging.getLogger("ex")


TIC_TIMEOUT = 0.1
SECONDS_IN_YEAR = 1.5
START_YEAR = 1957
GUN_YEAR = 1970


ANIMATION_FOLDER = 'files'
SPACESHIP_VEL_MUL_ROW = 10
SPACESHIP_VEL_MUL_COL = 10

