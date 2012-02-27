from datetime import datetime, timedelta
import requests

from django.core.cache import cache

from django.http import HttpRequest

from django.views.decorators.cache import cache_page

#cache = dict(_responses=dict())


def _use_cache(url, expire_after=5):

    try:
        pointer = cache[url]
        stored_at, response = cache['_responses'][pointer]
    except KeyError:
        return False, None
    difference = datetime.now() - stored_at
    if difference < timedelta(minutes=expire_after):
        return True, response
    else:
        for r in response.history:
            del cache[r.url]
        del cache['_responses'][url]
        del cache[url]
        print 'sending request'
    return False, None

def _to_cache(response, allowable_codes=(200,)):
    if (response.status_code in allowable_codes
        and not hasattr(response, '_from_cache')):
        response._from_cache = True
        cache['_responses'][response.url] = datetime.now(), response
        cache[response.url] = response.url
        for r in response.history:
            cache[r.url] = response.url
    return response

def get(url, **kwargs):

    # try and get the cached GET response
    cache_key = get_cache_key(request, self.key_prefix, 'GET', cache=self.cache)

    if cache_key is None:
        _cache_update_cache = True

    response = cache.get(cache_key, None)

    if response is None:
        _cache_update_cache = True

    if response is not None:
        response = requests.get(url, **kwargs)

    if _cache_update_cache:
        cache_key = learn_cache_key()
        cache.set(cache_key, response, timeout)

    return response


def post(url, **kwargs):
    return requests.post(url, **kwargs)


