
if __name__ == '__main__':
    from src.config import cfg, keys
    if cfg['notify']:
        import src.server
    from src.client import client
    client.run(keys['DiscordToken'])
