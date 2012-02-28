import requests
from requests import *
from django.http import HttpRequest, HttpResponse
from requests_wrapper.cache import CacheManager

from django.core.cache import cache

def get(url, **kwargs):

    # check if the url is permanently redirect or not
    redirect_to = cache.get('redirect.%s' % url)
    if redirect_to:
        return get(redirect_to, **kwargs)


    # Construct Django HttpRequest object
    http_request = HttpRequest()
    http_request.path = url
    http_request.method = 'GET'
    http_request.META = {}

    # HttpRequest.META in Django prefixes each header with HTTP_
    if kwargs.has_key('headers'):
        for key, value in kwargs['headers'].items():
            http_request.META['HTTP_'+key.upper().replace('-', '_')] = value

    cache_manager = CacheManager()
    response = cache_manager.process_request(http_request)
    if response:
        return response

    kwargs['allow_redirects'] = False
    response = requests.get(url, **kwargs)

    if response.status_code == 301:
        #TODO: handle case of no Location header
        redirect_to = response.headers.get('Location')
        cache.set('redirect.%s' % url, redirect_to )
        return get(redirect_to, **kwargs)

    # TODO:
    # 1. Check for 301 -- DONE!!!
#    if response.status_code == 301:
#        cache.set('redirect.%s' % url, )

    # 2. Cache 2xx and 4xx --- DONE!!!

    # 3. Send If-Modified-Since if response has Last-Modified

    # 4. Send If-None-Match if response has ETag

    #Update cache if cache-control is not no-cache
    cache_control = response.headers.get('Cache-Control')
    if cache_control is not None and 'no-cache' not in cache_control:

        http_response = HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/html'))
        for header in response.headers:
            http_response[header] = response.headers[header]

        cache_manager.process_response(http_request, http_response)
    return response
