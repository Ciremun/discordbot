import sqlite3
import os

conn = sqlite3.connect('discord_data.db')

c = conn.cursor()

print('+sql')

while True:
    try:
        inp = input()
        if inp == '!exit':
            conn.close()
            os._exit(0)
        if inp:
            with conn:
                c.execute(inp)
            print('\n')
            print(c.fetchall())
            print('\n')
            inp = ''
    except Exception as e:
        print(e)
