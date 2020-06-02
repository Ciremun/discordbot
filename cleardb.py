import sqlite3

conn = sqlite3.connect('db/discord_data.db')
c = conn.cursor()

for table in ['channels', 'modlist', 'notify']:
    with conn:
        c.execute(f'delete from {table}')
with conn:
    c.execute('vacuum')
