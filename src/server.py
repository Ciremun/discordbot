import asyncio
import re
import os
from threading import Thread

from gevent.pywsgi import WSGIServer
from flask import Flask, request, Response

from .client import client, processPostRequest
from .log import logger

app = Flask(__name__)
hub_challenge_regex = r'hub\.challenge=([a-zA-Z\d\-_]+)&'


def run():
    wsgi = WSGIServer(('0.0.0.0', int(os.environ.get('PORT'))), app)
    logger.info('run server')
    wsgi.serve_forever()


@app.route('/', methods=['GET', 'POST'])
def result():
    if request.method == 'GET':
        if request.query_string:
            echo = re.search(hub_challenge_regex,
                             request.query_string.decode('utf-8'))
            if echo:
                return echo.group(1), 200
    elif request.headers.get('X-Hub-Signature'):
        asyncio.run_coroutine_threadsafe(processPostRequest({
            'args': request.args,
            'bytes': request.data,
            'json': request.get_json(),
            'X-Hub-Signature': request.headers['X-Hub-Signature'],
            'notifyID': request.headers['Twitch-Notification-Id']
        }), client.loop)
    return Response(status=200)


serverThread = Thread(target=run)
serverThread.start()
