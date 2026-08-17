import functools

from fastapi_cache import FastAPICache


def invalidate_cache(namespace: str):
    def decorator(fun):
        @functools.wraps(fun)
        async def inner(*args, **kwargs):
            await FastAPICache.clear(namespace=namespace)
            return await fun(*args, **kwargs)
        return inner
    return decorator