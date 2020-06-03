import sqlite3

conn = sqlite3.connect('db/discord_data.db')
c = conn.cursor()

for table in ['channels', 'modlist', 'notify']:
    with conn:
        c.execute(f'delete from {table}')
with conn:
    c.execute('vacuum')

moderators = input('Enter comma separated bot moderator IDs\n')

if moderators:
    with conn:
        moderators = [(int(x),) for x in moderators.split(',')]
        c.executemany('INSERT INTO modlist(user_id) values (?)', moderators)
