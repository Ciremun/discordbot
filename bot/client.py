import threading
import discord

from globals import tokens, cfg, client, commands
from database import db

class DiscordClient(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        client.run(tokens['DiscordToken'])


@client.event
async def on_message(message):

    if message.author == client.user or not any(message.channel.id == i for i in db.getBotChannels()):
        return

    if message.content.startswith(cfg['prefix']):
        try:
            messagesplit = message.content.split()
            await commands[messagesplit[0][1:]](message)
        except (KeyError, TypeError):
            return


discordClient = DiscordClient()
