import sys
import traceback
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Path("log/").mkdir(exist_ok=True)

fileHandler = RotatingFileHandler('log/latest.log', mode='a', maxBytes=5242880, backupCount=2)
fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s'))
logger.addHandler(fileHandler)

def uncaughtExceptionHandler(etype, value, tb):
    formatted_exception = ' '.join(traceback.format_exception(etype, value, tb))
    print(formatted_exception)
    logger.error(f"Uncaught exception: {formatted_exception}")

sys.excepthook = uncaughtExceptionHandler
