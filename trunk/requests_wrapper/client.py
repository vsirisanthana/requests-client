import requests
from requests import *

from cache import CacheManager
from cookie import extract_cookie, get_domain_cookie
from default_cache import cache


CACHE_MANAGER = CacheManager(key_prefix='dogbutler', cache=cache)      # A singleton cache manager


class Request:

    def __init__(self, url, method='GET', **kwargs):
        self.path = url
        self.method = method
        self.headers = kwargs.get('headers', {})

    def get_full_path(self):
        return self.path


DEFAULT_CONTENT_TYPE = 'text/html'

class Response(requests.Response):

    def __init__(self, content='', status=200, content_type=DEFAULT_CONTENT_TYPE):
        self.content = content
        self.status_code = status
        self.headers = {}


def has_header(self, header):
    return header in self.headers


requests.Response.has_header = lambda self, header: header in self.headers
requests.Response.__getitem__ = lambda self, header: self.headers[header]


def get(url, queue=None, **kwargs):

    # check if the url is permanently redirect or not
    history = []
    while True:
        if url in history:
            raise TooManyRedirects()
        redirect_to = cache.get('redirect.%s' % url)
        if redirect_to is None:
            break
        url = redirect_to

    http_request = Request(url, method='GET', **kwargs)
#    http_request.path = url
#    http_request.method = 'GET'
#    http_request.META = {}
    http_request.COOKIES = get_domain_cookie(url) or dict()

    # HttpRequest.META in Django prefixes each header with HTTP_
#    if kwargs.has_key('headers'):
#        for key, value in kwargs['headers'].items():
#            http_request.META['HTTP_'+key.upper().replace('-', '_')] = value

    response = CACHE_MANAGER.process_request(http_request)
    if response is not None:
        if queue: queue.put(response)
        return response

    CACHE_MANAGER.patch_if_modified_since_header(http_request)
    CACHE_MANAGER.patch_if_none_match_header(http_request)

    # Copy HttpRequest headers back
#    if http_request.META.items():
#        if not kwargs.has_key('headers'):
#            kwargs['headers'] = {}
#        for key, value in http_request.META.items():
#            if key.startswith('HTTP_') or key in ['CONTENT_LENGTH', 'CONTENT_TYPE']:
#                key = key.replace('HTTP_', '').replace('_', '-').title()
#                kwargs['headers'][key] = value

    if http_request.headers: kwargs['headers'] = http_request.headers

    # set cookie
    if get_domain_cookie(url):
        kwargs['cookies'] = get_domain_cookie(url)
    response = requests.get(url, **kwargs)
    if response.history:
        http_request.path = response.url

        for r in response.history:
            if r.status_code == 301:
                #TODO: handle case of no Location header
                redirect_to = r.headers.get('Location')
                cache.set('redirect.%s' % r.url, redirect_to)

    # TODO:
    # 1. Check for 301 -- DONE!!!

    # 2. Cache 2xx and 4xx --- DONE!!!

    # 3. Send If-Modified-Since if response has Last-Modified --- DONE!!!

    # 4. Send If-None-Match if response has ETag --- DONE!!!

    # 5. Handle 304 --- DONE!!!

    # 6. Try parellel requests --- DONE!!! (Support GET only)

    # 7. Try HTTPS

    # 8. Handle simple domain cookie :) --- DONE!!

    # Handle 304
    if response.status_code == 304:
        response = CACHE_MANAGER.process_304_response(http_request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(url, **kwargs)
    
    #handle cookie
    extract_cookie(url, response)

    #Update cache if cache-control is not no-cache
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:

#        http_response = HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/html'))
#        for header in response.headers:
#            http_response[header] = response.headers[header]

#        CACHE_MANAGER.process_response(http_request, http_response)

        CACHE_MANAGER.process_response(http_request, response)

    if queue: queue.put(response)
    return response
