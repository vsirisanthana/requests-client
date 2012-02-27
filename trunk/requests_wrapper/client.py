from datetime import datetime, timedelta
from django.utils.cache import get_max_age, patch_response_headers, get_cache_key
import requests

from django.core.cache import cache, get_cache

from django.http import HttpRequest, HttpResponse

from django.views.decorators.cache import cache_page

#cache = dict(_responses=dict())

from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware


#KEY_PREFIX = 'euam'


#def get_cache_response(request):
#    """
#    Checks whether the page is already cached and returns the cached
#    version if available.
#    """
#    cache_key = get_cache_key(request, KEY_PREFIX, 'GET', cache=get_cache(self.cache_alias))
#    if cache_key is None:
#        return None # No cache information available, need to send a request.
#    response = cache.get(cache_key, None)
#
#    if response is None:
#        return None# No cache information available, need to send a request
#
#    return response

#def process_response(response, allowable_codes=(200,)):
#    """Sets the cache, if needed."""
#
#    if not response.status_code == 200:
#        return response
#        # Try to get the timeout from the "max-age" section of the "Cache-
#
#    # Control" header before reverting to using the default cache_timeout
#    # length.
#    timeout = get_max_age(response)
#    if timeout == None:
#        timeout = self.cache_timeout
#    elif timeout == 0:
#        # max-age was set to 0, don't bother caching.
#        return response
#    patch_response_headers(response, timeout)
#    if timeout:
#        cache_key = learn_cache_key(request, response, timeout, self.key_prefix, cache=self.cache)
#        if hasattr(response, 'render') and callable(response.render):
#            response.add_post_render_callback(
#                lambda r: cache.set(cache_key, r, timeout)
#            )
#        else:
#            cache.set(cache_key, response, timeout)
#    return response

def get(url, **kwargs):

    # Construct Django HttpRequest object
    http_request = HttpRequest()
    http_request.path = url
    http_request.method = 'GET'
    http_request.META = kwargs['headers'] if kwargs.has_key('headers') else {}

    response = FetchFromCacheMiddleware().process_request(http_request)

#    response = get_cache_response(request)
    if response:
        return response

#    response = requests.get(url, hooks=dict(response=process_response), **kwargs)

    response = requests.get(url, **kwargs)

    #if no cache-control or cache-control == no-cache return responhse
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:

        http_response = HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/html'))
        for header in response.headers:
            http_response[header] = response.headers[header]


        UpdateCacheMiddleware().process_response(http_request, http_response)
    return response


def post(url, **kwargs):
    return requests.post(url, **kwargs)


