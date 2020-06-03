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

client.run(tokens['DiscordToken'])
