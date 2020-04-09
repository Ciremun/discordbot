import discord
import re
import os
from PIL import Image
import io
import sqlite3
import asyncio
import threading
import requests
import random
from math import floor
from datetime import datetime
import time

color_roles_limit = 50
notify_enabled = True
stream_discord_embed_hex6 = "#3498db"
prefix = '!'
notify_sleep_time = 90

start_time = time.time()
TOKEN, client_id = [line.split()[1].rstrip() for line in open('tokens')]
bot_channel_ids, modlist, commands_dict = [], [], {}
hex_color_regex = re.compile(r'^#([A-Fa-f0-9]{6})$')
hex3_color_regex = re.compile(r'^#([A-Fa-f0-9]{3})$')
rgb_regex = re.compile(r'^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
rgb_hex_regex = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
client = discord.Client()


def bot_command(func):
    def wrapper(message, *args, **kwargs):
        return func(message, *args, **kwargs)

    commands_dict[func.__code__.co_name[:-8]] = wrapper
    return wrapper


def mod_command(func):
    def wrapper(message, *args, **kwargs):
        if not user_is_mod(message):
            return
        return func(message, *args, **kwargs)

    commands_dict[func.__code__.co_name[:-8]] = wrapper
    return wrapper


def get_stream_discord_embed(channel_info: dict):
    """
    get discord.Embed for stream notification
    :param channel_info: twitch api get_streams data dictionary
    :return: discord.Embed
    """
    embed = discord.Embed(title=f'{channel_info["title"]}',
                          url=f'https://twitch.tv/{channel_info["user_name"]}', color=int(stream_discord_embed_hex6[1:],
                                                                                          16))
    embed.add_field(name='Playing', value=f'{channel_info["game"]}')
    embed.add_field(name='Stream started',
                    value=f'{seconds_convert(time.time() - convert_utc_to_epoch(channel_info["started_at"]))} ago')
    embed.set_footer(text='hehe xd')
    random_emote_id = get_random_guild_emote(random.choice([guild.id for guild in client.guilds])).get("id", None)
    if random_emote_id:
        embed.set_image(url=f'https://cdn.discordapp.com/emojis/{random_emote_id}.png')
    return embed


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


def get_random_guild_emote(guild_id: int):
    """
    get random discord server emote as a dictionary
    :param guild_id: discord guild id to fetch emotes
    :return: dict
    """
    guild_emotes_list = [{'name': x.name,
                          'id': x.id} for x in client.get_guild(guild_id).emojis if not x.animated and x.available]
    if guild_emotes_list:
        return random.choice(guild_emotes_list)
    return {}


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


def user_is_mod(message):
    return bool(any(message.author.id == i for i in modlist))


@mod_command
async def channel_command(message):
    messagesplit = message.content.split()
    try:
        target_channel = int(messagesplit[1])
        if not any(target_channel == channel.id for channel in message.guild.channels if
                   channel.type == discord.ChannelType.text):
            await message.channel.send(f'{message.author.mention}, {target_channel} - unknown channel id')
            return
        channel_object = client.get_channel(target_channel)
        if db.get_channel_by_id(target_channel):
            db.disconnect_channel(target_channel)
            bot_channel_ids.remove(target_channel)
            await message.channel.send(
                f'{message.author.mention}, successfully removed '
                f'{channel_object.guild} - {channel_object.mention} from listen')
        else:
            db.connect_channel(target_channel)
            bot_channel_ids.append(target_channel)
            await message.channel.send(
                f'{message.author.mention}, successfully added '
                f'{channel_object.guild} - {channel_object.mention} to listen')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting [{messagesplit[1]}] to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no channel id')


@bot_command
async def colorinfo_command(message):
    messagesplit = message.content.split()
    color_code = ' '.join(messagesplit[1:])
    if not color_code:
        await message.channel.send(f'{message.author.mention}, no color! usage: colorinfo <#hex or rgb>')
        return
    if not re.match(rgb_hex_regex, color_code):
        await message.channel.send(f'{message.author.mention}, color: #hex or rgb, example: #f542f2 or 245, 66, 242')
        return
    if re.match(rgb_regex, color_code):
        try:
            r, g, b = [int(i.strip(',')) for i in color_code.split()]
            color_code = rgb_to_hex(r, g, b)
        except ValueError:
            await message.channel.send(f'{message.author.mention}, rgb example: 245, 66, 242')
            return
    elif re.match(hex3_color_regex, color_code):
        color_code = hex3_to_hex6(color_code)
    color_img = Image.new("RGB", (100, 100), color_code)
    with io.BytesIO() as image_binary:
        color_img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await message.channel.send(f'color: rgb{hex_to_rgb(color_code)}, {color_code}',
                                   file=discord.File(fp=image_binary, filename='image.png'))


@mod_command
async def nocolors_command(message):
    for role in message.guild.roles:
        if re.match(hex_color_regex, role.name):
            await role.delete()


@bot_command
async def nocolor_command(message):
    for role in message.author.roles:
        if re.match(hex_color_regex, role.name):
            await message.author.remove_roles(role)
            return
    await message.channel.send(f'{message.author.mention}, you have no color role')


@bot_command
async def color_command(message):
    messagesplit = message.content.split()
    color_code = ' '.join(messagesplit[1:])
    if not color_code:
        for role in message.author.roles:
            if re.match(hex_color_regex, role.name):
                await message.channel.send(f'{message.author.mention}, your current color is {role.mention}')
                return
        await message.channel.send(f'{message.author.mention}, you have no color role')
        return
    if len([role for role in message.guild.roles if re.match(hex_color_regex, role.name)]) > color_roles_limit:
        await message.channel.send(
            f'{message.author.mention}, color roles limit reached, created color roles - !colors')
        return
    elif not re.match(rgb_hex_regex, color_code):
        await message.channel.send(f'{message.author.mention}, color: #hex or rgb, example: #f542f2 or 245, 66, 242')
        return
    if re.match(rgb_regex, color_code):
        try:
            r, g, b = [int(i.strip(',')) for i in color_code.split()]
            color_code = rgb_to_hex(r, g, b)
        except ValueError:
            await message.channel.send(f'{message.author.mention}, rgb example: 245, 66, 242')
            return
    elif re.match(hex3_color_regex, color_code):
        color_code = hex3_to_hex6(color_code)
    if any(role.name == color_code.lower() for role in message.author.roles):
        await message.channel.send(
            f'{message.author.mention}, you already have '
            f'{discord.utils.get(message.guild.roles, name=color_code.lower()).mention} '
            f' color')
    else:
        for i in message.guild.roles:
            if i.name == color_code:
                for role in message.author.roles:
                    if re.match(hex_color_regex, role.name):
                        await message.author.remove_roles(role)
                        break
                await message.author.add_roles(i)
                return
        for role in message.author.roles:
            if re.match(hex_color_regex, role.name):
                await message.author.remove_roles(role)
                break
        new_role = await message.guild.create_role(name=color_code.lower(),
                                                   colour=discord.Colour(int(color_code[1:], 16)))
        await message.author.add_roles(new_role)


@bot_command
async def colors_command(message):
    colors_list = [role.mention for role in message.guild.roles if re.match(hex_color_regex, role.name)]
    if not colors_list:
        await message.channel.send(f'{message.author.mention}, no colors available')
        return
    await message.channel.send(f'created color roles - {", ".join(colors_list)}')


@mod_command
async def exit_command(message):
    os._exit(0)


@mod_command
async def notify_command(message):
    messagesplit = message.content.split()
    try:
        twitch_login = messagesplit[1]
        if not 4 <= len(twitch_login) <= 25:
            await message.channel.send(f'{message.author.mention}, twitch login must be between 4 and 25 characters')
            return
        notify_channel_id = int(messagesplit[2])
        if not any(notify_channel_id == channel.id for channel in message.guild.channels if
                   channel.type == discord.ChannelType.text):
            await message.channel.send(f'{message.author.mention}, {notify_channel_id} - unknown channel id')
            return
        channel_object = client.get_channel(notify_channel_id)
        if db.get_twitch_notify_by_login(twitch_login):
            if stream_notify.twitchers_dict[twitch_login]['notify_channel'] != notify_channel_id:
                db.update_twitch_notify(twitch_login, stream_notify.twitchers_dict[twitch_login]['notify_channel'],
                                        notify_channel_id)
                stream_notify.twitchers_dict[twitch_login] = {'notify_sent': False,
                                                              'user_data': {},
                                                              'notify_message': None,
                                                              'started_at': '',
                                                              'notify_channel': notify_channel_id}
                await message.channel.send(f'{message.author.mention}, successfully updated {twitch_login} channel to '
                                           f'{channel_object.guild} - {channel_object.mention}')
                return
            db.remove_twitch_notify(twitch_login, notify_channel_id)
            del stream_notify.twitchers_dict[twitch_login]
            stream_notify.requests_str = stream_notify.requests_str.replace(f'&user_login={twitch_login}', '')
            await message.channel.send(
                f'{message.author.mention}, successfully removed '
                f'{channel_object.guild} - {channel_object.mention} from notify')
        else:
            db.add_twitch_notify(twitch_login, notify_channel_id)
            stream_notify.twitchers_dict[twitch_login] = {'notify_sent': False,
                                                          'user_data': {},
                                                          'notify_message': None,
                                                          'started_at': '',
                                                          'notify_channel': notify_channel_id}
            stream_notify.requests_str += f'&user_login={twitch_login}'
            await message.channel.send(
                f'{message.author.mention}, successfully added '
                f'{channel_object.guild} - {channel_object.mention} to notify')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting [{messagesplit[2]}] to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no twitch login / channel id')


@bot_command
async def info_command(message):
    response = ''
    response += 'listening to:\n'
    for channel_id in bot_channel_ids:
        channel = client.get_channel(channel_id)
        response += f'{channel.guild} - #{channel.name}\n'
    if notify_enabled:
        response += '\ntwitch notifications:\n'
        for username, data in stream_notify.twitchers_dict.items():
            channel = client.get_channel(data['notify_channel'])
            response += f'[{username}] - {channel.guild} - #{channel.name}\n'
    response += '\nmoderators:\n'
    for user_id in modlist:
        user = client.get_user(user_id)
        response += f'[{user.name}#{user.discriminator}]\n'
    await message.channel.send(
        f"""```css\n[uptime: {seconds_convert(floor(time.time() - start_time))}]\n{response}\n```""")


@bot_command
async def help_command(message):
    await message.channel.send(
        f"""```css
prefix={prefix}
commands:

colorinfo <#hex or rgb> - get color image

nocolor - remove color role

color <#hex or rgb> - get color role, replace if exists, example: #f542f2 or 245, 66, 242

colors - list created color roles

info - uptime, bot channels, modlist

mod_commands:

channel <channel_id> - bot will respond only in added channels, add channel if <channel_id> not in database, remove if present

nocolors - delete all color roles

notify <twitch_login> <discord_channel_id> - twitch stream notify, it will add stream if <discord_channel_id> not in database, remove if present, update if differs```""")


@client.event
async def on_message(message):
    if message.author == client.user or not any(message.channel.id == i for i in bot_channel_ids):
        return

    messagesplit = message.content.split()

    if message.content.startswith(prefix):
        try:
            await commands_dict[messagesplit[0][1:]](message)
        except (KeyError, TypeError):
            return


class DiscordData:

    def __init__(self):
        global bot_channel_ids, modlist
        self.conn = sqlite3.connect('db/discord_data.db')
        self.c = self.conn.cursor()
        bot_channel_ids = [i[0] for i in self.get_channels()]
        modlist = [i[0] for i in self.get_modlist()]

    def connect_channel(self, channel_id: int):
        with self.conn:
            self.c.execute('INSERT INTO channels (channel_id) VALUES (:channel_id)', {'channel_id': channel_id})

    def disconnect_channel(self, channel_id: int):
        with self.conn:
            self.c.execute('DELETE FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})

    def get_channels(self):
        self.c.execute('SELECT channel_id FROM channels')
        return self.c.fetchall()

    def get_channel_by_id(self, channel_id: int):
        self.c.execute('SELECT channel_id FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})
        return self.c.fetchall()

    def get_twitch_notify(self):
        self.c.execute('SELECT twitch_login, notify_channel_id FROM notify')
        return self.c.fetchall()

    def get_twitch_notify_by_login(self, twitch_login: str):
        self.c.execute(
            'SELECT twitch_login FROM notify WHERE twitch_login = :twitch_login', {'twitch_login': twitch_login})
        return self.c.fetchall()

    def get_modlist(self):
        self.c.execute('SELECT user_id FROM modlist')
        return self.c.fetchall()

    def add_twitch_notify(self, twitch_login: str, notify_channel_id: int):
        with self.conn:
            self.c.execute(
                'INSERT INTO notify (twitch_login, notify_channel_id) VALUES (:twitch_login, :notify_channel_id)',
                {'twitch_login': twitch_login, 'notify_channel_id': notify_channel_id})

    def remove_twitch_notify(self, twitch_login: str, notify_channel_id: int):
        with self.conn:
            self.c.execute(
                'DELETE FROM notify WHERE twitch_login = :twitch_login and notify_channel_id = :notify_channel_id',
                {'twitch_login': twitch_login, 'notify_channel_id': notify_channel_id})

    def update_twitch_notify(self, twitch_login: str, notify_channel_id: int, new_notify_channel_id: int):
        with self.conn:
            self.c.execute(
                'UPDATE notify SET notify_channel_id = :new_notify_channel_id WHERE twitch_login = :twitch_login and '
                'notify_channel_id = :notify_channel_id',
                {'twitch_login': twitch_login,
                 'notify_channel_id': notify_channel_id, 'new_notify_channel_id': new_notify_channel_id})


class StreamNotify(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.twitchers_dict = {k.lower(): v for k, v in db.get_twitch_notify()}
        self.sleep_time = notify_sleep_time
        self.requests_str = 'https://api.twitch.tv/helix/streams?'
        for username, channel_id in self.twitchers_dict.items():
            self.requests_str += f'user_login={username}&'
            self.twitchers_dict[username] = {'notify_sent': False,
                                             'user_data': {},
                                             'notify_message': None,
                                             'started_at': '',
                                             'notify_channel': channel_id}
        self.requests_str = self.requests_str[:-1]

    def run(self):
        while not client.is_ready():
            time.sleep(1)
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('--------------')
        print(f'modlist:')
        [print(client.get_user(user).name) for user in modlist]
        print('--------------')
        print(f'listening to:')
        [print(f'{channel.guild} - #{channel.name}') for channel in
         [client.get_channel(channel_id) for channel_id in bot_channel_ids]]
        print('--------------')
        print(f'stream notify:')
        [print(f'[{k}] - {channel.guild} - #{channel.name}') for k, v in stream_notify.twitchers_dict.items() for
         channel in [client.get_channel(v['notify_channel'])]]
        if notify_enabled:
            self.check_if_live()

    def check_if_live(self):
        while notify_enabled:
            channels_data = requests.get(self.requests_str, headers={"Client-ID": f'{client_id}'}).json()['data']
            for user_data in channels_data:
                self.twitchers_dict[user_data['user_name'].lower()]['user_data'] = user_data
            for username in self.twitchers_dict:
                if not self.twitchers_dict[username]['user_data']:
                    if self.twitchers_dict[username]['notify_message']:
                        stream_duration = seconds_convert(time.time() - convert_utc_to_epoch(
                            self.twitchers_dict[username]['started_at']))
                        future = asyncio.run_coroutine_threadsafe(self.twitchers_dict[username]['notify_message'].edit(
                            content=f'Stream ended, it lasted {stream_duration}',
                            embed=None), client.loop)
                        try:
                            future.result()
                        except discord.errors.NotFound:
                            asyncio.run_coroutine_threadsafe(
                                self.twitchers_dict[username]['notify_message'].channel.send
                                (f'Stream ended, it lasted {stream_duration}'),
                                client.loop)
                        self.twitchers_dict[username]['notify_message'] = None
                    self.twitchers_dict[username]['notify_sent'] = False
                elif not self.twitchers_dict[username]['notify_sent']:
                    try:
                        self.twitchers_dict[username]['user_data']['game'] = \
                            requests.get(
                                f"https://api.twitch.tv/helix/games?id="
                                f"{self.twitchers_dict[username]['user_data']['game_id']}",
                                headers={"Client-ID": f'{client_id}'}).json()['data'][0]['name']
                    except IndexError:
                        self.twitchers_dict[username]['user_data']['game'] = 'nothing xd'
                    embed = get_stream_discord_embed(self.twitchers_dict[username]['user_data'])
                    channel = client.get_channel(self.twitchers_dict[username]['notify_channel'])
                    future = asyncio.run_coroutine_threadsafe(
                        channel.send(
                            f'@everyone https://www.twitch.tv/{username} is live '
                            f'{random.choice(["pog", "poggers", "pogchamp", "poggies"])}',
                            embed=embed), client.loop)
                    self.twitchers_dict[username]['notify_message'] = future.result()
                    self.twitchers_dict[username]['notify_sent'] = True
                    self.twitchers_dict[username]['started_at'] = \
                        self.twitchers_dict[username]['user_data']['started_at']
                self.twitchers_dict[username]['user_data'].clear()
            time.sleep(self.sleep_time)


db = DiscordData()
stream_notify = StreamNotify('StreamNotify')
stream_notify.start()
client.run(TOKEN)
