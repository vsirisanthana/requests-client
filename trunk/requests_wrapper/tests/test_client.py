from time import sleep

from django.core.cache import cache
from django.test import TestCase
from mock import patch
from requests.models import Response

from requests_wrapper import client


class TestClient(TestCase):

    def setUp(self):
        cache.clear()

    @patch('requests.get')
    def test_get_cache_control(self, mock_get):
        response = Response()
        response.status_code = 200
        response._content = 'Test mock'
        response.headers = {
            'Cache-Control': 'max-age=1',
        }
        mock_get.return_value = response

        client.get('http://test')
        self.assertEqual(mock_get.call_count, 1)
        client.get('http://test')
        self.assertEqual(mock_get.call_count, 1)

        sleep(1)

        client.get('http://test')
        self.assertEqual(mock_get.call_count, 2)