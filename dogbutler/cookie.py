from Cookie import SimpleCookie
from datetime import datetime
import re
from urlparse import urlparse


ORIGIN_KEY_PREFIX = 'origin'

def _make_cookie(cookie_headers):
    def _add_dash(match_obj):
        return match_obj.group(0).replace(' ', '-')

    cookie = SimpleCookie()
    set_cookie_str = re.sub(r'\d{2}\s\w+\s\d{4}', _add_dash, cookie_headers)
    cookie.load(set_cookie_str)

    return  cookie

def get_max_age(cookie):
    max_age = None
    # convert expires to seconds, so we use take advantage of cache expiry feature,
    # no need to clear cookie ourselves
    if cookie['expires']:
        fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
        try:
            expired  = datetime.strptime(cookie['expires'], fmt)
            now = datetime.utcnow()
            max_age = (expired - now).total_seconds()
        except ValueError:
            # if cookie has wrong date format we ignore the expires
            cookie['expires'] = ''
            max_age = None

    # max-age has higher priority than  expires
    if cookie['max-age']:
        max_age = int(cookie['max-age'])
    return max_age

def is_domain_valid(domain):
    if domain.endswith('.'):
        return False
    else:
        return True

def normalize_domain(domain):
    return domain.lstrip('.')

def normalize_path(path):
    return path.rstip('/') if path != '/' else path


class CookieManager(object):

    def __init__(self, key_prefix, cache):
        self.key_prefix = key_prefix
        self.cache = cache

    def process_request(self, request):
        """
        Set 'Cookie' header in request
        """
        request.cookies = self.get_cookies(request.url)

    def process_response(self, request, response):
        """
        Process 'Set-Cookie' header in response
        """
        if response and response.has_header('Set-Cookie'):
            origin = urlparse(response.url).netloc
            cookies = _make_cookie(response.headers['Set-Cookie'])
            for name, cookie in cookies.items():
                domain = cookie['domain']
                if not domain:
                    self.set_origin_cookie(origin, cookie)
                else:
                    self.set_domain_cookie(cookie)

    def get_domain_cookie_key(self, domain, path, name):
        return '%s.%s.%s.%s' % (self.key_prefix, normalize_domain(domain), path, name)

    def get_domain_cookie_lookup_key(self, domain):
        return '%s.%s' % (self.key_prefix, normalize_domain(domain))

    def get_origin_cookie_key(self, origin, path, name):
        return '%s.%s.%s.%s.%s' % (self.key_prefix, ORIGIN_KEY_PREFIX, normalize_domain(origin), path, name)

    def get_origin_cookie_lookup_key(self, origin):
        return '%s.%s.%s' % (self.key_prefix, ORIGIN_KEY_PREFIX, normalize_domain(origin))

    def get_cookies(self, url):
        """
        Return a dictionary (key:value) of cookies for the given URL
        """
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        path = urlparse(url).path
        cookies = self.get_origin_cookies(domain, path)
        for i in reversed(range(len(domain_parts))):
            d = '.'.join(domain_parts[i:])
            c = self.get_domain_cookies(d, path)
            cookies.update(c)
        return cookies

    def get_domain_cookies(self, domain, path):
        """
        Return a dictionary (key:value) of domain cookies
        """
        return self.get_xxx_cookies(self.get_domain_cookie_lookup_key, domain, path)

    def get_origin_cookies(self, domain, path):
        """
        Return a dictionary (key:value) of origin cookies
        """
        return self.get_xxx_cookies(self.get_origin_cookie_lookup_key, domain, path)

    def get_xxx_cookies(self, get_lookup_key_fn, domain, path):
        """
        Return a dictionary (key:value) of xxx cookies
        """
        lookup_key = get_lookup_key_fn(domain)
        cookie_keys_set = self.cache.get(lookup_key) or set()
        cookies = {}
        expired_cookie_keys_set = set()
        if cookie_keys_set:
            for cookie_key in cookie_keys_set:
                cookie = self.cache.get(cookie_key)
                if cookie:
                    if self._path_ok(cookie, path):
                        cookies[cookie.key] = cookie.value
                else:
                    expired_cookie_keys_set.add(cookie_key)
        self.cache.set(lookup_key, cookie_keys_set.difference(expired_cookie_keys_set))
        return cookies

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

    def set_domain_cookie(self, cookie):
        """
        Set domain cookie (i.e. cookie that has Domain attribute) in cache.
        """
        domain = cookie['domain']
        if not is_domain_valid(domain):
            return

        max_age = get_max_age(cookie)
        name = cookie.key
        path = cookie['path']

        cookie_key = self.get_domain_cookie_key(domain, path, name)
        lookup_key = self.get_domain_cookie_lookup_key(domain)
        self.cache.set(cookie_key, cookie, max_age)

        cookie_keys_set = self.cache.get(lookup_key) or set()
        cookie_keys_set.add(cookie_key)
        self.cache.set(lookup_key, cookie_keys_set)

    def set_origin_cookie(self, origin, cookie):
        """
        Set origin cookie (i.e. cookie that does not have Domain attribute) in cache.
        """
        max_age = get_max_age(cookie)
        name = cookie.key
        path = cookie['path']

        cookie_key = self.get_origin_cookie_key(origin, path, name)
        lookup_key = self.get_origin_cookie_lookup_key(origin)
        self.cache.set(cookie_key, cookie, max_age)

        cookie_keys_set = self.cache.get(lookup_key) or set()
        cookie_keys_set.add(cookie_key)
        self.cache.set(lookup_key, cookie_keys_set)