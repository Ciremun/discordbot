import discord

from globals import tokens, cfg, client, commands
from utils import is_mod
from database import db 


@client.event
async def on_message(message):

    if message.author == client.user or (not is_mod(message) and not any(message.channel.id == i for i in db.getBotChannels())):
        return

    if message.content.startswith(cfg['prefix']):
        try:
            messagesplit = message.content.split()
            await commands[messagesplit[0][1:]](message)
        except (KeyError, TypeError):
            return


@client.event
async def on_guild_channel_delete(channel):
    db.disconnect_channel(channel.id)
    streams = db.getStreams()
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
                db.removeNotify(username, ', '.join(channels), userid=userid)
                continue
            newChannels = [str(x) for x in newChannels]
            db.updateNotifyChannels(username, ', '.join(channels), ', '.join(newChannels), userid=userid)
        except ValueError:
            pass

client.run(tokens['DiscordToken'])
