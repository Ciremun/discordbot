import json
import discord
import asyncio
import time

startTime = time.time()
tokens = json.load(open('tokens.json'))
cfg = json.load(open('cfg.json'))
commands, streams = {}, {}
client = discord.Client()

if cfg['notify']:
    import server
    from utils import updateWebhooks
    client.loop.create_task(updateWebhooks())
