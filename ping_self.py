import os
import time
from random import uniform
from os.path import join, dirname

import requests
from dotenv import load_dotenv

load_dotenv(join(dirname(__name__), '.env'))

self_url = os.environ.get('CALLBACK_URL')

while True:
    time.sleep(uniform(5, 10) * 60)
    requests.get(self_url)