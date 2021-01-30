import json
import time
import os
from os.path import join, dirname

from dotenv import load_dotenv

load_dotenv(join(dirname(__name__), '.env'))

keys = {attr: os.environ.get(attr) for attr in ['CLIENT_ID', 'DISCORD_TOKEN', 'CLIENT_OAUTH', 'CLIENT_SECRET', 'APP_ACCESS_TOKEN', 'CALLBACK_URL', 'SECRET']}
cfg = json.load(open('cfg.json'))
start_time = time.time()