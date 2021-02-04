import os
import time
from random import uniform
from os.path import join, dirname

import requests
from dotenv import load_dotenv

from src.log import logger

load_dotenv(join(dirname(__name__), '.env'))

self_url = os.environ.get('CALLBACK_URL')

while True:
    time.sleep(uniform(15, 25) * 60)
    try:
        requests.get(self_url)
    except Exception as e:
        logger.error(e)