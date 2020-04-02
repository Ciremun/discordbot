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

TOKEN, client_id = [line.split(' ')[1].rstrip() for line in open('tokens')]
# reading tokens from "tokens" file, local dir
client = discord.Client()
hex_color_regex = re.compile(r'^#([A-Fa-f0-9]{6})$')
hex3_color_regex = re.compile(r'^#([A-Fa-f0-9]{3})$')
rgb_regex = re.compile(r'^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
rgb_hex_regex = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^(?:(?:^|,?\s*)([01]?\d\d?|2[0-4]\d|25[0-5])){3}$')
color_roles_limit = 50
bot_channel_ids, notify_channel_ids, modlist = [], [], []
# discord channel ids to listen and send stream notify, discord user ids for bot mod commands, edit via db_query
notify_enabled = True
notify_twitcher_username = 'mallfiss_'
discord_guild_id = 692557289982394418
stream_discord_embed_hex6 = "#00BFFF"
prefix = '!'


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
    random_emote_id = get_random_guild_emote(discord_guild_id).get("id", None)
    if random_emote_id:
        embed.set_image(url=f'https://cdn.discordapp.com/emojis/{random_emote_id}.png')
    return embed


def new_timecode_explicit(seconds, minutes, hours, duration):
    if duration <= 59:
        return f'{duration}s'
    elif duration <= 3599:
        return f'{minutes}m {seconds}s'
    else:
        return f'{hours}h {minutes}m {seconds}s'


def seconds_convert(duration):
    h = floor(duration / 3600)
    m = floor(duration % 3600 / 60)
    s = floor(duration % 3600 % 60)
    return new_timecode_explicit(s, m, h, duration)


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


async def ttv_command(message):
    channel_info = requests.get(f"https://api.twitch.tv/helix/streams?user_login={notify_twitcher_username}",
                                headers={"Client-ID": f'{client_id}'}).json()['data']
    if not channel_info or channel_info[0]['type'] != 'live':
        await message.channel.send(f'{notify_twitcher_username} is offline')
    else:
        channel_info = channel_info[0]
        try:
            channel_info['game'] = requests.get(f"https://api.twitch.tv/helix/games?id={channel_info['game_id']}",
                                                headers={"Client-ID": f'{client_id}'}).json()['data'][0]['name']
        except IndexError:
            channel_info['game'] = 'nothing xd'
        embed = get_stream_discord_embed(channel_info)
        await message.channel.send(
            f'https://www.twitch.tv/{notify_twitcher_username} is live '
            f'{random.choice(["pog", "poggers", "pogchamp", "poggies"])}',
            embed=embed)


async def connect_command(message):
    if not user_is_mod(message):
        return
    await connect_disconnect_command(message, db.connect_channel, True, ['already listening', 'added to'],
                                     bot_channel_ids.append)


async def disconnect_command(message):
    if not user_is_mod(message):
        return
    await connect_disconnect_command(message, db.disconnect_channel, False, ['not connected', 'removed from'],
                                     bot_channel_ids.remove)


async def connect_disconnect_command(message, db_call, if_param, response_list, bot_channel_ids_act):
    try:
        messagesplit = message.content.split()
        target_channel = int(messagesplit[1])
        if db.get_channel_by_id(target_channel) == if_param:
            await message.channel.send(f'{message.author.mention}, {response_list[0]} to {messagesplit[1]}')
            return
        db_call(target_channel)
        bot_channel_ids_act(target_channel)
        channel_object = client.get_channel(target_channel)
        await message.channel.send(
            f'{message.author.mention}, {channel_object.guild} - #{channel_object.name} successfully '
            f'{response_list[1]} listen')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no channel_id!')


async def connections_command(message):
    if not user_is_mod(message):
        return
    result = [i[0] for i in db.get_channels()]
    response = [f'{channel.guild} - #{channel.name}\n' for channel in
                [client.get_channel(channel_id) for channel_id in result]]
    await message.channel.send(f"""```css\n{''.join(response)}```""")


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


async def nocolors_command(message):
    if not user_is_mod(message):
        return
    for role in message.guild.roles:
        if re.match(hex_color_regex, role.name):
            await role.delete()


async def nocolor_command(message):
    for role in message.author.roles:
        if re.match(hex_color_regex, role.name):
            await message.author.remove_roles(role)
            return
    await message.channel.send(f'{message.author.mention}, you have no color role')


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


async def colors_command(message):
    colors_list = [role.mention for role in message.guild.roles if re.match(hex_color_regex, role.name)]
    if not colors_list:
        await message.channel.send(f'{message.author.mention}, no colors available')
        return
    await message.channel.send(f'created color roles - {", ".join(colors_list)}')


async def exit_command(message):
    if not user_is_mod(message):
        return
    os._exit(0)


async def help_command(message):
    await message.channel.send(
        f"""```css
prefix=!
commands:
colorinfo <#hex or rgb> - get color image
nocolor - remove color role
color <#hex or rgb> - get color role, replace if exists, example: #f542f2 or 245, 66, 242
colors - list created color roles
ttv - check if live on twitch
mod_commands:
connect, disconnect, connections
nocolors - delete all color roles```""")


commands_dict = {
    'help': help_command,
    'ttv': ttv_command,
    'color': color_command,
    'colors': colors_command,
    'nocolor': nocolor_command,
    'nocolors': nocolors_command,
    'connections': connections_command,
    'connect': connect_command,
    'disconnect': disconnect_command,
    'exit': exit_command,
    'colorinfo': colorinfo_command
}


@client.event
async def on_message(message):
    if message.author == client.user or not any(message.channel.id == i for i in bot_channel_ids):
        return

    messagesplit = message.content.split()

    if message.content.startswith(prefix):
        command = commands_dict.get(messagesplit[0][1:], None)
        if command is None:
            return
        await command(message)


@client.event
async def on_ready():
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

    if notify_enabled:
        live_notify.call_check_if_live(notify_twitcher_username)


class ThreadDB:

    def __init__(self):
        global bot_channel_ids, notify_channel_ids, modlist
        self.conn = sqlite3.connect('db/discord_data.db')
        self.c = self.conn.cursor()
        bot_channel_ids = [i[0] for i in self.get_channels()]
        notify_channel_ids = [i[0] for i in self.get_notify_channels()]
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

    def get_notify_channels(self):
        self.c.execute('SELECT notify_channel_id FROM notify')
        return self.c.fetchall()

    def get_modlist(self):
        self.c.execute('SELECT user_id FROM modlist')
        return self.c.fetchall()


class AsyncioLoop:

    def __init__(self, loop):
        self.loop = loop
        self.notification_sent = True
        self.sleep_time = 600
        asyncio.set_event_loop(self.loop)

        async def start():
            while True:
                await asyncio.sleep(0.1)

        def run_it_forever(loop):
            loop.run_forever()

        self.loop.create_task(start())
        thread = threading.Thread(target=run_it_forever, args=(self.loop,))
        thread.start()

    def call_check_if_live(self, username):
        self.loop.create_task(self.check_if_live(username))

    async def check_if_live(self, username):
        if not notify_enabled:
            return
        channel_info = requests.get(f"https://api.twitch.tv/helix/streams?user_login={username}",
                                    headers={"Client-ID": f'{client_id}'}).json()['data']
        if not channel_info or channel_info[0]['type'] != 'live':
            self.notification_sent = False
            self.sleep_time = 120
        elif not self.notification_sent:
            channel_info = channel_info[0]
            self.sleep_time = 600
            try:
                channel_info['game'] = requests.get(f"https://api.twitch.tv/helix/games?id={channel_info['game_id']}",
                                                    headers={"Client-ID": f'{client_id}'}).json()['data'][0]['name']
            except IndexError:
                channel_info['game'] = 'nothing xd'
            embed = get_stream_discord_embed(channel_info)
            for channel_id in notify_channel_ids:
                channel = client.get_channel(channel_id)
                asyncio.run_coroutine_threadsafe(
                    channel.send(
                        f'@everyone https://www.twitch.tv/{username} is live '
                        f'{random.choice(["pog", "poggers", "pogchamp", "poggies"])}',
                        embed=embed), client.loop)
                self.notification_sent = True
        await asyncio.sleep(self.sleep_time)
        self.loop.create_task(self.check_if_live(username))


db = ThreadDB()
live_notify_loop = asyncio.new_event_loop()
live_notify = AsyncioLoop(live_notify_loop)
client.run(TOKEN)
