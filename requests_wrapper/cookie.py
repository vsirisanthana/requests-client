from urlparse import urlparse
from django.core.cache import cache
from django.http import SimpleCookie


def get_domain_cookie(url):
    domain = urlparse(url).netloc
    cookies = cache.get('cookies')
    set_cookie = {}
    if cookies and cookies.get(domain):
        domain_cookie = cookies.get(domain)
        for k, v in domain_cookie.items():
            set_cookie.update({k:v.value})

    return  set_cookie


def extract_cookie(url, response):
    cookies = cache.get('cookies')
    if response.cookies:
        cookies = cookies or dict()
        domain = urlparse(url).netloc
        if not domain in cookies.keys():
            cookies[domain] = {}

        domain_cookies = cookies[domain]
        cookie = SimpleCookie()
        cookie.load(response.headers['set-cookie'])
        domain_cookies.update(cookie)
        cache.set('cookies', cookies)

