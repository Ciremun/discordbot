import io
import time
import re
from os import _exit

import discord
from PIL import Image

import src.db as db
from .config import cfg, start_time
from .utils import is_mod, hex3_to_hex6, hex_to_rgb, rgb_to_hex, seconds_convert, webhookStreamsRequest
from .regex import hex_color_regex, hex3_color_regex, rgb_regex, rgb_hex_regex
from .client import client

commands = {}

def bot_command(*, name, check_func=None):
    def decorator(func):
        def wrapper(message):
            if callable(check_func) and not check_func(message):
                return False
            return func(message)
        commands[name] = wrapper
        return wrapper
    return decorator


@bot_command(name="exec", check_func=is_mod)
async def exec_command(message):
    try:
        code = '\n'.join(message.content.split('\n')[2:])[:-3]
        exec(code)
    except Exception as e:
        await message.channel.send(f'{e}')


@bot_command(name="mute", check_func=is_mod)
async def mute_command(message):
    mutedRole = discord.utils.get(message.guild.roles, name='Muted')
    if not mutedRole:
        await message.channel.send(f'{message.author.mention}, "Muted" role doesnt exist')
        return
    messagesplit = message.content.split()
    targets = messagesplit[1:]
    if not targets:
        await message.channel.send(f'{message.author.mention}, no mute target')
        return
    for target in message.mentions + targets:
        if isinstance(target, discord.Member):
            member = target
        else:
            try:
                member = discord.utils.get(message.guild.members, id=int(target))
                if not member:
                    await message.channel.send(f'{message.author.mention}, userID [{target}] not found')
                    continue
            except ValueError:
                continue
        for role in member.roles:
            if role.id == mutedRole.id:
                await member.remove_roles(mutedRole)
                break
        else:
            await member.add_roles(mutedRole)


@bot_command(name="help")
async def help_command(message):
    await message.channel.send("https://github.com/Ciremun/discordbot/blob/master/README.md")


@bot_command(name="info")
async def info_command(message):
    response = '\n'
    response += 'listening to:\n'
    for channel_id in db.get_bot_channels():
        channel = client.get_channel(channel_id)
        response += f'{channel.guild} - #{channel.name}\n'
    if cfg['notify']:
        streams = db.get_streams()
        if streams:
            response += '\ntwitch notifications:\n'
            for username, userdata in streams.items():
                for channel in userdata['channels']:
                    channel = client.get_channel(channel)
                    response += f'[{username}] - {channel.guild} - #{channel.name}\n'
    modlist = db.getModlist()
    if modlist:
        response += '\nmoderators:\n'
        for user_id in modlist:
            user = client.get_user(user_id)
            if not user:
                response += f'[userid:{user_id}]\n'
            else:
                response += f'[{user.name}#{user.discriminator}]\n'
    response += '\n'
    if len(response) > 2000:
        response = ""
    await message.channel.send(
        f"""```css\n[uptime: {seconds_convert(time.time() - start_time)}]{response}```""")


@bot_command(name="channel", check_func=is_mod)
async def channel_command(message):
    messagesplit = message.content.split()
    try:
        target_channel = int(messagesplit[1])
        if not client.get_channel(target_channel):
            await message.channel.send(f'{message.author.mention}, {target_channel} - unknown channel id')
            return
        channel_object = client.get_channel(target_channel)
        if db.get_channel_by_id(target_channel):
            db.disconnect_channel(target_channel)
            await message.channel.send(
                f'{message.author.mention}, removed '
                f'{channel_object.guild} - {channel_object.mention} from listen')
        else:
            db.connect_channel(target_channel)
            await message.channel.send(
                f'{message.author.mention}, added '
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
        if len([role for role in message.guild.roles if re.match(hex_color_regex, role.name)]) > cfg['rolesLimit']:
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
        if not notifyChannelIDsStr:
            await message.channel.send(f'{message.author.mention}, no channel IDs')
            return
        notifyChannelIDs = [int(x) for x in notifyChannelIDsStr.split()]
        for x in notifyChannelIDs:
            if not client.get_channel(x):
                await message.channel.send(f'{message.author.mention}, {x} - unknown channel id')
        data = db.getNotifyChannelsByName(twitch_login)
        if not data:
            db.addNotify(twitch_login, notifyChannelIDsStr)
            client.loop.create_task(webhookStreamsRequest(twitch_login, 'subscribe'))
            await message.channel.send(
                f'{message.author.mention}, added {twitch_login} - {notifyChannelIDsStr} channels to notify')
            return
        channels, userid = data[0]
        if channels:
            if notifyChannelIDsStr.strip() !=  channels.strip():
                db.updateNotifyChannels(twitch_login, channels, notifyChannelIDsStr, userid=userid)
                await message.channel.send(f'{message.author.mention}, updated {twitch_login} channels to '
                                           f'{notifyChannelIDsStr}')
                return
            db.removeNotify(twitch_login, notifyChannelIDsStr, userid=userid)
            client.loop.create_task(webhookStreamsRequest(twitch_login, 'unsubscribe', userid=userid))
            await message.channel.send(
                f'{message.author.mention}, removed {twitch_login} - {notifyChannelIDsStr} channels from notify')
    except ValueError:
        await message.channel.send(f'{message.author.mention}, error converting {messagesplit[2:]} to int')
    except IndexError:
        await message.channel.send(f'{message.author.mention}, no twitch login')


@bot_command(name="exit", check_func=is_mod)
async def exit_command(message):
    _exit(0)
