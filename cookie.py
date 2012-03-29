from Cookie import SimpleCookie
from datetime import datetime
from urlparse import urlparse

class CookieManager(object):

    def __init__(self, key_prefix, cache):
        self.key_prefix = key_prefix
        self.cache = cache

    def process_request(self, request):
        request.cookies = self.get_domain_cookie(request.url) or dict()

    def process_response(self, request, response):
        self.extract_cookie(request.url, response)

    def _path_ok(self, cookie, url):
        if not cookie['path']:
            return True

        if cookie['path'] and cookie['path'] == '/':
            return True
        request_path = urlparse(url).path

        if not request_path.startswith('/'):
            request_path = '/' + request_path

        if request_path == cookie['path']:
            return True
        elif cookie['path'].endswith('/') and request_path.startswith(cookie['path']):
            return True
        elif request_path.startswith(cookie['path']) and request_path[len(cookie['path'])] == '/':
            return True
        else:
            return False

    def get_domain_cookie(self, url):
        """
        return simple dictionary of (key:value) cookies for domain
        """
        domain = urlparse(url).netloc
        set_cookie = {}
        expired_cookie = set()
        if self.cache.get(domain):
            domain_cookies = self.cache.get(domain)
            for cookie_name in domain_cookies:
                cookie = self.cache.get(cookie_name)
                if cookie:
                    if self._path_ok(cookie, url):
                        set_cookie.update({cookie.key: cookie.value})
                else:
                    expired_cookie.add(cookie_name)

            updated_domain_cookies = domain_cookies.difference(expired_cookie)
            self.cache.set(domain, updated_domain_cookies)

        return  set_cookie

    def extract_cookie(self, url, response):
        #if there's Set-Cookie in response
        if response and response.cookies:
            origin = urlparse(url).netloc
            #if there's not cookie for this domain, create one

            if not self.cache.get(origin):
                self.cache.set(origin,set())
            origin_cookies = self.cache.get(origin)
            cookie = SimpleCookie()
            cookie.load(response.headers['Set-Cookie'])
            for name, c in cookie.items():
                cookie_name = '%s.%s' % (origin, name)
                max_age = None
                # convert expires to seconds, so we use take advantage of cache expiry feature,
                # no need to clear cookie ourselves
                if c['expires']:
                    fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
                    expired  = datetime.strptime(c['expires'], fmt)
                    now = datetime.utcnow()
                    max_age = (expired - now).total_seconds()

                # max-age has higher priority than  expires
                if c['max-age']:
                    max_age = int(c['max-age'])

                domain = c['domain']
                if domain:
                    if not self.cache.get(domain):
                        self.cache.set(domain, set())
                    cookie_name = '%s.%s' % (domain,name)
                    domain_cookies = self.cache.get(c['domain'])
                    domain_cookies.add(cookie_name)

                # save morsel (cookie info) in cache :) if max_age < 0, the key is deleted
                if max_age is not None:
                    self.cache.set(cookie_name, c, max_age)
                else:
                    self.cache.set(cookie_name, c)

                #update lookup cache
                if domain:
                    self.cache.set(domain, domain_cookies)
                else:
                    origin_cookies.add(cookie_name)

            self.cache.set(origin, origin_cookies)
