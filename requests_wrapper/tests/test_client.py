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