from dummycache.cache import Cache

DEFAULT_CACHE = Cache()


def get_default_cache():
    return DEFAULT_CACHE

def set_default_cache(cache):
    global DEFAULT_CACHE
    DEFAULT_CACHE = cache