from django.core.cache import cache


def has_obtained_redis_lock(key, timeout=30):
    return cache.set(key, True, timeout=timeout, nx=True)


def release_redis_lock(key):
    cache.delete(key)
