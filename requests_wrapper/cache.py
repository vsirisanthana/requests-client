from django.middleware.cache import CacheMiddleware
from django.utils.cache import get_cache_key, learn_cache_key, patch_response_headers, get_max_age


CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX = 'longterm'
CACHE_MANAGER_LONG_TERM_CACHE_SECONDS = 60 * 60 * 24 * 30


class CacheManager(CacheMiddleware):

    def patch_if_modified_since_header(self, request):
        """
        Add 'If-Modified-Since' header to request if:
        1. request does not have 'If-Modified-Since' already, and
        2. Previous response has 'Last-Modified' header.
        """
        if 'HTTP_IF_MODIFIED_SINCE' not in request.META:
            cache_key = get_cache_key(request, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, 'GET', cache=self.cache)
            if cache_key is not None:
                response = self.cache.get(cache_key, None)
                if response is not None:
                    if response.has_header('Last-Modified'):
                        request.META['HTTP_IF_MODIFIED_SINCE'] = response['Last-Modified']

    def patch_if_none_match_header(self, request):
        """
        Add 'If-None-Match' header to request if:
        1. request does not have 'If-None-Match' already, and
        2. Previous response has 'ETag' header.
        """
        if 'HTTP_IF_NONE_MATCH' not in request.META:
            cache_key = get_cache_key(request, CACHE_MANAGER_LONG_TERM_CACHE_KEY_PREFIX+self.key_prefix, 'GET', cache=self.cache)
            if cache_key is not None:
                response = self.cache.get(cache_key, None)
                if response is not None:
                    if response.has_header('ETag'):
                        request.META['HTTP_IF_NONE_MATCH'] = response['ETag']

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

    def process_response(self, request, response):
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
