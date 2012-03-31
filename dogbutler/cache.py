from dogbutler.utils.cache import get_cache_key, learn_cache_key, get_max_age


CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX = 'longterm'
CACHE_MANAGER_LONG_TERM_CACHE_SECONDS = 60 * 60 * 24 * 30


class CacheManager(object):

    def __init__(self, key_prefix, cache, cache_anonymous_only=False):
        self.key_prefix = key_prefix
        self.cache = cache
        self.cache_anonymous_only = cache_anonymous_only

    def process_request(self, request):
        response = self.check_cache(request)
        if response is None:
            self.patch_if_modified_since_header(request)
            self.patch_if_none_match_header(request)
        return response

    def check_cache(self, request):
        """
        Checks whether the page is already cached and returns the cached
        version if available.
        """
        if not request.method in ('GET', 'HEAD'):
            request._cache_update_cache = False
            return None # Don't bother checking the cache.

        # try and get the cached GET response
        cache_key = get_cache_key(request, self.key_prefix, 'GET', cache=self.cache)
        if cache_key is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.
        response = self.cache.get(cache_key, None)
        # if it wasn't found and we are looking for a HEAD, try looking just for that
        if response is None and request.method == 'HEAD':
            cache_key = get_cache_key(request, self.key_prefix, 'HEAD', cache=self.cache)
            response = self.cache.get(cache_key, None)

        if response is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.

        # hit, return cached response
        request._cache_update_cache = False
        return response

    def patch_if_modified_since_header(self, request):
        """
        Add 'If-Modified-Since' header to request if:
        1. request does not have 'If-Modified-Since' already, and
        2. Previous response has 'Last-Modified' header.
        """
        if 'If-Modified-Since' not in request.headers:
            cache_key = get_cache_key(request, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, 'GET', cache=self.cache)
            if cache_key is not None:
                response = self.cache.get(cache_key, None)
                if response is not None:
                    if response.has_header('Last-Modified'):
                        request.headers['If-Modified-Since'] = response['Last-Modified']

    def patch_if_none_match_header(self, request):
        """
        Add 'If-None-Match' header to request if:
        1. request does not have 'If-None-Match' already, and
        2. Previous response has 'ETag' header.
        """
        if 'If-None-Match' not in request.headers:
            cache_key = get_cache_key(request, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, 'GET', cache=self.cache)
            if cache_key is not None:
                response = self.cache.get(cache_key, None)
                if response is not None:
                    if response.has_header('ETag'):
                        request.headers['If-None-Match'] = response['ETag']

    def process_304_response(self, request, response):
        cache_key = get_cache_key(request, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, 'GET', cache=self.cache)
        if cache_key is None:
            return None
        cached_response = self.cache.get(cache_key, None)
        if cached_response is None:
            return None
        else:
            response._content = cached_response.content
            return response

    def _should_update_cache(self, request, response):
        if not hasattr(request, '_cache_update_cache') or not request._cache_update_cache:
            return False
        # If the session has not been accessed otherwise, we don't want to
        # cause it to be accessed here. If it hasn't been accessed, then the
        # user's logged-in status has not affected the response anyway.
        if self.cache_anonymous_only and self._session_accessed(request):
            assert hasattr(request, 'user'), "The Django cache middleware with CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True requires authentication middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.auth.middleware.AuthenticationMiddleware' before the CacheMiddleware."
            if request.user.is_authenticated():
                # Don't cache user-variable requests from authenticated users.
                return False
        return True

    def process_response(self, request, response):
        """Update cache if cache-control is not no-cache"""
        cache_control = response.headers.get('Cache-Control')
        if cache_control is not None and 'no-cache' not in cache_control:
            self.update_cache(request, response)

    def update_cache(self, request, response):
        """Sets the cache, if needed."""
        if not self._should_update_cache(request, response):
            # We don't need to update the cache, just return.
            return response
        if response.status_code/100 != 2 and response.status_code/100 != 4 and response.status_code != 304:
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
#        patch_response_headers(response, timeout)
        if timeout:
            cache_key = learn_cache_key(request, response, timeout, self.key_prefix, cache=self.cache)
            long_term_cache_key = learn_cache_key(request, response, CACHE_MANAGER_LONG_TERM_CACHE_SECONDS, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, cache=self.cache)
            if hasattr(response, 'render') and callable(response.render):

                # TODO: Investigate 'post_render_callback'
                def post_render_callback(r):
                    self.cache.set(cache_key, r, timeout)
                    self.cache.set(long_term_cache_key, r, CACHE_MANAGER_LONG_TERM_CACHE_SECONDS)

                response.add_post_render_callback(post_render_callback)
            else:
                self.cache.set(cache_key, response, timeout)
                self.cache.set(long_term_cache_key, response, CACHE_MANAGER_LONG_TERM_CACHE_SECONDS)
        return response
