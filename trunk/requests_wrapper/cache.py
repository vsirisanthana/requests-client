#import re
#
#from django.conf import settings
#from django.utils.encoding import iri_to_uri
#from django.utils.hashcompat import md5_constructor
#
#cc_delim_re = re.compile(r'\s*,\s*')
#
#
#
#def _generate_cache_key(url, headers, method, headerlist, key_prefix):
#    """Returns a cache key from the headers given in the header list."""
#    ctx = md5_constructor()
#    for header in headerlist:
#        value = headers.get(header, None)
#        if value is not None:
#            ctx.update(value)
#    path = md5_constructor(iri_to_uri(url))
#    cache_key = 'views.decorators.cache.cache_page.%s.%s.%s.%s' % (
#        key_prefix, method, path.hexdigest(), ctx.hexdigest())
##    return _i18n_cache_key_suffix(request, cache_key)
#    return cache_key
#
#def _generate_cache_header_key(key_prefix, url):
#    """Returns a cache key for the header cache."""
#    path = md5_constructor(iri_to_uri(url))
#    cache_key = 'views.decorators.cache.cache_header.%s.%s' % (
#        key_prefix, path.hexdigest())
##    return _i18n_cache_key_suffix(request, cache_key)
#    return cache_key
#
#def get_cache_key(url, headers={}, key_prefix=None, method='GET', cache=None):
#    """
#    Returns a cache key based on the request path and query. It can be used
#    in the request phase because it pulls the list of headers to take into
#    account from the global path registry and uses those to build a cache key
#    to check against.
#
#    If there is no headerlist stored, the page needs to be rebuilt, so this
#    function returns None.
#    """
#    if key_prefix is None:
#        key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
#    cache_key = _generate_cache_header_key(key_prefix, url)
##    if cache is None:
##        cache = get_cache(settings.CACHE_MIDDLEWARE_ALIAS)
#    headerlist = cache.get(cache_key, None)
#    if headerlist is not None:
#        return _generate_cache_key(url, headers, method, headerlist, key_prefix)
#    else:
#        return None
#
#def learn_cache_key(request_url, request_headers, response_url, response_headers, cache_timeout=None, key_prefix=None, cache=None):
#    """
#    Learns what headers to take into account for some request path from the
#    response object. It stores those headers in a global path registry so that
#    later access to that path will know what headers to take into account
#    without building the response object itself. The headers are named in the
#    Vary header of the response, but we want to prevent response generation.
#
#    The list of headers to use for cache key generation is stored in the same
#    cache as the pages themselves. If the cache ages some data out of the
#    cache, this just means that we have to build the response once to get at
#    the Vary header and so at the list of headers to use for the cache key.
#    """
#    if key_prefix is None:
#        key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
#    if cache_timeout is None:
#        cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
#    cache_key = _generate_cache_header_key(key_prefix, request_url)
##    if cache is None:
##        cache = get_cache(settings.CACHE_MIDDLEWARE_ALIAS)
#    if response_headers.get('Vary', None):
#        headerlist = ['HTTP_'+header.upper().replace('-', '_')
#                      for header in cc_delim_re.split(response_headers['Vary'])]
#        cache.set(cache_key, headerlist, cache_timeout)
#        return _generate_cache_key(request_url, request.method, headerlist, key_prefix)
#    else:
#        # if there is no Vary header, we still need a cache key
#        # for the request.get_full_path()
#        cache.set(cache_key, [], cache_timeout)
#        return _generate_cache_key(request, request.method, [], key_prefix)