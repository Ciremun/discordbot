import os
import psycopg2

import src.config
from .decorators import acquireLock

conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
conn.autocommit = True
cursor = conn.cursor()

tables = [
    "CREATE TABLE IF NOT EXISTS channels (id SERIAL PRIMARY KEY, channel_id bigint NOT NULL)",
    "CREATE TABLE IF NOT EXISTS modlist (id SERIAL PRIMARY KEY, user_id bigint NOT NULL)",
    "CREATE TABLE IF NOT EXISTS notify (id SERIAL PRIMARY KEY, username text NOT NULL, userid integer, channels text NOT NULL)"
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


@acquireLock
def connect_channel(channel_id: int):
    cursor.execute(
        'INSERT INTO channels (channel_id) VALUES (%s)', (channel_id,))


@acquireLock
def disconnect_channel(channel_id: int):
    cursor.execute('DELETE FROM channels WHERE channel_id = %s', (channel_id,))


@acquireLock
def get_bot_channels():
    cursor.execute('SELECT channel_id FROM channels')
    return [i[0] for i in cursor.fetchall()]


@acquireLock
def get_channel_by_id(channel_id: int):
    cursor.execute(
        'SELECT channel_id FROM channels WHERE channel_id = %s', (channel_id,))
    return cursor.fetchall()


@acquireLock
def get_twitch_notify():
    cursor.execute('SELECT username, userid, channels FROM notify')
    return cursor.fetchall()


@acquireLock
def getModlist():
    cursor.execute('SELECT user_id FROM modlist')
    return [i[0] for i in cursor.fetchall()]


@acquireLock
def addNotify(username: str, channels: str):
    cursor.execute(
        'INSERT INTO notify (username, channels) VALUES (%s, %s)', (username, channels))


@acquireLock
def removeNotify(username: str, channels: str, userid=None):
    if userid is None:
        cursor.execute(
            'DELETE FROM notify WHERE username = %s and channels = %s and userid IS NULL', (username, channels))
        return
    cursor.execute(
        'DELETE FROM notify WHERE username = %s and channels = %s and userid = %s', (username, channels, userid))


@acquireLock
def updateNotifyChannels(username: str, channels: str, newChannels: str, userid=None):
    if userid is None:
        cursor.execute(
            'UPDATE notify SET channels = %s WHERE username = %s and channels = %s '
            'and userid IS NULL', (newChannels, username, channels))
        return
    cursor.execute(
        'UPDATE notify SET channels = %s WHERE username = %s and channels = %s '
        'and userid = %s', (newChannels, username, channels, userid))


@acquireLock
def addNotifyUserID(username: str, userid: int):
    cursor.execute(
        'UPDATE notify SET userid = %s WHERE username = %s and userid IS NULL', (userid, username))


def getNotifyChannelsByName(username: str):
    cursor.execute(
        'SELECT channels, userid FROM notify WHERE username = %s', (username,))
    return cursor.fetchall()
