# Create your views here.
from django.shortcuts import render_to_response
from django.utils import simplejson
from requests_wrapper import client
def home(request):
    response = client.get('http://Manhattan.local:8000/categories')
    categories_response = response.content
    categories = simplejson.loads(categories_response).get('results')
    return render_to_response('delecious.html',{'categories':categories})
