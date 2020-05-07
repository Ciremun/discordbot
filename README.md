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

run `token_setup.py` to add discord bot token, twitch client id & helix api oauth, channel ids to listen and stream notify, user ids for bot moderators  


## global variables

`color_roles_limit` (int)  
`notify_enabled` (boolean)  
`stream_discord_embed_hex6` (string): stream notification embed line color, six-digit HEX color  
`prefix` (string):  chat command prefix  
`notify_sleep_time` (numeric): twitch check interval in seconds  

## commands

`colorinfo <#hex or rgb>` - get color image  
`nocolor` - remove color role  
`color <#hex or rgb>` - get color role, replace if exists  
`colors` - list created color roles  
`info` - uptime, bot channels, modlist  

moderators:  
`nocolors` - delete all color roles  
`channel <channel_id>` - bot will respond only in added channels, add channel if <channel_id> not in database, remove if present  
`notify <twitch_login> <discord_channel_id>` - twitch stream notify, it will add stream if <discord_channel_id> not in database, remove if present, update if differs  
