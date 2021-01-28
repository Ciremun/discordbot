import os
import sqlite3

import src.config
from .decorators import acquireLock

conn = sqlite3.connect('discordbot.db', check_same_thread=False, isolation_level=None)
cursor = conn.cursor()
tables = [
"CREATE TABLE IF NOT EXISTS channels (id integer PRIMARY KEY, channel_id integer NOT NULL)",
"CREATE TABLE IF NOT EXISTS modlist (id integer PRIMARY KEY, user_id integer NOT NULL)",
"CREATE TABLE IF NOT EXISTS notify (id integer PRIMARY KEY, username text NOT NULL, userid integer, channels text NOT NULL)"
]

for create_table_query in tables:
    cursor.execute(create_table_query)

default_moderator_id = os.environ.get('DEFAULT_MODERATOR_ID')
if default_moderator is not None:
    cursor.execute('SELECT count(id) FROM modlist')
    if not cursor.fetchone():
        cursor.execute('INSERT INTO modlist (user_id) VALUES (?)', int(default_moderator_id))

def get_streams():
    return {uname: {'userid': uid, 'channels': [int(x) for x in channels.split()]} 
                    for uname, uid, channels in get_twitch_notify()}


@acquireLock
def connect_channel(channel_id: int):
    cursor.execute('INSERT INTO channels (channel_id) VALUES (:channel_id)', {'channel_id': channel_id})


@acquireLock
def disconnect_channel(channel_id: int):
    cursor.execute('DELETE FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})


@acquireLock
def get_bot_channels():
    cursor.execute('SELECT channel_id FROM channels')
    return [i[0] for i in cursor.fetchall()]


@acquireLock
def get_channel_by_id(channel_id: int):
    cursor.execute('SELECT channel_id FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})
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
    cursor.execute('INSERT INTO notify (username, channels) VALUES (:username, :channels)',
                    {'username': username, 'channels': channels})


@acquireLock
def removeNotify(username: str, channels: str, userid=None):
    if userid is None:
        cursor.execute(
        'DELETE FROM notify WHERE username = :username and channels = :channels and userid is null',
        {'username': username, 'channels': channels})
        return
    cursor.execute(
        'DELETE FROM notify WHERE username = :username and channels = :channels and userid = :userid',
        {'username': username, 'channels': channels, 'userid': userid})
    

@acquireLock
def updateNotifyChannels(username: str, channels: str, newChannels: str, userid=None):
    if userid is None:
        cursor.execute(
            'UPDATE notify SET channels = :newChannels WHERE username = :username and channels = :channels '
            'and userid is null',
            {'username': username, 'channels': channels, 'newChannels': newChannels})
        return
    cursor.execute(
            'UPDATE notify SET channels = :newChannels WHERE username = :username and channels = :channels '
            'and userid = :userid',
            {'username': username, 'channels': channels, 'newChannels': newChannels, 'userid': userid})


@acquireLock
def addNotifyUserID(username: str, userid: int):
    cursor.execute('UPDATE notify SET userid = :userid WHERE username = :username and userid is null',
                   {'username': username,  'userid': userid})


def getNotifyChannelsByName(username: str):
    cursor.execute('SELECT channels, userid FROM notify WHERE username = :username', {'username': username})
    return cursor.fetchall()
