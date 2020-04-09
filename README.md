# shtcd discord bot
 
allows you to:  
manage discord server color roles (create/assign/delete)  
get twitch live notifications in discord announcement channels  

## Install

### req.txt

```
discord>=1.0.1  
Pillow>=7.0.0  
requests>=2.23.0  
```

### tokens, channel/user ids

run `token_setup.py` to add discord bot token, twitch app client id,  
channel ids to listen and stream notify, user ids for bot moderators  

use `db/db_query.py` to execute sql queries  

## global variables

color_roles_limit(int)  
notify_enabled(bool)  
notify_twitcher_usernames(list of strings) - twitch usernames to check   
stream_discord_embed_hex6(hex6 color str) - stream notification embed line color  
prefix(str) - chat command prefix  
notify_sleep_time(int, float) - twitch check interval in seconds  

## commands

everyone: color, nocolor, colorinfo, colors, help, info  
bot moderators: channel, nocolors, notify, exit  

see bot help for more info  
