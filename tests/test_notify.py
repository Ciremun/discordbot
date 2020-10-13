import unittest
import random
import hmac
import sys
sys.path.append('.')
from unittest.mock import MagicMock
from copy import deepcopy

from src.config import keys, cfg
cfg['notify'] = False

import src.client
from src.client import client, streams, processPostRequest, randomGuildEmote
from src.log import logger

class Mock:
    def __init__(self):
        self.emojis = []
        self.send = lambda x : None
        self.edit = lambda **kwargs : None

async def mock():
    return Mock()

random.choice = MagicMock(123)
randomGuildEmote = MagicMock(123)
client.get_guild = MagicMock(Mock())
client.get_channel = MagicMock(Mock())
client.loop.create_task = lambda x : mock()

sign_success = f"sha256={hmac.new(keys['secret'].encode(), b'success', 'sha256').hexdigest()}"
sign_fail = f"sha256={hmac.new(keys['secret'].encode(), b'fail', 'sha256').hexdigest()}"

request_form = {
    'X-Hub-Signature': None,
    'args': {'u': 'shtcd'},
    'notifyID': 'abcd-efgh-ijkl-mnop',
    'bytes': b'success',
    'json': {
        'data': 
        [
            {
            'game_id': '513181',
            'id': '39661965500',
            'language': 'en',
            'started_at': '2020-10-13T17:31:11Z',
            'tag_ids': None,
            'thumbnail_url': 'pajaDank.jpg',
            'title': 'title',
            'type': 'live',
            'user_id': '469085101',
            'user_name': 'shtcd',
            'viewer_count': 0
            }
        ]
    }
}

request = None

class TestWebhook(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        global request
        src.client.streams.clear()
        request = deepcopy(request_form)
        logger.debug(f'TEST START {self._testMethodName}')

    def tearDown(self):
        logger.debug(f'TEST END {self._testMethodName}')

    async def test_webhook_success_single(self):
        request['X-Hub-Signature'] = sign_success
        result = await processPostRequest(request)
        self.assertEqual(result, True)

    async def test_webhook_success_multi(self):
        request['X-Hub-Signature'] = sign_success
        start = await processPostRequest(request)
        request['args']['u'] = 'ciremun'
        request['notifyID'] = 'ponm-lkji-hgfe-dcba1'
        start2 = await processPostRequest(request)
        request['json']['data'].clear()
        request['notifyID'] = 'ponm-lkji-hgfe-dcba2'
        end = await processPostRequest(request)
        request['args']['u'] = 'shtcd'
        request['notifyID'] = 'ponm-lkji-hgfe-dcba3'
        end2 = await processPostRequest(request)
        self.assertEqual(start, True)
        self.assertEqual(start2, True)
        self.assertEqual(end, True)
        self.assertEqual(end2, True)

    async def test_webhook_fail_hmac(self):
        request['X-Hub-Signature'] = sign_fail
        result = await processPostRequest(request)
        self.assertEqual(result, None)

    async def test_webhook_fail_duplicate(self):
        request['X-Hub-Signature'] = sign_success
        await processPostRequest(request)
        result = await processPostRequest(request)
        self.assertEqual(result, None)

    async def test_webhook_fail_no_messages(self):
        request['X-Hub-Signature'] = sign_success
        await processPostRequest(request)
        src.client.streams['shtcd']['notify_messages'].clear()
        request['notifyID'] = 'ponm-lkji-hgfe-dcba'
        request['json']['data'].clear()
        result = await processPostRequest(request)
        self.assertEqual(result, None)

if __name__ == "__main__":
    unittest.main()
