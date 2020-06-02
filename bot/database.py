import sqlite3

from decorators import connQuery, regularQuery

class DiscordData:

    def __init__(self):
        self.conn = sqlite3.connect('db/discord_data.db', check_same_thread=False)
        self.c = self.conn.cursor()

    def getBotChannels(self):
        return [i[0] for i in self.get_channels()]

    def getModlist(self):
        return [i[0] for i in self.get_modlist()]

    def getStreams(self):
        return {uname: {'userid': uid, 'channels': [int(x) for x in channels.split(',')]} 
                        for uname, uid, channels in self.get_twitch_notify()}

    @connQuery
    def connect_channel(self, channel_id: int):
        self.c.execute('INSERT INTO channels (channel_id) VALUES (:channel_id)', {'channel_id': channel_id})

    @connQuery
    def disconnect_channel(self, channel_id: int):
        self.c.execute('DELETE FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})

    @regularQuery
    def get_channels(self):
        self.c.execute('SELECT channel_id FROM channels')
        return self.c.fetchall()

    @regularQuery
    def get_channel_by_id(self, channel_id: int):
        self.c.execute('SELECT channel_id FROM channels WHERE channel_id = :channel_id', {'channel_id': channel_id})
        return self.c.fetchall()

    @regularQuery
    def get_twitch_notify(self):
        self.c.execute('SELECT username, userid, channels FROM notify')
        return self.c.fetchall()

    @regularQuery
    def get_modlist(self):
        self.c.execute('SELECT user_id FROM modlist')
        return self.c.fetchall()

    @connQuery
    def addNotify(self, username: str, channels: str):
        self.c.execute('INSERT INTO notify (username, channels) VALUES (:username, :channels)',
                        {'username': username, 'channels': channels})
        from utils import webhookStreamsRequest
        from globals import client
        client.loop.create_task(webhookStreamsRequest(username, 'subscribe'))

    @connQuery
    def removeNotify(self, username: str, channels: str, userid=None):
        if userid is None:
            self.c.execute(
            'DELETE FROM notify WHERE username = :username and channels = :channels and userid is null',
            {'username': username, 'channels': channels})
            return
        self.c.execute(
            'DELETE FROM notify WHERE username = :username and channels = :channels and userid = :userid',
            {'username': username, 'channels': channels, 'userid': userid})
        from utils import webhookStreamsRequest
        from globals import client
        client.loop.create_task(webhookStreamsRequest(username, 'unsubscribe', userid=userid))
        

    @connQuery
    def updateNotifyChannels(self, username: str, channels: str, newChannels: str, userid=None):
        if userid is None:
            self.c.execute(
                'UPDATE notify SET channels = :newChannels WHERE username = :username and channels = :channels '
                'and userid is null',
                {'username': username, 'channels': channels, 'newChannels': newChannels})
            return
        self.c.execute(
                'UPDATE notify SET channels = :newChannels WHERE username = :username and channels = :channels '
                'and userid = :userid',
                {'username': username, 'channels': channels, 'newChannels': newChannels, 'userid': userid})
    
    @connQuery
    def addNotifyUserID(self, username: str, userid: int):
        self.c.execute( 'UPDATE notify SET userid = :userid WHERE username = :username and userid is null',
                        {'username': username,  'userid': userid})


    @regularQuery
    def getNotifyChannelsByName(self, username: str):
        self.c.execute('SELECT channels, userid FROM notify WHERE username = :username', {'username': username})
        return self.c.fetchall()

db = DiscordData()
