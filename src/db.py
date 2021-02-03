import os
import threading
import json
from typing import Callable, Any, Dict, Tuple

import psycopg2

from .log import logger

conn = None
cursor = None
lock = threading.Lock()


def db_connect():
    global conn, cursor
    if conn is not None:
        conn.close()
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
    conn.autocommit = True
    cursor = conn.cursor()


def db(func: Callable) -> Callable:
    global lock

    def wrapper(*args, **kwargs) -> Any:
        try:
            lock.acquire(True)
            return func(*args, **kwargs)
        except psycopg2.OperationalError:
            logger.info('try reconnect')
            db_connect()
            return func(*args, **kwargs)
        finally:
            lock.release()
    wrapper.__name__ = func.__name__
    return wrapper


@db
def db_init():

    tables = [
        "CREATE TABLE IF NOT EXISTS channels (id SERIAL PRIMARY KEY, channel_id bigint NOT NULL)",
        "CREATE TABLE IF NOT EXISTS modlist (id SERIAL PRIMARY KEY, user_id bigint NOT NULL)",
        "CREATE TABLE IF NOT EXISTS notify (id SERIAL PRIMARY KEY, username text NOT NULL, userid integer, channels text NOT NULL)",
        "CREATE TABLE IF NOT EXISTS streams_state (id SERIAL PRIMARY KEY, streams json NOT NULL)"
    ]

    for create_table_query in tables:
        cursor.execute(create_table_query)

    default_moderator_id = os.environ.get('DEFAULT_MODERATOR_ID')
    if default_moderator_id is not None:
        cursor.execute('SELECT 1 FROM modlist')
        if not cursor.fetchone():
            cursor.execute('INSERT INTO modlist (user_id) VALUES (%s)',
                           (int(default_moderator_id),))


def get_streams():
    return {uname: {'userid': uid, 'channels': [int(x) for x in channels.split()]}
            for uname, uid, channels in get_twitch_notify()}


@db
def connect_channel(channel_id: int):
    cursor.execute(
        'INSERT INTO channels (channel_id) VALUES (%s)', (channel_id,))


@db
def disconnect_channel(channel_id: int):
    cursor.execute('DELETE FROM channels WHERE channel_id = %s', (channel_id,))


@db
def get_bot_channels():
    cursor.execute('SELECT channel_id FROM channels')
    return [i[0] for i in cursor.fetchall()]


@db
def get_channel_by_id(channel_id: int):
    cursor.execute(
        'SELECT channel_id FROM channels WHERE channel_id = %s', (channel_id,))
    return cursor.fetchall()


@db
def get_twitch_notify():
    cursor.execute('SELECT username, userid, channels FROM notify')
    return cursor.fetchall()


@db
def getModlist():
    cursor.execute('SELECT user_id FROM modlist')
    return [i[0] for i in cursor.fetchall()]


@db
def addNotify(username: str, channels: str):
    cursor.execute(
        'INSERT INTO notify (username, channels) VALUES (%s, %s)', (username, channels))


@db
def removeNotify(username: str, channels: str, userid=None):
    if userid is None:
        cursor.execute(
            'DELETE FROM notify WHERE username = %s and channels = %s and userid IS NULL', (username, channels))
        return
    cursor.execute(
        'DELETE FROM notify WHERE username = %s and channels = %s and userid = %s', (username, channels, userid))


@db
def updateNotifyChannels(username: str, channels: str, newChannels: str, userid=None):
    if userid is None:
        cursor.execute(
            'UPDATE notify SET channels = %s WHERE username = %s and channels = %s '
            'and userid IS NULL', (newChannels, username, channels))
        return
    cursor.execute(
        'UPDATE notify SET channels = %s WHERE username = %s and channels = %s '
        'and userid = %s', (newChannels, username, channels, userid))


@db
def addNotifyUserID(username: str, userid: int):
    cursor.execute(
        'UPDATE notify SET userid = %s WHERE username = %s and userid IS NULL', (userid, username))


@db
def getNotifyChannelsByName(username: str):
    cursor.execute(
        'SELECT channels, userid FROM notify WHERE username = %s', (username,))
    return cursor.fetchall()


@db
def update_streams_state(streams: Dict):
    cursor.execute('SELECT 1 FROM streams_state')
    if cursor.fetchone():
        logger.info('UPDATE streams_state')
        cursor.execute('UPDATE streams_state SET streams = %s',
                       (json.dumps(streams),))
    else:
        logger.info('INSERT INTO streams_state')
        cursor.execute(
            'INSERT INTO streams_state (streams) VALUES (%s)', (json.dumps(streams),))


@db
def get_streams_state() -> Tuple[Dict]:
    cursor.execute('SELECT streams FROM streams_state')
    logger.info('get_streams_state')
    return cursor.fetchone() or ({},)


db_connect()
db_init()