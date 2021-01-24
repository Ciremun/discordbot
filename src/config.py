import json
import time
import os
from os.path import join, dirname

from dotenv import load_dotenv

load_dotenv(join(dirname(__name__), '.env'))

keys = {attr: os.environ.get(attr) for attr in [
    'DiscordToken', 'ClientOAuth', 'ClientSecret', 'AppAccessToken', 'callbackURL', 'secret']}
cfg = json.load(open('cfg.json'))
start_time = time.time()