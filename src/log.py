from logging.handlers import RotatingFileHandler
from threading import ExceptHookArgs
from pathlib import Path
import logging
import traceback
import threading
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Path("log/").mkdir(exist_ok=True)

streamHandlerFormatter = logging.Formatter('%(message)s')
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(streamHandlerFormatter)
logger.addHandler(streamHandler)

fileHandlerFormatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s:%(message)s')
fileHandler = RotatingFileHandler(
    'log/latest.log', mode='a', maxBytes=5242880, backupCount=1, encoding='utf-8')
fileHandler.setFormatter(fileHandlerFormatter)
logger.addHandler(fileHandler)


def printLogException(etype, value, tb):
    formatted_exception = ' '.join(
        traceback.format_exception(etype, value, tb))
    logger.critical(f"Uncaught exception: {formatted_exception}")


def threadingExceptionHandler(e: ExceptHookArgs):
    printLogException(e.exc_type, e.exc_value, e.exc_traceback)


sys.excepthook = printLogException
threading.excepthook = threadingExceptionHandler
