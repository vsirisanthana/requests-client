from Cookie import _getdate
from datetime import datetime, timedelta
from unittest import TestCase

from dummycache import cache as dummycache_cache
from dummycache.cache import Cache
from mock import patch
from requests.models import Response
from requests.utils import dict_from_string

from .. import get
from ..default_cache import get_default_cache, set_default_cache
from .datetimestub import DatetimeStub


@patch('requests.get')
class TestClient(TestCase):

    def setUp(self):
        super(TestClient, self).setUp()
        dummycache_cache.datetime = DatetimeStub()
        self.cache = get_default_cache()
        self.cache.clear()

    def tearDown(self):
        self.cache.clear()
        dummycache_cache.datetime = datetime
        super(TestClient, self).tearDown()

    def test_get_max_age(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
        }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)

    def test_get_different_urls(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        get('http://www.test.com/path/1')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path/2')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path/1')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path/3')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path/2')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_different_queries(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        get('http://www.test.com/path?name=john')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path?name=emily')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path?name=john&age=30')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path?name=emily')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path?name=john&age=30')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_different_fragments(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        get('http://www.test.com/path#help')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path#header')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path#header')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path#footer')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path#help')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_vary_on_accept(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
            'Vary': 'Accept'
        }
        mock_get.return_value = response

        get('http://www.test.com/path', headers={'Accept': 'application/json'})
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path', headers={'Accept': 'application/json'})
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path', headers={'Accept': 'application/xml'})
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path', headers={'Accept': 'text/html'})
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path', headers={'Accept': 'application/json, */*'})
        self.assertEqual(mock_get.call_count, 4)

    def test_get_no_cache_control_header(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        # no cache-control header
        response.headers = {}
        mock_get.return_value = response

        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_cache_control_no_cache(self, mock_get):
        """
        Make sure we not cache at all even there's a no-cache only at certain field
        """
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        # no cache-control header
        response.headers = {
            'Cache-Control': 'no-cache=field, max-age=10'
        }
        mock_get.return_value = response

        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_cache_control_no_cache_empty_field(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        # no cache-control header
        response.headers = {
            'Cache-Control': 'no-cache'
        }
        mock_get.return_value = response

        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_cache_201(self, mock_get):
        response = Response()
        response.status_code = 201
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 201)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 201)

    def test_get_cache_204(self, mock_get):
        response = Response()
        response.status_code = 204
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 204)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 204)

    def test_get_cache_400(self, mock_get):
        response = Response()
        response.status_code = 400
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 400)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 400)

    def test_get_cache_401(self, mock_get):
        response = Response()
        response.status_code = 401
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 401)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 401)

    def test_get_cache_403(self, mock_get):
        response = Response()
        response.status_code = 403
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 403)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 403)

    def test_get_cache_404(self, mock_get):
        response = Response()
        response.status_code = 404
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 404)

        response = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 404)

    def test_get_301_only_once(self, mock_get):
        response0 = Response()
        response0.url = 'http://www.test.com/neverseemeagain'
        response0.status_code = 301
        response0.headers = {
            'Location': 'http://www.test.com/redirect_here',
        }

        response1 = Response()
        response1.url = 'http://www.test.com/redirect_here'
        response1.status_code = 200
        response1._content = 'Mocked response content'
        response1.headers = {
            'Vary': 'Accept',
        }
        response1.history = [response0]

        mock_get.return_value = response1


        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/neverseemeagain')
        self.assertEqual(r.status_code, 200)

        #assert we not make request to 301 again
        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/redirect_here')
        self.assertEqual(r.status_code, 200)

    def test_get_301_only_once_with_cache(self, mock_get):
        response0 = Response()
        response0.url = 'http://www.test.com/neverseemeagain'
        response0.status_code = 301
        response0.headers = {
            'Location': 'http://www.test.com/redirect_here',
        }

        response1 = Response()
        response1.url = 'http://www.test.com/redirect_here'
        response1.status_code = 200
        response1._content = 'Mocked response content'
        response1.headers = {
            'Cache-Control': 'max-age=10',
            'Vary': 'Accept',
        }
        response1.history = [response0]

        mock_get.return_value = response1


        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/neverseemeagain')
        self.assertEqual(r.status_code, 200)

        # assert we not making any call as we get result from cache
        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        # assert get the redirected url direct is working fine, and give us result from cache
        r = get('http://www.test.com/redirect_here')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

    def test_get_301_thrice(self, mock_get):
        response0 = Response()
        response0.url = 'http://www.test.com/neverseemeagain'
        response0.status_code = 301
        response0.headers = {
            'Location': 'http://www.test.com/redirect_1',
            }

        response1 = Response()
        response1.url = 'http://www.test.com/redirect_1'
        response1.status_code = 301
        response1.headers = {
            'Location': 'http://www.test.com/redirect_2',
            }

        response2 = Response()
        response2.url = 'http://www.test.com/redirect_2'
        response2.status_code = 301
        response2.headers = {
            'Location': 'http://www.test.com/redirect_3',
            }

        response3 = Response()
        response3.url = 'http://www.test.com/redirect_3'
        response3.status_code = 200
        response3._content = 'Mocked response content'
        response3.headers = {
            'Vary': 'Accept',
            }
        response3.history = [response0, response1, response2]

        mock_get.return_value = response3


        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/neverseemeagain')
        self.assertEqual(r.status_code, 200)

        #assert we not make request to 301 again
        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/redirect_3')
        self.assertEqual(r.status_code, 200)

        r = get('http://www.test.com/redirect_1')
        self.assertEqual(mock_get.call_count, 3)
        mock_get.assert_called_with('http://www.test.com/redirect_3')
        self.assertEqual(r.status_code, 200)

        r = get('http://www.test.com/redirect_2')
        self.assertEqual(mock_get.call_count, 4)
        mock_get.assert_called_with('http://www.test.com/redirect_3')
        self.assertEqual(r.status_code, 200)

        r = get('http://www.test.com/redirect_3')
        self.assertEqual(mock_get.call_count, 5)
        mock_get.assert_called_with('http://www.test.com/redirect_3')
        self.assertEqual(r.status_code, 200)

    def test_get_301_thrice_with_cache(self, mock_get):
        response0 = Response()
        response0.url = 'http://www.test.com/neverseemeagain'
        response0.status_code = 301
        response0.headers = {
            'Location': 'http://www.test.com/redirect_1',
            }

        response1 = Response()
        response1.url = 'http://www.test.com/redirect_1'
        response1.status_code = 301
        response1.headers = {
            'Location': 'http://www.test.com/redirect_2',
            }

        response2 = Response()
        response2.url = 'http://www.test.com/redirect_2'
        response2.status_code = 301
        response2.headers = {
            'Location': 'http://www.test.com/redirect_3',
            }

        response3 = Response()
        response3.url = 'http://www.test.com/redirect_3'
        response3.status_code = 200
        response3._content = 'Mocked response content'
        response3.headers = {
            'Cache-Control': 'max-age=10',
            'Vary': 'Accept',
            }
        response3.history = [response0, response1, response2]

        mock_get.return_value = response3


        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        # assert we not making any call as we get result from cache
        r = get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        # assert get the redirected url direct is working fine, and give us result from cache
        r = get('http://www.test.com/redirect_1')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        r = get('http://www.test.com/redirect_2')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        r = get('http://www.test.com/redirect_3')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

    def test_get_if_modified_since_header(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
            'Last-Modified': 'Tue, 28 Feb 2012 15:50:14 GMT',
            }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-Modified-Since': 'Tue, 28 Feb 2012 15:50:14 GMT'})

    def test_get_if_modified_since_header_not_overridden(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
            'Last-Modified': 'Tue, 28 Feb 2012 15:50:14 GMT',
            }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        get('http://www.test.com/path', headers={'If-Modified-Since': '2011-01-11 00:00:00.000000'})
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-Modified-Since': '2011-01-11 00:00:00.000000'})

    def test_get_if_modified_since_header_no_cache(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=0',
            'Last-Modified': 'Tue, 28 Feb 2012 15:50:14 GMT',
            }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path')

        get('http://www.test.com/path', headers={'If-Modified-Since': 'Sun, 01 Jan 2012 00:00:00 GMT'})
        self.assertEqual(mock_get.call_count, 3)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-Modified-Since': 'Sun, 01 Jan 2012 00:00:00 GMT'})

    def test_get_if_none_match_header(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
            'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
        }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-None-Match': '"fdcd6016cf6059cbbf418d66a51a6b0a"'})

    def test_get_if_none_match_header_not_overridden(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
            'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
        }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        get('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})

    def test_get_if_modified_since_header_no_cache(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'no-cache',
            'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
        }
        mock_get.return_value = response

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path')

        get('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})
        self.assertEqual(mock_get.call_count, 3)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})

    def test_get_304(self, mock_get):
        response0 = Response()
        response0.status_code = 200
        response0._content = 'Mocked response content'
        response0.headers = {
            'Cache-Control': 'max-age=1',
            'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
        }

        response1 = Response()
        response1.status_code = 304
        response1._content = ''
        response1.headers = {
            'Cache-Control': 'max-age=2',
        }
        mock_get.side_effect = [response0, response1, response1, response1]

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(r.status_code, 304)
        self.assertEqual(r.content, 'Mocked response content')
        self.assertEqual(r.headers['Cache-Control'], 'max-age=2')

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(r.status_code, 304)
        self.assertEqual(r.content, 'Mocked response content')

        # Move time forward 3 seconds (1 + 2)
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(r.status_code, 304)
        self.assertEqual(r.content, 'Mocked response content')
        self.assertEqual(r.headers['Cache-Control'], 'max-age=2')

    def test_get_304_cache_not_exist(self, mock_get):
        response0 = Response()
        response0.status_code = 200
        response0._content = 'Mocked response content X'
        response0.headers = {
            'Cache-Control': 'max-age=10',
            'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
            }

        response1 = Response()
        response1.status_code = 304
        response1._content = ''
        response1.headers = {
            'Cache-Control': 'max-age=10',
            }

        response2 = Response()
        response2.status_code = 200
        response2._content = 'Mocked response content Y'
        response2.headers = {
            'Cache-Control': 'max-age=10',
            'ETag': '"a0b6a15a66d814fbbc9506fc6106dcdf"',
            }

        mock_get.side_effect = [response0, response1, response2]

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.content, 'Mocked response content X')

        self.cache.clear()

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(r.content, 'Mocked response content Y')

        r = get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(r.content, 'Mocked response content Y')

    def test_cookie_for_domain(self, mock_get):
        response0 = Response()
        response0.status_code = 200
        response0._content = 'Mocked response content'
        response0.headers = {
            'set-cookie': 'name=value; domain=www.test.com, name2=value2;max-age=20'
        }
        response0.cookies = dict_from_string(response0.headers['set-cookie'])

        response1 = Response()
        response1.status_code = 200
        response1._content = 'Mocked response content'

        response2 = Response()
        response2.status_code = 200
        response2._content = 'Mocked response content'
        response2.headers = {
            'set-cookie': 'other_name=value; domain=www.othertest.com, other_name2=value2;max-age=20'
        }
        response2.cookies = dict_from_string(response0.headers['set-cookie'])

        response3 = Response()
        response3.status_code = 200
        response3._content = 'Mocked response content'
        response3.headers = {
            'set-cookie': 'name3=value3; domain=www.test.com'
        }
        response3.cookies = dict_from_string(response0.headers['set-cookie'])

        mock_get.side_effect = [response0, response3, response0, response1, response2, response2, response0]

        response = get('http://www.test.com/cookie')
        mock_get.assert_called_with('http://www.test.com/cookie')
        self.assertIn('name', response.cookies.keys())
        self.assertTrue(self.cache.get('www.test.com'))

        #all later calls of same domain must send cookies in header
        response = get('http://www.test.com/some_other_path/')
        mock_get.assert_called_with('http://www.test.com/some_other_path/', cookies={'name2': 'value2', 'name': 'value'})

        response = get('http://www.test.com/some_other_path2/')
        mock_get.assert_called_with('http://www.test.com/some_other_path2/', cookies={'name2': 'value2', 'name3': 'value3', 'name': 'value'})

        # other domain get no cookies
        response = get('http://www.other_domain.com/some_other_path2/')
        mock_get.assert_called_with('http://www.other_domain.com/some_other_path2/')

        # other domain get their cookies
        response = get('http://www.othertest.com/')

        self.assertIsNotNone(self.cache.get('www.othertest.com'))
        self.assertIsNotNone(self.cache.get('www.othertest.com.other_name'))
        self.assertIsNotNone(self.cache.get('www.othertest.com.other_name2'))

        response = get('http://www.othertest.com/some_other_path2/')
        mock_get.assert_called_with('http://www.othertest.com/some_other_path2/', cookies={'other_name2': 'value2', 'other_name': 'value'})

        #call first one again, make sure we still send cookie
        response = get('http://www.test.com/some_other_path/')
        mock_get.assert_called_with('http://www.test.com/some_other_path/', cookies={'name2': 'value2', 'name3': 'value3', 'name': 'value'})

    def test_expired_cookie(self, mock_get):

        expire_string = _getdate(future=3)
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'set-cookie': 'other_name=value; expires=%s; domain=www.othertest.com, other_name2=value2;max-age=6' % expire_string
        }
        response.cookies = dict_from_string(response.headers['set-cookie'])


        mock_get.return_value = response
        response = get('http://www.othertest.com/some_other_path2/')

        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)
        response = get('http://www.othertest.com/some_other_path/')
        mock_get.assert_called_with('http://www.othertest.com/some_other_path/', cookies={'other_name2': 'value2', 'other_name': 'value'})

        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=4)
        response = get('http://www.othertest.com/some_other_path/')
        mock_get.assert_called_with('http://www.othertest.com/some_other_path/', cookies={'other_name2': 'value2'})

        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=11)
        response = get('http://www.othertest.com/some_other_path/')
        mock_get.assert_called_with('http://www.othertest.com/some_other_path/')

    def test_set_default_cache(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=100',
        }
        mock_get.return_value = response

        C0 = self.cache
        C1 = Cache()
        C2 = Cache()

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)

        set_default_cache(C1)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)

        set_default_cache(C2)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)

        set_default_cache(C0)

        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)
        get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 3)