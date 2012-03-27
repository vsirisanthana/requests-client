import requests
from requests import request, head, post, patch, put, delete, options, TooManyRedirects

from .cache import CacheManager
from .cookie import extract_cookie, get_domain_cookie
from .defaults import get_default_cache, get_default_redirect_cache
from .models import Request
from .redirect import RedirectManager


DEFAULT_KEY_PREFIX = 'dogbutler'
DEFAULT_REDIRECT_KEY_PREFIX = 'redirect'


def get(url, queue=None, **kwargs):
    # Create managers
    cache_manager = CacheManager(key_prefix=DEFAULT_KEY_PREFIX, cache=get_default_cache())
    redirect_manager = RedirectManager(key_prefix=DEFAULT_REDIRECT_KEY_PREFIX, cache=get_default_redirect_cache())

    # Convert to Request object
    request = Request(url, method='GET', **kwargs)
    request.COOKIES = get_domain_cookie(url) or dict()

    # check if the url is permanently redirect or not
    redirect_manager.process_request(request)

    response = cache_manager.process_request(request)
    if response is not None:
        if queue: queue.put(response)
        return response

    # Update kwargs with new headers
    if request.headers: kwargs['headers'] = request.headers

    # set cookie
    if get_domain_cookie(request.url):
        kwargs['cookies'] = get_domain_cookie(request.url)
    response = requests.get(request.url, **kwargs)

    redirect_manager.process_response(request, response)

    # Handle 304
    if response.status_code == 304:
        response = cache_manager.process_304_response(request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(request.url, **kwargs)

    #handle cookie
    extract_cookie(request.url, response)

    # Update cache as necessary
    cache_manager.process_response(request, response)

    if queue: queue.put(response)
    return response
