import random
import hmac
import time
from typing import Optional

import discord
import requests

import src.db as db
from .config import keys, cfg
from .utils import is_mod, updateWebhooks, seconds_convert, convert_utc_to_epoch, webhookStreamsRequest
from .log import logger

client = discord.Client()
streams = db.get_streams_state()[0]
if cfg['notify']:
    client.loop.create_task(updateWebhooks())


@client.event
async def on_ready(*args, **kwargs):
    logger.info('bot ready')


@client.event
async def on_message(message):
    from .commands import commands

    if message.author == client.user or (not is_mod(message) and not any(message.channel.id == i for i in db.get_bot_channels())):
        return

    if message.content.startswith(cfg['prefix']):
        try:
            messagesplit = message.content.split()
            await commands[messagesplit[0][len(cfg['prefix']):]](message)
        except (KeyError, TypeError):
            return


@client.event
async def on_guild_channel_delete(channel):
    db.disconnect_channel(channel.id)
    streams = db.get_streams()
    for username, userdata in streams.items():
        channels = userdata['channels']
        if channel.id not in channels:
            continue
        userid = userdata['userid']
        newChannels = channels.copy()
        channels = [str(x) for x in channels]
        try:
            newChannels.remove(channel.id)
            if not newChannels:
                db.removeNotify(username, ' '.join(channels), userid=userid)
                client.loop.create_task(webhookStreamsRequest(
                    username, 'unsubscribe', userid=userid))
                continue
            newChannels = [str(x) for x in newChannels]
            db.updateNotifyChannels(username, ' '.join(
                channels), ' '.join(newChannels), userid=userid)
        except ValueError:
            pass


def discordEmbed(channel_info: dict) -> discord.Embed:
    """
    get discord.Embed for stream notification
    :param channel_info: twitch api get_streams data dictionary
    """
    embed = discord.Embed(title=f'{channel_info["title"]}',
                          url=f'https://twitch.tv/{channel_info["user_name"]}', color=int(cfg['embedHex6'][1:], 16))
    embed.add_field(name='Playing', value=f'{channel_info["game"]}')
    embed.add_field(name='Stream started',
                    value=f'{seconds_convert(time.time() - convert_utc_to_epoch(channel_info["started_at"]))} ago')
    embed.set_footer(text=cfg['footerText'])
    random_emote_id = randomGuildEmote(
        random.choice([guild.id for guild in client.guilds]))
    if random_emote_id:
        embed.set_image(
            url=f'https://cdn.discordapp.com/emojis/{random_emote_id}.png')
    return embed


def randomGuildEmote(guild_id: int) -> Optional[int]:
    guild_emotes_list = [{'name': x.name,
                          'id': x.id} for x in client.get_guild(guild_id).emojis if not x.animated and x.available]
    if guild_emotes_list:
        return random.choice(guild_emotes_list).get("id")
    return None


async def processPostRequest(request):
    alg, sign = request['X-Hub-Signature'].split('=')
    # recompute hash to validate notification
    xHub = hmac.new(keys['SECRET'].encode(), request['bytes'], alg).hexdigest()
    if xHub == sign:
        global streams
        username = request['args']['u']
        notifyID = request['notifyID']
        if not streams.get(username):
            streams[username] = {'live': None, 'notify_messages': []}
        # check if same notification ID
        if streams[username].get('notifyID') == notifyID:
            logger.debug(f'duplicate ID {username} - {notifyID}')
            return
        streams[username]['notifyID'] = notifyID
        if not request['json']['data'] and streams[username]['live']:      # went offline
            logger.debug(
                f'{username} went offline, ID {streams[username]["notifyID"]}')
            streams[username]['live'] = False
            if not streams[username]['notify_messages']:
                logger.debug(f'no notify_messages {username}')
                return
            duration = seconds_convert(
                time.time() - convert_utc_to_epoch(streams[username]['user_data']['started_at']))
            sent_notifications = []
            for message in streams[username]['notify_messages']:
                try:
                    await client.loop.create_task(message.edit(
                        content=f"```apache\n[{username}] Stream ended, it lasted {duration}```", embed=None))
                except discord.errors.NotFound:
                    client.loop.create_task(message.channel.send(
                        f"```apache\n[{username}] Stream ended, it lasted {duration}```"))
                except Exception as e:
                    logger.error(e)
                sent_notifications.append(message)
            for message in sent_notifications:
                streams[username]['notify_messages'].remove(message)
            sent_notifications.clear()
        elif request['json']['data'] and not streams[username]['live']:  # went live
            logger.debug(
                f'{username} went live, ID {streams[username]["notifyID"]}')
            streams[username]['live'] = True
            streams[username]['user_data'] = request['json']['data'][0]
            try:
                streams[username]['user_data']['game'] = \
                    requests.get(f"https://api.twitch.tv/helix/games?id={streams[username]['user_data']['game_id']}",
                                 headers={
                                     "Client-ID": keys['CLIENT_ID'],
                                     'Authorization': f'Bearer {keys["CLIENT_OAUTH"]}'
                                 }).json()['data'][0]['name']
            except:
                streams[username]['user_data']['game'] = 'nothing xd'
            embed = discordEmbed(streams[username]['user_data'])
            channels = db.get_streams()[username]['channels']
            for channel in channels:
                channel = client.get_channel(channel)
                if not channel:
                    continue
                message = await client.loop.create_task(channel.send(
                    f'@everyone https://www.twitch.tv/{username} is live '
                    f'{random.choice(["pog", "poggers", "pogchamp", "poggies"])}',
                    embed=embed))
                streams[username]['notify_messages'].append(message)
        db.update_streams_state(streams)
        return True
    return
