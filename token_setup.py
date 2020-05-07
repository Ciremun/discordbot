import sqlite3

conn = sqlite3.connect('db/discord_data.db')
c = conn.cursor()
tables = [{'channels': 'channel_id'}, {'modlist': 'user_id'}]

token = input('discord token?\n')
client_id = input('twitch app client id?\n')
twitch_helix_oauth = input('twitch helix api oauth?\n')

with open('tokens', 'w') as f:
    f.write(f'discord_token {token}\n'
            f'client_id {client_id}\n'
            f'twitch_oauth {twitch_helix_oauth}')
with conn:
    c.execute(f'delete from notify')

for table_dict in tables:
    for table, table_column in table_dict.items():
        ids = input(f'\nadd discord channel/user ids for {table} table\n')
        ids_tuples = [(int(i),) for i in ids.split(',')]
        with conn:
            c.execute(f'delete from {table}')
            c.executemany(f'insert into {table} ({table_column}) values (?)', ids_tuples)
