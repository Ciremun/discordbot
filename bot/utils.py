import hmac
import requests
import logging
import discord
import time
import random
import asyncio
import globals as g

from decorators import exponentBackoff
from database import db
from math import floor
from datetime import datetime


streams = {}

def new_timecode_explicit(days, hours, minutes, seconds, duration):
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
    days, hours, minutes, seconds = [floor(x) for x in [days, hours, minutes, seconds]]
    return new_timecode_explicit(days, hours, minutes, seconds, init_duration)


def convert_utc_to_epoch(utc_time: str) -> float:
    utc_time = datetime.strptime(utc_time, '%Y-%m-%dT%H:%M:%SZ')
    return (utc_time - datetime(1970, 1, 1)).total_seconds()


def hex3_to_hex6(hex_color: str):
    hex6 = '#'
    for h in hex_color.lstrip('#'):
        hex6 += f'{h}{h}'
    return hex6


def rgb_to_hex(r: int, g: int, b: int):
    return '#%02x%02x%02x' % (r, g, b)


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))


def is_mod(message):
    return any(message.author.id == i for i in db.getModlist())


def discordEmbed(channel_info: dict):
    """
    get discord.Embed for stream notification
    :param channel_info: twitch api get_streams data dictionary
    :return: discord.Embed
    """
    embed = discord.Embed(title=f'{channel_info["title"]}',
                          url=f'https://twitch.tv/{channel_info["user_name"]}', color=int(g.cfg['embedHex6'][1:], 16))
    embed.add_field(name='Playing', value=f'{channel_info["game"]}')
    embed.add_field(name='Stream started',
                    value=f'{seconds_convert(time.time() - convert_utc_to_epoch(channel_info["started_at"]))} ago')
    embed.set_footer(text='hehe xd')
    random_emote_id = randomGuildEmote(random.choice([guild.id for guild in g.client.guilds])).get("id", None)
    if random_emote_id:
        embed.set_image(url=f'https://cdn.discordapp.com/emojis/{random_emote_id}.png')
    return embed


def randomGuildEmote(guild_id: int):
    """
    get random discord server emote as a dictionary
    :param guild_id: discord guild id to fetch emotes
    :return: dict
    """
    guild_emotes_list = [{'name': x.name,
                          'id': x.id} for x in g.client.get_guild(guild_id).emojis if not x.animated and x.available]
    if guild_emotes_list:
        return random.choice(guild_emotes_list)
    return {}


async def validateAppAccessToken():
    response = requests.get('https://id.twitch.tv/oauth2/validate', 
                                headers={'Authorization': f'OAuth {g.tokens["AppAccessToken"]}'}).json()
    if not g.tokens['Client-ID'] == response.get('client_id'):
        print('invalid AppAccessToken, generating a new one')
        response = requests.post(f'https://id.twitch.tv/oauth2/token?'
                                          f'client_id={g.tokens["Client-ID"]}&'
                                          f'client_secret={g.tokens["ClientSecret"]}&'
                                          f'grant_type=client_credentials').json()
        g.tokens['AppAccessToken'] = response['access_token']
        print(f'new AppAccessToken - {g.tokens["AppAccessToken"]}')


async def processPostRequest(request):
    try:
        alg, sign = request['X-Hub-Signature'].split('=')
        xHub = hmac.new(g.tokens['secret'].encode(), request['bytes'], alg).hexdigest() # recompute hash to validate notification
        if xHub == sign:
            global streams
            username = request['args']['u']
            notifyID = request['notifyID']
            channels = db.getStreams()[username]['channels']
            if not streams.get(username):
                streams[username] = {}
            if streams[username].get('notifyID') == notifyID: # check if same notification ID
                return
            streams[username]['notifyID'] = notifyID
            if not request['json']['data']: # went offline
                duration = seconds_convert(time.time() - convert_utc_to_epoch(streams[username]['user_data']['started_at']))
                for message in streams[username]['notify_messages']:
                    try:
                        await g.client.loop.create_task(message.edit(
                            content=f"```apache\n[{username}] Stream ended, it lasted {duration}```", embed=None))
                    except discord.errors.NotFound:
                        g.client.loop.create_task(message.channel.send(
                                f"```apache\n[{username}] Stream ended, it lasted {duration}```"))
                    except Exception:
                        logging.exception('e')
            else:                           # went live
                streams[username]['notify_messages'] = []
                streams[username]['user_data'] = request['json']['data'][0]
                try:
                    streams[username]['user_data']['game'] = \
                        requests.get(f"https://api.twitch.tv/helix/games?id={streams[username]['user_data']['game_id']}",
                                        headers={
                                            "Client-ID": g.tokens['Client-ID'], 
                                            'Authorization': f'Bearer {g.tokens["ClientOAuth"]}'
                                            }).json()['data'][0]['name']
                except IndexError:
                    streams[username]['user_data']['game'] = 'nothing xd'
                embed = discordEmbed(streams[username]['user_data'])
                for channel in channels:
                    channel = g.client.get_channel(channel)
                    try:
                        message = await g.client.loop.create_task(channel.send(
                                f'@everyone https://www.twitch.tv/{username} is live '
                                f'{random.choice(["pog", "poggers", "pogchamp", "poggies"])}',
                                embed=embed))
                        streams[username]['notify_messages'].append(message)
                    except Exception:
                        logging.exception('e')
    except Exception:
        logging.exception('e')


@exponentBackoff
async def webhookStreamsRequest(username, mode, *, userid=None):
    if userid is None:
        response = requests.get(f'https://api.twitch.tv/helix/users?login={username}', 
                                    headers={'Client-ID': g.tokens["Client-ID"], 
                                                'Authorization': f'Bearer {g.tokens["ClientOAuth"]}'}).json()
        userid = response['data'][0]['id']
        db.addNotifyUserID(username, userid)
    await validateAppAccessToken()
    r = requests.post('https://api.twitch.tv/helix/webhooks/hub', 
                        headers={'Client-ID': g.tokens["Client-ID"], 
                                    'Authorization': f'Bearer {g.tokens["AppAccessToken"]}'
                                }, 
                        data={
                            'hub.callback': f'{g.tokens["callbackURL"]}?u={username}', 
                            'hub.mode': mode, 
                            'hub.topic': f'https://api.twitch.tv/helix/streams?user_id={userid}', 
                            'hub.lease_seconds': 863000, 
                            'hub.secret': g.tokens["secret"]
                        })
    if r.content:
        print(r.content)
        return
    return True

async def updateWebhooks():
    while True:
        for username, userdata in db.getStreams().items():
            await webhookStreamsRequest(username, 'subscribe', userid=userdata['userid'])
        await asyncio.sleep(860000) # 864000

