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
created tables list:  

```
select * from tables
```

insert channel_id to listen:  

```
insert into channels (channel_id) values (<channel_id_here>)
```

table columns info:  

```
pragma table_info(<table_name_here>)
```
