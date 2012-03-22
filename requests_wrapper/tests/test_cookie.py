from Cookie import SimpleCookie, _getdate
from datetime import datetime, timedelta
from unittest import TestCase

from requests.models import Response
from requests.utils import dict_from_string
from dummycache import cache as dummycache_cache

from requests_wrapper.cookie import get_domain_cookie, extract_cookie
from requests_wrapper.default_cache import cache
from requests_wrapper.tests.datetimestub import DatetimeStub


class TestCookie(TestCase):

    def setUp(self):
        super(TestCookie, self).setUp()
        dummycache_cache.datetime = DatetimeStub()
        cache.clear()
        # prepare cookie
        self.cookies = SimpleCookie()
        self.cookies['oreo'] = 'yumm'
        self.cookies['oreo']['max-age']= 5
        self.cookies['twix'] = 'yumm yummm'
        self.cookies['twix']['max-age']= 3
        self.name_set = set()
        for cookie_name, cookie in self.cookies.items():
            name = 'www.test.com.%s' % cookie_name
            self.name_set.add(name)
            cache.set(name, cookie, int(cookie['max-age']))

        cache.set('www.test.com', self.name_set)

    def tearDown(self):
        cache.clear()
        dummycache_cache.datetime = datetime
        super(TestCookie, self).tearDown()

    def test_get_domain_cookie(self):
        # start testing our get domain cookie
        set_cookie = get_domain_cookie('http://www.test.com/somepath')
        self.assertTrue(set_cookie.has_key('oreo'))
        self.assertTrue(set_cookie.has_key('twix'))
        self.assertEqual(set_cookie['oreo'], self.cookies['oreo'].value)
        self.assertEqual(set_cookie['twix'], self.cookies['twix'].value)

        cookie_name_list = cache.get('www.test.com')
        self.assertEquals(len(cookie_name_list), 2)
        self.assertIn('www.test.com.oreo', cookie_name_list)
        self.assertIn('www.test.com.twix', cookie_name_list)
        self.assertEqual(cookie_name_list, self.name_set)

    def test_get_domain_update_cookie_list_when_cookie_expired(self):

        # 3 seconds pass by
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)
        set_cookie = get_domain_cookie('http://www.test.com/somepath')
        self.assertEqual(len(set_cookie), 1)
        self.assertTrue(set_cookie.has_key('oreo'))
        self.assertFalse(set_cookie.has_key('twix'))
        self.assertEqual(set_cookie['oreo'], self.cookies['oreo'].value)

        cookie_name_list = cache.get('www.test.com')
        self.assertEquals(len(cookie_name_list), 1)
        self.assertIn('www.test.com.oreo', cookie_name_list)
        self.assertNotIn('www.test.com.twix', cookie_name_list)

        # 3 more seconds so all cookie should expired now
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=6)
        set_cookie = get_domain_cookie('http://www.test.com/somepath')
        self.assertEqual(len(set_cookie), 0)
        self.assertFalse(set_cookie.has_key('oreo'))
        self.assertFalse(set_cookie.has_key('twix'))

        cookie_name_list = cache.get('www.test.com')
        self.assertEquals(len(cookie_name_list), 0)
        self.assertNotIn('www.test.com.oreo', cookie_name_list)
        self.assertNotIn('www.test.com.twix', cookie_name_list)

    def test_extract_cookie(self):
        expire_string = _getdate(future=3)
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'set-cookie': 'chips_ahoy=cookie; expires=%s;, cadbury=chocolate;max-age=3;, coke=soda; expires=%s; max-age=5' % (expire_string, expire_string)
        }
        response.cookies = dict_from_string(response.headers['set-cookie'])

        self.assertIsNone(cache.get('www.another_test.com'))

        extract_cookie('http://www.another_test.com', response)

        #assert that cookie for domain is there
        name_list = cache.get('www.another_test.com')
        self.assertEqual(set(['www.another_test.com.chips_ahoy', 'www.another_test.com.cadbury', 'www.another_test.com.coke']), name_list)

        chips_ahoy = cache.get('www.another_test.com.chips_ahoy')
        self.assertIsNotNone(chips_ahoy)
        self.assertEqual('chips_ahoy', chips_ahoy.key)
        self.assertEqual('cookie', chips_ahoy.value)
        self.assertEqual(expire_string, chips_ahoy['expires'])


        cadbury = cache.get('www.another_test.com.cadbury')
        self.assertIsNotNone(cadbury)
        self.assertEqual('cadbury', cadbury.key)
        self.assertEqual('chocolate', cadbury.value)
        self.assertEqual('3', cadbury['max-age'])

        coke = cache.get('www.another_test.com.coke')
        self.assertIsNotNone(coke)
        self.assertEqual('coke', coke.key)
        self.assertEqual('soda', coke.value)
        self.assertEqual('5', coke['max-age'])
        self.assertEqual(expire_string, coke['expires'])


        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)
        # assert that we set the max-age for cache correctly for both max-age and expires
        chips_ahoy = cache.get('www.another_test.com.chips_ahoy')
        self.assertIsNone(chips_ahoy)

        cadbury = cache.get('www.another_test.com.cadbury')
        self.assertIsNone(cadbury)

        # should still exist as max-age has higher priority than expires
        coke = cache.get('www.another_test.com.coke')
        self.assertIsNotNone(coke)

        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=5)
        coke = cache.get('www.another_test.com.coke')
        self.assertIsNone(coke)
