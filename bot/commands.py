import discord
import io
import time
import globals as g

from decorators import bot_command
from utils import is_mod, hex3_to_hex6, hex_to_rgb, rgb_to_hex, seconds_convert
from database import db
from regex import *
from PIL import Image
from os import _exit


@bot_command(name="help")
async def help_command(message):
    await message.channel.send(
        f"""```css
commands:
colorinfo <#hex or rgb> - get color image
nocolor - remove color role
color <#hex or rgb> - get color role, replace if exists, example: #f542f2 or 245, 66, 242
colors - list created color roles
info - uptime, bot channels, modlist

mod commands:
channel <channel_id> - bot will respond only in added channels, add channel if <channel_id> not in database, remove if present
nocolors - delete all color roles
notify <twitch_login> <discord_channel_id> - twitch stream notify, it will add stream if <discord_channel_id> not in database, remove if present, update if differs```""")


@bot_command(name="info")
async def info_command(message):
    response = ''
    response += 'listening to:\n'
    for channel_id in db.getBotChannels():
        channel = g.client.get_channel(channel_id)
        response += f'{channel.guild} - #{channel.name}\n'
    if g.cfg['notify']:
        streams = db.getStreams()
        if streams:
            response += '\ntwitch notifications:\n'
            for username, userdata in streams.items():
                for channel in userdata['channels']:
                    channel = g.client.get_channel(channel)
                    response += f'[{username}] - {channel.guild} - #{channel.name}\n'
    modlist = db.getModlist()
    if modlist:
        response += '\nmoderators:\n'
        for user_id in modlist:
            user = g.client.get_user(user_id)
            response += f'[{user.name}#{user.discriminator}]\n'
    await message.channel.send(
        f"""```css\n[uptime: {seconds_convert(time.time() - g.startTime)}]\n{response}\n```""")


@bot_command(name="channel", check_func=is_mod)
async def channel_command(message):
    messagesplit = message.content.split()
    try:
        target_channel = int(messagesplit[1])
        if not any(target_channel == channel.id for channel in message.guild.channels if
                   channel.type == discord.ChannelType.text):
            await message.channel.send(f'{message.author.mention}, {target_channel} - unknown channel id')
            return
        channel_object = g.client.get_channel(target_channel)
        if db.get_channel_by_id(target_channel):
            db.disconnect_channel(target_channel)
            await message.channel.send(
                f'{message.author.mention}, successfully removed '
                f'{channel_object.guild} - {channel_object.mention} from listen')
        else:
            db.connect_channel(target_channel)
            await message.channel.send(
                f'{message.author.mention}, successfully added '
                f'{channel_object.guild} - {channel_object.mention} to listen')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting [{messagesplit[1]}] to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no channel id')


@bot_command(name="colorinfo")
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


@bot_command(name="nocolors", check_func=is_mod)
async def nocolors_command(message):
    for role in message.guild.roles:
        if re.match(hex_color_regex, role.name):
            await role.delete()


@bot_command(name="nocolor")
async def nocolor_command(message):
    for role in message.author.roles:
        if re.match(hex_color_regex, role.name):
            await message.author.remove_roles(role)
            return
    await message.channel.send(f'{message.author.mention}, you have no color role')


@bot_command(name="color")
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
        if len([role for role in message.guild.roles if re.match(hex_color_regex, role.name)]) > g.cfg['rolesLimit']:
            await message.channel.send(
                f'{message.author.mention}, color roles limit reached, created color roles - !colors')
            return
        for role in message.author.roles:
            if re.match(hex_color_regex, role.name):
                await message.author.remove_roles(role)
                break
        new_role = await message.guild.create_role(name=color_code.lower(),
                                                   colour=discord.Colour(int(color_code[1:], 16)))
        await message.author.add_roles(new_role)


@bot_command(name="colors")
async def colors_command(message):
    colors_list = [role.mention for role in message.guild.roles if re.match(hex_color_regex, role.name)]
    if not colors_list:
        await message.channel.send(f'{message.author.mention}, no colors available')
        return
    await message.channel.send(f'created color roles - {", ".join(colors_list)}')


@bot_command(name="notify", check_func=is_mod)
async def notify_command(message):
    messagesplit = message.content.split()
    try:
        twitch_login = messagesplit[1].lower()
        if not 4 <= len(twitch_login) <= 25:
            await message.channel.send(f'{message.author.mention}, twitch login must be between 4 and 25 characters')
            return
        notifyChannelIDsStr = ' '.join(messagesplit[2:])
        notifyChannelIDs = [int(x) for x in notifyChannelIDsStr.split(',')]
        for x in notifyChannelIDs:
            if not any(x == channel.id for channel in message.guild.channels if channel.type == discord.ChannelType.text):
                await message.channel.send(f'{message.author.mention}, {x} - unknown channel id')
                return
        data = db.getNotifyChannelsByName(twitch_login)
        if not data:
            db.addNotify(twitch_login, notifyChannelIDsStr)
            await message.channel.send(
                f'{message.author.mention}, successfully added {twitch_login} - {notifyChannelIDsStr} channels to notify')
            return
        channels, userid = data[0]
        if channels:
            if notifyChannelIDsStr.strip() !=  channels.strip():
                db.updateNotifyChannels(twitch_login, channels, notifyChannelIDsStr, userid=userid)
                await message.channel.send(f'{message.author.mention}, successfully updated {twitch_login} channels to '
                                           f'{notifyChannelIDsStr}')
                return
            db.removeNotify(twitch_login, notifyChannelIDsStr, userid=userid)
            await message.channel.send(
                f'{message.author.mention}, successfully removed {twitch_login} - {notifyChannelIDsStr} channels from notify')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting [{messagesplit[2:]}] to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no twitch login / channel id')


@bot_command(name="exit", check_func=is_mod)
async def exit_command(message):
    _exit(0)
