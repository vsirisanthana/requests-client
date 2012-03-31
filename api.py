import requests
from requests import request, head, post, patch, put, delete, options, TooManyRedirects

from .cache import CacheManager
from .cookie import CookieManager
from .defaults import get_default_cache, get_default_cookie_cache, get_default_redirect_cache
from .models import Request
from .redirect import RedirectManager


DEFAULT_KEY_PREFIX = 'dogbutler'
DEFAULT_COOKIE_KEY_PREFIX = 'cookie'
DEFAULT_REDIRECT_KEY_PREFIX = 'redirect'


def get(url, queue=None, **kwargs):

    # Create managers
    cache_manager = CacheManager(key_prefix=DEFAULT_KEY_PREFIX, cache=get_default_cache())
    cookie_manager = CookieManager(key_prefix=DEFAULT_COOKIE_KEY_PREFIX, cache=get_default_cookie_cache())
    redirect_manager = RedirectManager(key_prefix=DEFAULT_REDIRECT_KEY_PREFIX, cache=get_default_redirect_cache())

    # Convert to Request object
    request = Request(url, method='GET', **kwargs)

    # Process request
    redirect_manager.process_request(request)                   # Redirect if previously got 301
    cookie_manager.process_request(request)                     # Set cookies
    response = cache_manager.process_request(request)           # Get from cache if conditions are met
    if response is not None:
        if queue: queue.put(response)
        return response

    # Update kwargs
    if request.headers: kwargs['headers'] = request.headers     # Update kwargs with new headers
    if request.cookies: kwargs['cookies'] = request.cookies     # Update kwargs with new cookies

    # Make a request
    response = requests.get(request.url, **kwargs)

    # Process response
    redirect_manager.process_response(request, response)        # Save redirect info

    # Handle 304
    if response.status_code == 304:
        response = cache_manager.process_304_response(request, response)
        if response is None:
            if kwargs.has_key('If-Modified-Since'): del kwargs['If-Modified-Since']
            if kwargs.has_key('If-None-Match'): del kwargs['If-None-Match']
            response = requests.get(request.url, **kwargs)

    cookie_manager.process_response(request, response)          # Handle cookie
    cache_manager.process_response(request, response)           # Update cache as necessary

    if queue: queue.put(response)
    return response
