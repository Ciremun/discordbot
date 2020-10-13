import sqlite3

conn = sqlite3.connect('discord.db', isolation_level=None)
cursor = conn.cursor()

tables = [
    "CREATE TABLE IF NOT EXISTS channels (id integer PRIMARY KEY, channel_id integer NOT NULL)",
    "CREATE TABLE IF NOT EXISTS modlist (id integer PRIMARY KEY, user_id integer NOT NULL)",
    "CREATE TABLE IF NOT EXISTS notify (id integer PRIMARY KEY, username text NOT NULL, userid integer, channels text NOT NULL)"
]
for create_table_query in tables:
    cursor.execute(create_table_query)

moderators = input('Enter moderator IDs\n')

if moderators:
    moderators = [(int(x),) for x in moderators.split()]
    cursor.executemany('INSERT INTO modlist(user_id) values (?)', moderators)
