import sqlite3
import sys

if (len(sys.argv) < 2):
    print('error: no moderator id')
    exit(1)

conn = sqlite3.connect('discordbot.db', isolation_level=None)
cursor = conn.cursor()

tables = [
    "CREATE TABLE IF NOT EXISTS channels (id integer PRIMARY KEY, channel_id integer NOT NULL)",
    "CREATE TABLE IF NOT EXISTS modlist (id integer PRIMARY KEY, user_id integer NOT NULL)",
    "CREATE TABLE IF NOT EXISTS notify (id integer PRIMARY KEY, username text NOT NULL, userid integer, channels text NOT NULL)"
]

for create_table_query in tables:
    cursor.execute(create_table_query)

cursor.executemany('INSERT INTO modlist(user_id) values (?)', [(int(arg),) for arg in sys.argv[1:]])