import asyncio
import threading

from .log import logger

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


def acquireLock(func):
    lock = threading.Lock()
    def wrapper(*args, **kwargs):
        try:
            lock.acquire(True)
            return func(*args, **kwargs)
        finally:
            lock.release()
    return wrapper
