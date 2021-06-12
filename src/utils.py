import asyncio
from math import floor
from datetime import datetime
from typing import Callable

import requests

import src.db as db
from .log import logger
from .config import keys


def exponentBackoff(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        for exponent in range(1, 6):
            try:
                if await func(*args, **kwargs):
                    return
                raise Exception
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(5 ** exponent)
    wrapper.__name__ = func.__name__
    return wrapper


def new_timecode_explicit(days, hours, minutes, seconds, duration) -> str:
    if duration < 1:
        return f'{floor(duration * 1000)}ms'
    timecode = []
    timecode_dict = {'d': days, 'h': hours, 'm': minutes, 's': seconds}
    for k, v in timecode_dict.items():
        if v:
            timecode.append(f'{v}{k}')
    return " ".join(timecode)


def seconds_convert(duration):
    init_duration = duration
    days = duration // (24 * 3600)
    duration = duration % (24 * 3600)
    hours = duration // 3600
    duration %= 3600
    minutes = duration // 60
    seconds = duration % 60
    days, hours, minutes, seconds = [
        floor(x) for x in [days, hours, minutes, seconds]]
    return new_timecode_explicit(days, hours, minutes, seconds, init_duration)


def convert_utc_to_epoch(utc_time: str) -> float:
    utc_time = datetime.strptime(utc_time, '%Y-%m-%dT%H:%M:%SZ')
    return (utc_time - datetime(1970, 1, 1)).total_seconds()


def hex3_to_hex6(hex_color: str) -> str:
    hex6 = '#'
    for h in hex_color.lstrip('#'):
        hex6 += f'{h}{h}'
    return hex6


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return '#%02x%02x%02x' % (r, g, b)


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))


def is_mod(message) -> bool:
    return any(message.author.id == i for i in db.getModlist())


async def validateAppAccessToken():
    response = requests.get('https://id.twitch.tv/oauth2/validate',
                            headers={'Authorization': f'OAuth {keys["APP_ACCESS_TOKEN"]}'}).json()
    if keys['CLIENT_ID'] != response.get('client_id'):
        logger.warning('invalid APP_ACCESS_TOKEN, generating a new one')
        response = requests.post(f'https://id.twitch.tv/oauth2/token?'
                                 f'client_id={keys["CLIENT_ID"]}&'
                                 f'client_secret={keys["CLIENT_SECRET"]}&'
                                 f'grant_type=client_credentials').json()
        keys['APP_ACCESS_TOKEN'] = response['access_token']
        logger.info(f'new APP_ACCESS_TOKEN - {keys["APP_ACCESS_TOKEN"]}')


@exponentBackoff
async def webhookStreamsRequest(username, mode, *, userid=None):
    if userid is None:
        response = requests.get(f'https://api.twitch.tv/helix/users?login={username}',
                                headers={'Client-ID': keys["CLIENT_ID"],
                                         'Authorization': f'Bearer {keys["CLIENT_OAUTH"]}'}).json()
        userid = response['data'][0]['id']
        logger.info(f'user id: {userid}')
        db.addNotifyUserID(username, userid)
    await validateAppAccessToken()
    r = requests.post('https://api.twitch.tv/helix/webhooks/hub',
                      headers={'Client-ID': keys["CLIENT_ID"],
                               'Authorization': f'Bearer {keys["APP_ACCESS_TOKEN"]}'
                               },
                      data={
                          'hub.callback': f'{keys["CALLBACK_URL"]}?u={username}',
                          'hub.mode': mode,
                          'hub.topic': f'https://api.twitch.tv/helix/streams?user_id={userid}',
                          'hub.lease_seconds': 863000,
                          'hub.secret': keys["SECRET"]
                      })
    logger.info(f'webhookStreamsRequest status: {r.status_code}: {r.text}')
    if r.content:
        logger.warning(f'r.content in webhookStreamsRequest:\n{r.content}')
        return
    return True


async def updateWebhooks():
    while True:
        for username, userdata in db.get_streams().items():
            await webhookStreamsRequest(username, 'subscribe', userid=userdata['userid'])
        await asyncio.sleep(860000)
