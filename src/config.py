import time
import os
from os.path import join, dirname

from dotenv import load_dotenv

cfg = {
    "prefix": "!",
    "rolesLimit": 100,
    "notify": True,
    "FlaskAppPort": 80,
    "embedHex6": "#6441a5",
    "footerText": "ayaya"
}

load_dotenv(join(dirname(__name__), '.env'))

keys = {attr: os.environ.get(attr) for attr in [
    'CLIENT_ID', 'DISCORD_TOKEN', 'CLIENT_OAUTH', 'CLIENT_SECRET', 'APP_ACCESS_TOKEN', 'CALLBACK_URL', 'SECRET']}

start_time = time.time()
