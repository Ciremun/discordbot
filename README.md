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

using db/db_query.py add channel and user ids  

insert channel_id, notify_channel_id, mod user_id:  

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
