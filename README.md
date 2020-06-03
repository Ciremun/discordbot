# shtcd discord bot

allows you to:  
manage discord server color roles (create/assign/delete)  
get twitch live notifications in discord announcement channels  

![image](image.png)

## Install

### req

    discord>=1.0.1  
    Pillow>=7.0.0  
    requests>=2.23.0  
    Flask>=1.1.2  

Tested on Python 3.7.5

run `setupdb.py` to add bot mods and clear db  

### tokens.json

create `tokens.json`  

`DiscordToken` (str): discord bot token, [Discord Developer Portal](https://discord.com/developers)  
`Client-ID` (str): twitch application Client ID, create app in [Twitch Developer Console](https://dev.twitch.tv/console/apps)  
`ClientSecret` (str): generate new secret in twitch dev console (under Client ID)  
`ClientOAuth` (str): user OAuth token, [twitchapps](https://twitchapps.com/tokengen/) helps obtain  
`AppAccessToken` (str): server OAuth token obtained with POST request using ClientID and ClientSecret: [Twitch docs](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow)  
`callbackURL` (str): server URL to catch webhook requests  
`secret` (str): secret used to sign notification payloads  

### cfg.json

`rolesLimit` (int): guild color roles limit  
`notify` (boolean): fetch and send notifications?  
`embedHex6` (string): stream notification embed line color, six-digit HEX color  
`prefix` (str): bot command prefix  
`FlaskAppPort` (int): server port, `80` for http  

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
