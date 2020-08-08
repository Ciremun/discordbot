import asyncio
import threading
import globals as g

from log import logger


lock = threading.Lock()

def bot_command(*, name, check_func=None):
    def decorator(func):
        def wrapper(message):
            if callable(check_func) and not check_func(message):
                return False
            return func(message)
        g.commands[name] = wrapper
        return wrapper
    return decorator


def exponentBackoff(func):
    async def wrapper(*args, **kwargs):
        for exponent in range(1, 6):
            try:
                if await func(*args, **kwargs):
                    return
                raise Exception
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(5 ** exponent)
    return wrapper


def connQuery(func):
    def wrapper(self, *args, **kwargs):
        with self.conn:
            try:
                lock.acquire(True)
                return func(self, *args, **kwargs)
            finally:
                lock.release()
    return wrapper


def regularQuery(func):
    def wrapper(self, *args, **kwargs):
        try:
            lock.acquire(True)
            return func(self, *args, **kwargs)
        finally:
            lock.release()
    return wrapper
