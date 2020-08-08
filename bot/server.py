import threading
import asyncio
import re

from utils import processPostRequest, logger
from flask import Flask, request, Response
from gevent.pywsgi import WSGIServer
from globals import cfg, client


class FlaskApp(threading.Thread):

    app = Flask(__name__)

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        wsgi = WSGIServer(('0.0.0.0', cfg['FlaskAppPort']), self.app, error_log=logger)
        wsgi.serve_forever()

    @staticmethod
    @app.route('/', methods=['GET', 'POST'])
    def result():
        if request.method == 'GET':
            if request.query_string:
                echo = re.search(r'hub\.challenge=([a-zA-Z\d\-_]+)&', request.query_string.decode('utf-8'))
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


server = FlaskApp()
