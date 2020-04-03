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

### tokens, channel/user ids

run `token_setup.py` to add discord bot token, twitch app client id,  
channel ids for bot and stream notify, user ids for bot moderators  

use `db/db_query.py` to execute sql queries  

## global variables

color_roles_limit(int)  
notify_enabled(bool)  
notify_twitcher_username(str) - twitch username to check  
discord_guild_id(int) - discord server to get random emote link  
stream_discord_embed_hex6(hex6 color str) - stream notification embed line color  
prefix(str) - chat command prefix  

## commands

everyone: color, nocolor, colorinfo, colors, ttv, help  
bot moderators: connect, disconnect, connections, nocolors, exit  
