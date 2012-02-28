from time import sleep

from django.core.cache import cache
from django.test import TestCase
from mock import patch
from requests.models import Response

from requests_wrapper import client


@patch('requests.get')
class TestClient(TestCase):

    def setUp(self):
        cache.clear()

    def test_get_max_age(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=1',
        }
        mock_get.return_value = response

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)

        sleep(1)

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)

    def test_get_different_urls(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        client.get('http://www.test.com/path/1')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path/2')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path/1')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path/3')
        self.assertEqual(mock_get.call_count, 3)
        client.get('http://www.test.com/path/2')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_different_queries(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        client.get('http://www.test.com/path?name=john')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path?name=emily')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path?name=john&age=30')
        self.assertEqual(mock_get.call_count, 3)
        client.get('http://www.test.com/path?name=emily')
        self.assertEqual(mock_get.call_count, 3)
        client.get('http://www.test.com/path?name=john&age=30')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_different_fragments(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        client.get('http://www.test.com/path#help')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path#header')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path#header')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path#footer')
        self.assertEqual(mock_get.call_count, 3)
        client.get('http://www.test.com/path#help')
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

        client.get('http://www.test.com/path', headers={'Accept': 'application/json'})
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path', headers={'Accept': 'application/json'})
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/path', headers={'Accept': 'application/xml'})
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/path', headers={'Accept': 'text/html'})
        self.assertEqual(mock_get.call_count, 3)
        client.get('http://www.test.com/path', headers={'Accept': 'application/json, */*'})
        self.assertEqual(mock_get.call_count, 4)

    def test_get_no_cache_control_header(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        # no cache-control header
        response.headers = {}
        mock_get.return_value = response

        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/nocache_control=True')
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

        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/nocache_control=True')
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

        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 2)
        client.get('http://www.test.com/nocache_control=True')
        self.assertEqual(mock_get.call_count, 3)

    def test_get_cache_201(self, mock_get):
        response = Response()
        response.status_code = 201
        response._content = 'Mocked response content'
        response.headers = {
            'Cache-Control': 'max-age=10',
        }
        mock_get.return_value = response

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 201)

        response = client.get('http://www.test.com/path')
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

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 204)

        response = client.get('http://www.test.com/path')
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

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 400)

        response = client.get('http://www.test.com/path')
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

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 401)

        response = client.get('http://www.test.com/path')
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

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 403)

        response = client.get('http://www.test.com/path')
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

        response = client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(response.status_code, 404)

        response = client.get('http://www.test.com/path')
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


        r = client.get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/neverseemeagain')
        self.assertEqual(r.status_code, 200)

        #assert we not make request to 301 again
        r = client.get('http://www.test.com/neverseemeagain')
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


        r = client.get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/neverseemeagain')
        self.assertEqual(r.status_code, 200)

        # assert we not making any call as we get result from cache
        r = client.get('http://www.test.com/neverseemeagain')
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Mocked response content')

        # assert get the redirected url direct is working fine, and give us result from cache
        r = client.get('http://www.test.com/redirect_here')
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        sleep(1)

        client.get('http://www.test.com/path')
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        sleep(1)

        client.get('http://www.test.com/path', headers={'If-Modified-Since': '2011-01-11 00:00:00.000000'})
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path')

        client.get('http://www.test.com/path', headers={'If-Modified-Since': 'Sun, 01 Jan 2012 00:00:00 GMT'})
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        sleep(1)

        client.get('http://www.test.com/path')
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        sleep(1)

        client.get('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})
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

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 1)
        mock_get.assert_called_with('http://www.test.com/path')

        client.get('http://www.test.com/path')
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with('http://www.test.com/path')

        client.get('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})
        self.assertEqual(mock_get.call_count, 3)
        mock_get.assert_called_with('http://www.test.com/path', headers={'If-None-Match': '"ffffffffffffffffffffffffffffffff"'})
