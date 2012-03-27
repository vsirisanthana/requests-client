from datetime import datetime, timedelta
from unittest import TestCase

from mock import patch
from requests.models import Response
from dummycache import cache as dummycache_cache

from requests_wrapper import async
from requests_wrapper.default_cache import get_default_cache
from requests_wrapper.tests.datetimestub import DatetimeStub


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

    def test_get(self, mock_get):
        # Setup mock
        def side_effect(url, *args, **kwargs):
            if '/1' in url:
                response = Response()
                response.status_code = 200
                response._content = 'Mocked response content X'
                response.headers = {
                    'Cache-Control': 'max-age=1',
                    'ETag': '"fdcd6016cf6059cbbf418d66a51a6b0a"',
                }
            elif '/2' in url:
                response = Response()
                response.status_code = 204
                response._content = 'Mocked response content Y'
                response.headers = {
                    'Cache-Control': 'max-age=1',
                    'ETag': '"ffffffffffffffffffffffffffffffff"',
                }
            else:
                response = Response()
                response.status_code = 403
                response._content = 'Mocked response content Z'
            return response
        mock_get.side_effect = side_effect

        requests = [
            ('http://www.test.com/path/1', {}),
            ('http://www.test.com/path/2', {}),
            ('http://www.test.com/path/3', {}),
        ]

        # Make multiple GET requests
        responses = async.get(requests)
        self.assertEqual(mock_get.call_count, 3)

        self.assertEqual(responses[0].status_code, 200)
        self.assertEqual(responses[0].content, 'Mocked response content X')

        self.assertEqual(responses[1].status_code, 204)
        self.assertEqual(responses[1].content, 'Mocked response content Y')

        self.assertEqual(responses[2].status_code, 403)
        self.assertEqual(responses[2].content, 'Mocked response content Z')

        # Make multiple GET requests again
        # A request to http://www.test.com/path/1 should have been cached
        responses = async.get(requests)
        self.assertEqual(mock_get.call_count, 4)

        self.assertEqual(responses[0].status_code, 200)
        self.assertEqual(responses[0].content, 'Mocked response content X')

        self.assertEqual(responses[1].status_code, 204)
        self.assertEqual(responses[1].content, 'Mocked response content Y')

        self.assertEqual(responses[2].status_code, 403)
        self.assertEqual(responses[2].content, 'Mocked response content Z')

        # Move time forward 1 second
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=1)

        # Make sure the If-None-Match still works
        responses = async.get(requests[:1])
        self.assertEqual(mock_get.call_count, 5)

        mock_get.assert_called_with('http://www.test.com/path/1', headers={'If-None-Match': '"fdcd6016cf6059cbbf418d66a51a6b0a"'})