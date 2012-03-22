from Cookie import SimpleCookie
from datetime import datetime
from urlparse import urlparse

from default_cache import cache

def get_domain_cookie(url):
    """
    return simple dictionary of (key:value) cookies for domain
    """
    domain = urlparse(url).netloc
    set_cookie = {}
    expired_cookie = set()
    if cache.get(domain):
        domain_cookies = cache.get(domain)
        for cookie_name in domain_cookies:
            cookie = cache.get(cookie_name)
            if cookie:
                set_cookie.update({cookie.key: cookie.value})
            else:
                expired_cookie.add(cookie_name)

        updated_domain_cookies = domain_cookies.difference(expired_cookie)
        cache.set(domain, updated_domain_cookies)

    return  set_cookie


def extract_cookie(url, response):
    #if there's set-cookie in response
    if response and response.cookies:
        domain = urlparse(url).netloc
        #if there's not cookie for this domain, create one
        if not cache.get(domain):
            cache.set(domain,set())
        domain_cookies = cache.get(domain)
        cookie = SimpleCookie()
        cookie.load(response.headers['set-cookie'])
        for name, c in cookie.items():
            cookie_name = '%s.%s' % (domain, name)
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

            # save morsel (cookie info) in cache :)
            if max_age is not None:
                cache.set(cookie_name, c, max_age)
            else:
                cache.set(cookie_name, c)

            domain_cookies.add(cookie_name)

        cache.set(domain, domain_cookies)


