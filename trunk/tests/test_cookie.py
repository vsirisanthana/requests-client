from Cookie import SimpleCookie, _getdate
from datetime import datetime, timedelta
from unittest import TestCase

from requests.models import Response
from requests.utils import dict_from_string
from dummycache import cache as dummycache_cache

from ..cookie import get_domain_cookie, extract_cookie
from ..defaults import get_default_cookie_cache
from .datetimestub import DatetimeStub


class TestCookie(TestCase):

    def setUp(self):
        super(TestCookie, self).setUp()
        dummycache_cache.datetime = DatetimeStub()
        self.cache = get_default_cookie_cache()
        self.cache.clear()
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
            self.cache.set(name, cookie, int(cookie['max-age']))

        self.cache.set('www.test.com', self.name_set)

    def tearDown(self):
        self.cache.clear()
        dummycache_cache.datetime = datetime
        super(TestCookie, self).tearDown()

    def test_get_domain_cookie(self):
        # start testing our get domain cookie
        set_cookie = get_domain_cookie('http://www.test.com/somepath')
        self.assertTrue(set_cookie.has_key('oreo'))
        self.assertTrue(set_cookie.has_key('twix'))
        self.assertEqual(set_cookie['oreo'], self.cookies['oreo'].value)
        self.assertEqual(set_cookie['twix'], self.cookies['twix'].value)

        cookie_name_list = self.cache.get('www.test.com')
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

        cookie_name_list = self.cache.get('www.test.com')
        self.assertEquals(len(cookie_name_list), 1)
        self.assertIn('www.test.com.oreo', cookie_name_list)
        self.assertNotIn('www.test.com.twix', cookie_name_list)

        # 3 more seconds so all cookie should expired now
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=6)
        set_cookie = get_domain_cookie('http://www.test.com/somepath')
        self.assertEqual(len(set_cookie), 0)
        self.assertFalse(set_cookie.has_key('oreo'))
        self.assertFalse(set_cookie.has_key('twix'))

        cookie_name_list = self.cache.get('www.test.com')
        self.assertEquals(len(cookie_name_list), 0)
        self.assertNotIn('www.test.com.oreo', cookie_name_list)
        self.assertNotIn('www.test.com.twix', cookie_name_list)

    def test_extract_cookie(self):
        expire_string = _getdate(future=3)
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Set-Cookie': 'chips_ahoy=cookie; expires=%s;, cadbury=chocolate;max-age=3;, coke=soda; expires=%s; max-age=5' % (expire_string, expire_string)
        }
        response.cookies = dict_from_string(response.headers['Set-Cookie'])

        self.assertIsNone(self.cache.get('www.another_test.com'))

        extract_cookie('http://www.another_test.com', response)

        #assert that cookie for domain is there
        name_list = self.cache.get('www.another_test.com')
        self.assertEqual(set(['www.another_test.com.chips_ahoy', 'www.another_test.com.cadbury', 'www.another_test.com.coke']), name_list)

        chips_ahoy = self.cache.get('www.another_test.com.chips_ahoy')
        self.assertIsNotNone(chips_ahoy)
        self.assertEqual('chips_ahoy', chips_ahoy.key)
        self.assertEqual('cookie', chips_ahoy.value)
        self.assertEqual(expire_string, chips_ahoy['expires'])


        cadbury = self.cache.get('www.another_test.com.cadbury')
        self.assertIsNotNone(cadbury)
        self.assertEqual('cadbury', cadbury.key)
        self.assertEqual('chocolate', cadbury.value)
        self.assertEqual('3', cadbury['max-age'])

        coke = self.cache.get('www.another_test.com.coke')
        self.assertIsNotNone(coke)
        self.assertEqual('coke', coke.key)
        self.assertEqual('soda', coke.value)
        self.assertEqual('5', coke['max-age'])
        self.assertEqual(expire_string, coke['expires'])


        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)
        # assert that we set the max-age for cache correctly for both max-age and expires
        chips_ahoy = self.cache.get('www.another_test.com.chips_ahoy')
        self.assertIsNone(chips_ahoy)

        cadbury = self.cache.get('www.another_test.com.cadbury')
        self.assertIsNone(cadbury)

        # should still exist as max-age has higher priority than expires
        coke = self.cache.get('www.another_test.com.coke')
        self.assertIsNotNone(coke)

        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=5)
        coke = self.cache.get('www.another_test.com.coke')
        self.assertIsNone(coke)


    def test_get_path_cookie(self):
        expire_string = _getdate(future=3)
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Set-Cookie': 'chips_ahoy=cookie; expires=%s; path="/sweet", ' \
                          'cadbury=chocolate;max-age=3; path="/sweet/", ' \
                          'coke=soda; path="/soda/"; expires=%s; max-age=5;, '\
                          'cottoncandy=soft; path="/sweet/tooth/";, '\
                          'orange=fruit;, grape=sweet; path="/";' % (expire_string, expire_string)
        }
        response.cookies = dict_from_string(response.headers['Set-Cookie'])

        self.assertIsNone(self.cache.get('www.another_test.com'))

        extract_cookie('http://www.another_test.com', response)

        self.assertIsNotNone(self.cache.get('www.another_test.com'))

        set_cookie = get_domain_cookie('http://www.another_test.com/sweetxxx/')
        self.assertFalse(set_cookie.has_key('chips_ahoy'))
        self.assertFalse(set_cookie.has_key('cadbury'))
        self.assertFalse(set_cookie.has_key('cottoncandy'))
        self.assertFalse(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))


        set_cookie = get_domain_cookie('http://www.another_test.com/sweet/')
        self.assertTrue(set_cookie.has_key('chips_ahoy'))
        self.assertTrue(set_cookie.has_key('cadbury'))
        self.assertFalse(set_cookie.has_key('cottoncandy'))
        self.assertFalse(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))

        set_cookie = get_domain_cookie('http://www.another_test.com/sweet/tooth/')
        self.assertTrue(set_cookie.has_key('chips_ahoy'))
        self.assertTrue(set_cookie.has_key('cadbury'))
        self.assertTrue(set_cookie.has_key('cottoncandy'))
        self.assertFalse(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))

        set_cookie = get_domain_cookie('http://www.another_test.com/soda/')
        self.assertFalse(set_cookie.has_key('chips_ahoy'))
        self.assertFalse(set_cookie.has_key('cadbury'))
        self.assertFalse(set_cookie.has_key('cottoncandy'))
        self.assertTrue(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))

        set_cookie = get_domain_cookie('http://www.another_test.com')
        self.assertFalse(set_cookie.has_key('chips_ahoy'))
        self.assertFalse(set_cookie.has_key('cadbury'))
        self.assertFalse(set_cookie.has_key('cottoncandy'))
        self.assertFalse(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))

        set_cookie = get_domain_cookie('http://www.another_test.com/')
        self.assertFalse(set_cookie.has_key('chips_ahoy'))
        self.assertFalse(set_cookie.has_key('cadbury'))
        self.assertFalse(set_cookie.has_key('cottoncandy'))
        self.assertFalse(set_cookie.has_key('coke'))
        self.assertTrue(set_cookie.has_key('orange'))
        self.assertTrue(set_cookie.has_key('grape'))


    def test_extract_cookie_for_domain_attribute(self):
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Set-Cookie': 'chips_ahoy=cookie; domain=sweet.another_test.com;, cadbury=chocolate; domain=sweet.another_test.com; coke=soda;'
        }
        response.cookies = dict_from_string(response.headers['Set-Cookie'])

        self.assertIsNone(self.cache.get('www.another_test.com'))

        extract_cookie('http://www.another_test.com', response)

        #assert that cookie for domain is there
        sweet_domain_name_list = self.cache.get('sweet.another_test.com')
        self.assertIsNotNone(sweet_domain_name_list)
        self.assertEqual(set(['sweet.another_test.com.chips_ahoy', 'sweet.another_test.com.cadbury']), sweet_domain_name_list)

        chips_ahoy = self.cache.get('sweet.another_test.com.chips_ahoy')
        self.assertIsNotNone(chips_ahoy)
        self.assertEqual('chips_ahoy', chips_ahoy.key)
        self.assertEqual('cookie', chips_ahoy.value)

        origin_name_list = self.cache.get('www.another_test.com')
        self.assertIsNotNone(origin_name_list)
        self.assertEqual(set(['www.another_test.com.coke']), origin_name_list)


    def test_cookie_no_dashed_expires_date_format(self):
        """
        SimpleCookie.loads recognize only dashed date style format, this is to make sure that if server send a new date
        format
        """
        response = Response()
        response.status_code = 200
        response._content = 'Mocked response content'
        response.headers = {
            'Set-Cookie': 'chips_ahoy=cookie; expires=Thu, 12 Jan 2013 12:34:22 GMT;, '
                          'cadbury=chocolate; Expires=Wed, 20-Feb-2014 08:23:55 GMT;, '
                          'coke=soda; Expires = Fri, 02 Jan 2021 GMT;'
        }

        extract_cookie('http://www.test.com', response)

        chips_ahoy = self.cache.get('www.test.com.chips_ahoy')
        self.assertIsNotNone(chips_ahoy)
        self.assertEqual('chips_ahoy', chips_ahoy.key)
        self.assertEqual('cookie', chips_ahoy.value)
        self.assertEqual('Thu, 12-Jan-2013 12:34:22 GMT', chips_ahoy['expires'])

        cadbury = self.cache.get('www.test.com.cadbury')
        self.assertIsNotNone(cadbury)
        self.assertEqual('cadbury', cadbury.key)
        self.assertEqual('chocolate', cadbury.value)
        self.assertEqual('Wed, 20-Feb-2014 08:23:55 GMT', cadbury['expires'])

        # cookie with wrong expires format won't get stored!
        coke = self.cache.get('www.test.com.coke')
        self.assertIsNotNone(coke)
        self.assertEqual('coke', coke.key)
        self.assertEqual('soda', coke.value)
        self.assertEqual('', coke['expires'])





