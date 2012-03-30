from Cookie import SimpleCookie
from datetime import datetime
import re
from urlparse import urlparse

from .defaults import get_default_cookie_cache

def _path_ok(cookie, url):
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


def get_domain_cookie(url):
    """
    return simple dictionary of (key:value) cookies for domain
    """
    cache = get_default_cookie_cache()
    domain = urlparse(url).netloc
    set_cookie = {}
    expired_cookie = set()
    if cache.get(domain):
        domain_cookies = cache.get(domain)
        for cookie_name in domain_cookies:
            cookie = cache.get(cookie_name)
            if cookie:
                if _path_ok(cookie, url):
                    set_cookie.update({cookie.key: cookie.value})
            else:
                expired_cookie.add(cookie_name)

        updated_domain_cookies = domain_cookies.difference(expired_cookie)
        cache.set(domain, updated_domain_cookies)

    return  set_cookie


def _make_cookie(cookie_headers):
    def _add_dash(match_obj):
        return match_obj.group(0).replace(' ', '-')

    cookie = SimpleCookie()
    set_cookie_str = re.sub(r'\d{2}\s\w+\s\d{4}', _add_dash, cookie_headers)
    cookie.load(set_cookie_str)

    return  cookie

def extract_cookie(url, response):
    cache = get_default_cookie_cache()
    #if there's set-cookie in response
    if response and response.headers.has_key('Set-Cookie'):
        origin = urlparse(url).netloc
        #if there's not cookie for this domain, create one

        if not cache.get(origin):
            cache.set(origin,set())
        origin_cookies = cache.get(origin)

        cookie = _make_cookie(response.headers['Set-Cookie'])

        for name, c in cookie.items():
            cookie_name = '%s.%s' % (origin, name)
            max_age = None
            # convert expires to seconds, so we use take advantage of cache expiry feature,
            # no need to clear cookie ourselves
            if c['expires']:
                fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
                try:
                    expired  = datetime.strptime(c['expires'], fmt)
                    now = datetime.utcnow()
                    max_age = (expired - now).total_seconds()
                except ValueError:
                    # if cookie has wrong date format we ignore the expires
                    c['expires'] = ''
                    max_age = None

            # max-age has higher priority than  expires
            if c['max-age']:
                max_age = int(c['max-age'])

            domain = c['domain']
            if domain:
                if not cache.get(domain):
                    cache.set(domain, set())
                cookie_name = '%s.%s' % (domain,name)
                domain_cookies = cache.get(c['domain'])
                domain_cookies.add(cookie_name)

            # save morsel (cookie info) in cache :) if max_age < 0, the key is deleted
            if max_age is not None:
                cache.set(cookie_name, c, max_age)
            else:
                cache.set(cookie_name, c)

            #update lookup cache
            if domain:
                cache.set(domain, domain_cookies)
            else:
                origin_cookies.add(cookie_name)

        cache.set(origin, origin_cookies)
