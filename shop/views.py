# Create your views here.
from datetime import datetime, timedelta
from django.shortcuts import render_to_response
from django.utils import simplejson

import requests
cache = dict(_responses=dict())


def _from_cache(request, expire_after=60):

    try:
        pointer = cache[request.url]
        stored_at, response = cache['_responses'][pointer]
    except KeyError:
        return request
    difference = datetime.now() - stored_at
    if difference < timedelta(minutes=expire_after):
        request.response = response
#        request.send = lambda self=None, anyway=False: True
        request.conn = None
        print 'do nothing'
        print response
    else:
        for r in response.history:
            del cache[r.url]
        del cache['_responses'][request.url]
        del cache[request.url]
        print 'sending request'
    return request

def _to_cache(response, allowable_codes=(200,)):
    if (response.status_code in allowable_codes
        and not hasattr(response, '_from_cache')):
        response._from_cache = True
        cache['_responses'][response.url] = datetime.now(), response
        cache[response.url] = response.url
        for r in response.history:
            cache[r.url] = response.url
    return response

def home(request):
    response = requests.get('http://localhost:8000/categories',  hooks=dict(pre_request=_from_cache, response=_to_cache))
    categories_response = response.content
    categories = simplejson.loads(categories_response).get('results')
    print 'cache', cache
    return render_to_response('delecious.html',{'categories':categories})