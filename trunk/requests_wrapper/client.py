from datetime import datetime, timedelta
import requests

cache = dict(_responses=dict())


def _use_cache(url, expire_after=5):

    try:
        pointer = cache[url]
        stored_at, response = cache['_responses'][pointer]
    except KeyError:
        return False, None
    difference = datetime.now() - stored_at
    if difference < timedelta(minutes=expire_after):
        return True, response
    else:
        for r in response.history:
            del cache[r.url]
        del cache['_responses'][url]
        del cache[url]
        print 'sending request'
    return False, None

def _to_cache(response, allowable_codes=(200,)):
    if (response.status_code in allowable_codes
        and not hasattr(response, '_from_cache')):
        response._from_cache = True
        cache['_responses'][response.url] = datetime.now(), response
        cache[response.url] = response.url
        for r in response.history:
            cache[r.url] = response.url
    return response

def get(url):
    use_cache, response = _use_cache(url)
    if use_cache:
        return response
    return requests.get(url, hooks=dict(response=_to_cache))


def post(url, **kwargs):
    return requests.post(url, **kwargs)


