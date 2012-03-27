from dummycache.cache import Cache

DEFAULT_CACHE = Cache()
DEFAULT_COOKIE_CACHE = Cache()
DEFAULT_REDIRECT_CACHE = Cache()

def get_default_cache():
    return DEFAULT_CACHE

def set_default_cache(cache):
    global DEFAULT_CACHE
    DEFAULT_CACHE = cache

def get_default_cookie_cache():
    return DEFAULT_COOKIE_CACHE

def set_default_cookie_cache(cache):
    global DEFAULT_COOKIE_CACHE
    DEFAULT_COOKIE_CACHE = cache

def get_default_redirect_cache():
    return DEFAULT_REDIRECT_CACHE

def set_default_redirect_cache(cache):
    global DEFAULT_REDIRECT_CACHE
    DEFAULT_REDIRECT_CACHE = cache