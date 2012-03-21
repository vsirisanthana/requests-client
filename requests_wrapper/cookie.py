from Cookie import SimpleCookie, _getdate
from datetime import datetime, timedelta
from urlparse import urlparse
from django.core.cache import cache
from time import gmtime, mktime, strptime

def get_domain_cookie(url):
    domain = urlparse(url).netloc
#    cookies = cache.get('cookies')
    set_cookie = {}
#    if cookies and cookies.get(domain):
    if cache.get(domain):
#        domain_cookie = cookies.get(domain)
        domain_cookie = cache.get(domain)
#        for name, cookie in domain_cookie.items():
#            #check only un expired cookie can get in the dict
#            if cookie['expires']:
#                fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
#                # otherwise have to convert back to epoh seconds :( make it gmt time when compare
#                expired  = gmtime(mktime(strptime(cookie['expires'],fmt)))
#                now = gmtime(mktime(strptime(_getdate(),fmt)))
#                if now > expired:
#                    del domain_cookie[name]
#                    continue
#            set_cookie.update({name:cookie.value})

        for cookiename in domain_cookie:
            cookie = cache.get(cookiename)
            if cookie:
                set_cookie.update({cookie.key: cookie.value})

    return  set_cookie


def extract_cookie(url, response):
#    cookies = cache.get('cookies')
    if response.cookies:
#        cookies = cookies or dict()
        domain = urlparse(url).netloc
#        if not domain in cookies.keys():
        if not cache.get(domain):
            #cookies[domain] = {}
            cache.set(domain,set())

#        domain_cookies = cookies[domain]
        domain_cookies = cache.get(domain)
        cookie = SimpleCookie()
        cookie.load(response.headers['set-cookie'])
        for name, c in cookie.items():
            cookiename = '%s.%s' % (domain, name)
            maxage = None
            if c['expires']:
                fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
                expired  = datetime.strptime(c['expires'], fmt)
                now = datetime.utcnow()
                maxage = (expired - now).total_seconds()

            if c['max-age']:
#                c['expires'] = _getdate(future=int(c['max-age']))
                maxage = int(c['max-age'])
            if maxage is not None:
                cache.set(cookiename, c, maxage)
            else:
                cache.set(cookiename, c)

            domain_cookies.add(cookiename)

#        domain_cookies.update(cookie)
#        cache.set('cookies', cookies)
        cache.set(domain, domain_cookies)

