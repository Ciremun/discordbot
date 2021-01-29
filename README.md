# shtcd discord bot

manage discord server color roles (create/assign/delete)  
get twitch live notifications in discord announcement channels  

![image](image.png)

## Install

[Python 3](https://www.python.org/)

### env

|       Variable       |  Type  |                                        Value
|----------------------|--------|----------------------------------------------------------------------------------------------|
|`DISCORD_TOKEN`       | `str`  | discord bot token, [discord developer portal](https://discord.com/developers)                |
|`CLIENT_ID`           | `str`  | twitch application Client ID, create app in [twitch developer console](https://dev.twitch.tv/console/apps)                                                                                           |  
|`CLIENT_SECRET`       | `str`  | generate new secret in twitch dev console (under Client ID)                                  |
|`CLIENT_OAUTH`        | `str`  | user OAuth token, [twitchapps](https://twitchapps.com/tokengen/) helps obtain                |
|`APP_ACCESS_TOKEN`    | `str`  | server OAuth token [twitch docs](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow)  
|`CALLBACK_URL`        | `str`  | server URL to catch webhook requests                                                         |
|`SECRET`              | `str`  | secret used to sign notification payloads                                                    |
|`PORT`                | `int`  | flask application port                                                                       |
|`DEFAULT_MODERATOR_ID`| `int`  | default bot moderator                                                                        |

### cfg.json

`prefix`       (str): bot command prefix  
`rolesLimit`   (int): guild color roles limit  
`notify`       (bool): fetch and send notifications?  
`embedHex6`    (str): stream notification embed line color, six-digit HEX color  
`footerText`   (str): stream notification embed footer text  

## commands

`colorinfo <#hex or rgb>` - get color image, rgb and hex  
`nocolor` - remove your color role  
`color <#hex or rgb>` - get color role, replace if exists  
`colors` - list created color roles  
`info` - uptime, channels, modlist  

### moderators
`nocolors` - delete all color roles  
`channel <channel_id>` - bot will respond only in added channels (except mods), add if `<channel_id>` not in database, remove if present  
`notify <twitch login> <space separated channel IDs>` - twitch streams notify, add stream if `<channel IDs>` not in database, remove if present, update if differs  
`mute <space separated mentions/userIDs>` - add/remove "Muted" role, you have to create role, edit channel permissions before using it  
