from datetime import datetime, timedelta
from django.utils.cache import get_max_age, patch_response_headers
import requests

from django.core.cache import cache

from django.http import HttpRequest

from django.views.decorators.cache import cache_page

#cache = dict(_responses=dict())


def get_cache_response(url):
    """
    Checks whether the page is already cached and returns the cached
    version if available.
    """
    cache_key = get_cache_key(request, self.key_prefix, 'GET', cache=self.cache)
    if cache_key is None:
        return None # No cache information available, need to send a request.
    response = cache.get(cache_key, None)

    if response is None:
        return None# No cache information available, need to send a request

    return response

def process_response(response, allowable_codes=(200,)):
    """Sets the cache, if needed."""

    if not response.status_code == 200:
        return response
        # Try to get the timeout from the "max-age" section of the "Cache-

    # Control" header before reverting to using the default cache_timeout
    # length.
    timeout = get_max_age(response)
    if timeout == None:
        timeout = self.cache_timeout
    elif timeout == 0:
        # max-age was set to 0, don't bother caching.
        return response
    patch_response_headers(response, timeout)
    if timeout:
        cache_key = learn_cache_key(request, response, timeout, self.key_prefix, cache=self.cache)
        if hasattr(response, 'render') and callable(response.render):
            response.add_post_render_callback(
                lambda r: cache.set(cache_key, r, timeout)
            )
        else:
            cache.set(cache_key, response, timeout)
    return response

def get(url, **kwargs):

    response = get_cache_response(url)
    if response:
        return response

    return requests.get(url, hooks=dict(response=process_response), **kwargs)


def post(url, **kwargs):
    return requests.post(url, **kwargs)

