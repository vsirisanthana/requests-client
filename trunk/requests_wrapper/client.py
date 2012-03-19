from urlparse import urlparse
import requests
from requests import *
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, SimpleCookie

from requests_wrapper.cache import CacheManager


CACHE_MANAGER = CacheManager()      # A singleton cache manager


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
    url_obj = urlparse(url)
    cookies = cache.get('cookies')
    domain_cookie = cookies.get(url_obj.netloc) if cookies else None

    # Construct Django HttpRequest object
    http_request = HttpRequest()
    http_request.path = url
    http_request.method = 'GET'
    http_request.META = {}
    http_request.COOKIES = domain_cookie or dict()
    # HttpRequest.META in Django prefixes each header with HTTP_
    if kwargs.has_key('headers'):
        for key, value in kwargs['headers'].items():
            http_request.META['HTTP_'+key.upper().replace('-', '_')] = value

    response = CACHE_MANAGER.process_request(http_request)
    if response:
        if queue: queue.put(response)
        return response

    CACHE_MANAGER.patch_if_modified_since_header(http_request)
    CACHE_MANAGER.patch_if_none_match_header(http_request)

    # Copy HttpRequest headers back
    if http_request.META.items():
        if not kwargs.has_key('headers'):
            kwargs['headers'] = {}
        for key, value in http_request.META.items():
            if key.startswith('HTTP_') or key in ['CONTENT_LENGTH', 'CONTENT_TYPE']:
                key = key.replace('HTTP_', '').replace('_', '-').title()
                kwargs['headers'][key] = value

    # set cookie
    if domain_cookie:
        set_cookie = {}
        for k, v in domain_cookie.items():
            set_cookie.update({k:v.value})
        kwargs['cookies'] = set_cookie
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

    # 8. Handle simple cookie :)

    # Handle 304
    if response.status_code == 304:
        response = CACHE_MANAGER.process_304_response(http_request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(url, **kwargs)
    
    #handle cookie
    if response.cookies:
        cookies = cache.get('cookie') or {}
        domain = url_obj.netloc
        if not domain in cookies.keys():
            cookies[domain] = {}

        domain_cookies = cookies[domain]
        cookie = SimpleCookie()
        cookie.load(response.headers['set-cookie'])
        domain_cookies.update(cookie)
        cache.set('cookies', cookies)

    #Update cache if cache-control is not no-cache
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:

        http_response = HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/html'))
        for header in response.headers:
            http_response[header] = response.headers[header]

        CACHE_MANAGER.process_response(http_request, http_response)

    if queue: queue.put(response)
    return response
