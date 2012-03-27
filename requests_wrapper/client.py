import requests
from requests import *

from cache import CacheManager
from cookie import extract_cookie, get_domain_cookie
from default_cache import get_default_cache


CACHE_MANAGER = CacheManager(key_prefix='dogbutler', cache=get_default_cache())      # A singleton cache manager


class Request:

    def __init__(self, url, method='GET', **kwargs):
        self.path = url
        self.method = method
        self.headers = kwargs.get('headers', {})

    def get_full_path(self):
        return self.path


requests.Response.has_header = lambda self, header: header in self.headers
requests.Response.__getitem__ = lambda self, header: self.headers[header]


def get(url, queue=None, **kwargs):
    # Get default cache
    cache = get_default_cache()

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

    response = CACHE_MANAGER.process_request(request)
    if response is not None:
        if queue: queue.put(response)
        return response

    CACHE_MANAGER.patch_if_modified_since_header(request)
    CACHE_MANAGER.patch_if_none_match_header(request)

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
        response = CACHE_MANAGER.process_304_response(request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(url, **kwargs)
    
    #handle cookie
    extract_cookie(url, response)

    #Update cache if cache-control is not no-cache
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:
        CACHE_MANAGER.process_response(request, response)

    if queue: queue.put(response)
    return response
