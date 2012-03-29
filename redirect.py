from requests.exceptions import TooManyRedirects

class RedirectManager(object):

    def __init__(self, key_prefix, cache):
        self.key_prefix = key_prefix
        self.cache = cache

    def get_cache_key(self, url):
        return '%s.%s' % (self.key_prefix, url)

    def process_request(self, request):
        url = request.url
        history = []
        while True:
            if url in history:
                raise TooManyRedirects()
            redirect_to = self.cache.get(self.get_cache_key(url))
            if redirect_to is None:
                break
            url = redirect_to
        request.url = url

    def process_response(self, request, response):
        if response.history:
            request.url = response.url
            for r in response.history:
                if r.status_code == 301:
                    #TODO: handle case of no Location header
                    redirect_to = r.headers.get('Location')
                    self.cache.set(self.get_cache_key(r.url), redirect_to)
