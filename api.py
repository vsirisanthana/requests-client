import requests
from requests import request, head, post, patch, put, delete, options, TooManyRedirects

from .cache import CacheManager
from .cookie import extract_cookie, get_domain_cookie
from .default_cache import get_default_cache
from .models import Request


DEFAULT_KEY_PREFIX = 'dogbutler'


def get(url, queue=None, **kwargs):
    # Get default cache
    cache = get_default_cache()
    cache_manager = CacheManager(key_prefix=DEFAULT_KEY_PREFIX, cache=cache)

    # check if the url is permanently redirect or not
    history = []
    while True:
        if url in history:
            raise TooManyRedirects()
        redirect_to = cache.get('redirect.%s' % url)
        if redirect_to is None:
            break
        url = redirect_to

    request = Request(url, method='GET', **kwargs)
    request.COOKIES = get_domain_cookie(url) or dict()

    response = cache_manager.process_request(request)
    if response is not None:
        if queue: queue.put(response)
        return response

    cache_manager.patch_if_modified_since_header(request)
    cache_manager.patch_if_none_match_header(request)

    # Update kwargs with new headers
    if request.headers: kwargs['headers'] = request.headers

    # set cookie
    if get_domain_cookie(url):
        kwargs['cookies'] = get_domain_cookie(url)
    response = requests.get(url, **kwargs)
    if response.history:
        request.path = response.url

        for r in response.history:
            if r.status_code == 301:
                #TODO: handle case of no Location header
                redirect_to = r.headers.get('Location')
                cache.set('redirect.%s' % r.url, redirect_to)

    # Handle 304
    if response.status_code == 304:
        response = cache_manager.process_304_response(request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(url, **kwargs)

    #handle cookie
    extract_cookie(url, response)

    #Update cache if cache-control is not no-cache
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:
        cache_manager.process_response(request, response)

    if queue: queue.put(response)
    return response
