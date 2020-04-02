# CiremunDiscordBot

simple discord bot  
allows you to:  
manage discord server color roles (create/assign/delete)  
get twitch stream notification in discord announcement channel  

## Install

### req.txt

```
discord>=1.0.1  
Pillow>=7.0.0  
requests>=2.23.0  
```

### tokens

"tokens" file, .py file directory

```
discord_token <token_here>
twitch_app_client_id <client_id_here>
```

### database

using db/db_query.py clear all tables then add channel and mod ids  

```
delete from channels
delete from notify
delete from modlist
```

```
insert into channels (channel_id) values (<channel_id_here>)
insert into notify (notify_channel_id) values (<channel_id_here>)
insert into modlist (user_id) values (<user_id_here>)
```

created tables list:  

```
select * from tables
```

table columns info:  

```
pragma table_info(<table_name_here>)
```

## global variables

color_roles_limit(int)  
notify_enabled(bool)  
notify_twitcher_username(str) - twitch username to check  
discord_guild_id(int) - discord server to get random emote link  
stream_discord_embed_hex6(hex6 color str) - stream notification embed line color  

## commands
prefix = !  
everyone: color, nocolor, colorinfo, colors, ttv, help  
bot moderators: connect, disconnect, connections, nocolors, exit  
