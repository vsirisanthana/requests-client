from Cookie import _getdate
from datetime import datetime, timedelta

from dummycache import cache as dummycache_cache
from requests.models import Response

from ..cookie import CookieManager
from ..models import Request
from .base import BaseTestCase


class TestCookie(BaseTestCase):

    def setUp(self):
        super(TestCookie, self).setUp()
        self.cookie_manager = CookieManager(key_prefix='test_cookie', cache=self.cookie_cache)


    def test_domain_cookies(self):
        """
        Test setting and getting domain cookies
        """

        # Cookie cache keys for convenience
        chipsahoy_key   = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'chipsahoy')
        cadbury_key     = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'cadbury')
        kfc_key         = self.cookie_manager.get_domain_cookie_key('food.test.com', '', 'kfc')
        happymeal_key   = self.cookie_manager.get_domain_cookie_key('test.com', '', 'happymeal')

        # Prepare test response
        response = Response()
        response.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Domain=sweet.test.com;, ' +
                          'cadbury=chocolate; Domain=sweet.test.com;, ' +
                          'kfc=chicken; Domain=food.test.com;, ' +
                          'happymeal=meal; Domain=test.com;, '
        }
        response.url = 'http://www.test.com/path'


        ##### Process response cookies #####
        self.cookie_manager.process_response(None, response)    # Note that 'request' is not used (thus None param)

        # Test sweet.test.com cache
        sweet_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com'))
        self.assertIsNotNone(sweet_test_com_cookie_keys_set)
        self.assertEqual(sweet_test_com_cookie_keys_set, set([chipsahoy_key, cadbury_key]))

        chipsahoy_cookie = self.cookie_cache.get(chipsahoy_key)
        self.assertIsNotNone(chipsahoy_cookie)
        self.assertEqual(chipsahoy_cookie.key, 'chipsahoy')
        self.assertEqual(chipsahoy_cookie.value, 'cookie')
        self.assertEqual(chipsahoy_cookie['domain'], 'sweet.test.com')
        self.assertEqual(chipsahoy_cookie['path'], '')

        cadbury_cookie = self.cookie_cache.get(cadbury_key)
        self.assertIsNotNone(cadbury_cookie)
        self.assertEqual(cadbury_cookie.key, 'cadbury')
        self.assertEqual(cadbury_cookie.value, 'chocolate')
        self.assertEqual(cadbury_cookie['domain'], 'sweet.test.com')
        self.assertEqual(cadbury_cookie['path'], '')

        # Test food.test.com cache
        food_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('food.test.com'))
        self.assertIsNotNone(food_test_com_cookie_keys_set)
        self.assertEqual(food_test_com_cookie_keys_set, set([kfc_key]))

        kfc_cookie = self.cookie_cache.get(kfc_key)
        self.assertIsNotNone(kfc_cookie)
        self.assertEqual(kfc_cookie.key, 'kfc')
        self.assertEqual(kfc_cookie.value, 'chicken')
        self.assertEqual(kfc_cookie['domain'], 'food.test.com')
        self.assertEqual(kfc_cookie['path'], '')

        # Test test.com cache
        test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('test.com'))
        self.assertIsNotNone(test_com_cookie_keys_set)
        self.assertEqual(test_com_cookie_keys_set, set([happymeal_key]))

        happymeal_cookie = self.cookie_cache.get(happymeal_key)
        self.assertIsNotNone(happymeal_cookie)
        self.assertEqual(happymeal_cookie.key, 'happymeal')
        self.assertEqual(happymeal_cookie.value, 'meal')
        self.assertEqual(happymeal_cookie['domain'], 'test.com')
        self.assertEqual(happymeal_cookie['path'], '')


        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'happymeal': 'meal'})

        request = Request('http://food.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'kfc': 'chicken', 'happymeal': 'meal'})

        request = Request('http://test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'happymeal': 'meal'})


    def test_weird_domain_cookies(self):
        """
        Test setting and getting domain cookies with weird domain
        """

        # Cookie cache keys for convenience
        chipsahoy_key   = self.cookie_manager.get_domain_cookie_key('.sweet.test.com', '', 'chipsahoy')
        cadbury_key     = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'cadbury')
        kfc_key         = self.cookie_manager.get_domain_cookie_key('..food.test.com', '', 'kfc')
        happymeal_key   = self.cookie_manager.get_domain_cookie_key('.test.com', '', 'happymeal')

        # Prepare test response
        response = Response()
        response.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Domain=.sweet.test.com;, ' +       # Leading . should be ignored
                          'cadbury=chocolate; Domain=sweet.test.com;, ' +
                          'kfc=chicken; Domain=..food.test.com;, ' +            # Leading . should be ignored
                          'happymeal=meal; Domain=.test.com;, ' +               # Leading . should be ignored
                          'baskin=icecream; Domain=food.test.com.'              # Trailing . makes cookie invalid
        }
        response.url = 'http://www.test.com/path'


        ##### Process response cookies #####
        self.cookie_manager.process_response(None, response)    # Note that 'request' is not used (thus None param)

        # Test sweet.test.com cache
        sweet_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com'))
        self.assertIsNotNone(sweet_test_com_cookie_keys_set)
        self.assertEqual(sweet_test_com_cookie_keys_set, set([chipsahoy_key, cadbury_key]))

        chipsahoy_cookie = self.cookie_cache.get(chipsahoy_key)
        self.assertIsNotNone(chipsahoy_cookie)
        self.assertEqual(chipsahoy_cookie.key, 'chipsahoy')
        self.assertEqual(chipsahoy_cookie.value, 'cookie')
        self.assertEqual(chipsahoy_cookie['domain'], '.sweet.test.com')
        self.assertEqual(chipsahoy_cookie['path'], '')

        cadbury_cookie = self.cookie_cache.get(cadbury_key)
        self.assertIsNotNone(cadbury_cookie)
        self.assertEqual(cadbury_cookie.key, 'cadbury')
        self.assertEqual(cadbury_cookie.value, 'chocolate')
        self.assertEqual(cadbury_cookie['domain'], 'sweet.test.com')
        self.assertEqual(cadbury_cookie['path'], '')

        # Test food.test.com cache
        food_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('food.test.com'))
        self.assertIsNotNone(food_test_com_cookie_keys_set)
        self.assertEqual(food_test_com_cookie_keys_set, set([kfc_key]))

        kfc_cookie = self.cookie_cache.get(kfc_key)
        self.assertIsNotNone(kfc_cookie)
        self.assertEqual(kfc_cookie.key, 'kfc')
        self.assertEqual(kfc_cookie.value, 'chicken')
        self.assertEqual(kfc_cookie['domain'], '..food.test.com')
        self.assertEqual(kfc_cookie['path'], '')

        # Test test.com cache
        test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('test.com'))
        self.assertIsNotNone(test_com_cookie_keys_set)
        self.assertEqual(test_com_cookie_keys_set, set([happymeal_key]))

        happymeal_cookie = self.cookie_cache.get(happymeal_key)
        self.assertIsNotNone(happymeal_cookie)
        self.assertEqual(happymeal_cookie.key, 'happymeal')
        self.assertEqual(happymeal_cookie.value, 'meal')
        self.assertEqual(happymeal_cookie['domain'], '.test.com')
        self.assertEqual(happymeal_cookie['path'], '')

        # Test food.test.com. cache. There should be no cache.
        food_test_com_dot_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('food.test.com.'))
        self.assertIsNone(food_test_com_dot_cookie_keys_set)


        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'happymeal': 'meal'})

        request = Request('http://food.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'kfc': 'chicken', 'happymeal': 'meal'})

        request = Request('http://test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'happymeal': 'meal'})


    def test_domain_cookies_with_max_age(self):
        """
        Test setting and getting domain cookies with 'Max-Age' and/or 'Expires' attribute
        """

        # Cache keys for convenience
        lookup_key      = self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com')
        chipsahoy_key   = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'chipsahoy')
        cadbury_key     = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'cadbury')
        kfc_key         = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'kfc')
        happymeal_key   = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'happymeal')

        # Prepare test response
        response = Response()
        response.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Domain=sweet.test.com; Max-Age=3;, ' +
                          'cadbury=chocolate; Domain=sweet.test.com; Max-Age=6;, ' +
                          'kfc=chicken; Domain=sweet.test.com; Expires=%s;, ' % _getdate(future=3) +
                          'happymeal=meal; Domain=sweet.test.com;, '
        }
        response.url = 'http://sweet.test.com/path'


        ##### Process response cookies #####
        self.cookie_manager.process_response(None, response)    # Note that 'request' is not used (thus None param)


        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'kfc': 'chicken', 'happymeal': 'meal'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([chipsahoy_key, cadbury_key, kfc_key, happymeal_key]))

        # 3 seconds pass by
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)

        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'cadbury': 'chocolate', 'happymeal': 'meal'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([cadbury_key, happymeal_key]))

        # 3 more seconds pass by
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=6)

        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'happymeal': 'meal'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([happymeal_key]))


    def test_domain_cookies_with_path(self):
        """
        Test setting and getting domain cookies with 'Path' attribute
        """

        # Cache keys for convenience
        lookup_key      = self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com')
        chipsahoy_key   = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '/', 'chipsahoy')
        cadbury_key     = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '/help', 'cadbury')
        kfc_key         = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '/help/me', 'kfc')
        happymeal_key   = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'happymeal')

        # Prepare test response
        response = Response()
        response.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Domain=sweet.test.com; Path=/;, ' +
                          'cadbury=chocolate; Domain=sweet.test.com; Path=/help;, ' +
                          'kfc=chicken; Domain=sweet.test.com; Path=/help/me;, ' +
                          'happymeal=meal; Domain=sweet.test.com;, '
        }
        response.url = 'http://sweet.test.com/path'


        ##### Process response cookies #####
        self.cookie_manager.process_response(None, response)    # Note that 'request' is not used (thus None param)

        # Test sweet.test.com cache
        sweet_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com'))
        self.assertIsNotNone(sweet_test_com_cookie_keys_set)
        self.assertEqual(sweet_test_com_cookie_keys_set, set([chipsahoy_key, cadbury_key, kfc_key, happymeal_key]))

        chipsahoy_cookie = self.cookie_cache.get(chipsahoy_key)
        self.assertIsNotNone(chipsahoy_cookie)
        self.assertEqual(chipsahoy_cookie.key, 'chipsahoy')
        self.assertEqual(chipsahoy_cookie.value, 'cookie')
        self.assertEqual(chipsahoy_cookie['domain'], 'sweet.test.com')
        self.assertEqual(chipsahoy_cookie['path'], '/')

        cadbury_cookie = self.cookie_cache.get(cadbury_key)
        self.assertIsNotNone(cadbury_cookie)
        self.assertEqual(cadbury_cookie.key, 'cadbury')
        self.assertEqual(cadbury_cookie.value, 'chocolate')
        self.assertEqual(cadbury_cookie['domain'], 'sweet.test.com')
        self.assertEqual(cadbury_cookie['path'], '/help')

        kfc_cookie = self.cookie_cache.get(kfc_key)
        self.assertIsNotNone(kfc_cookie)
        self.assertEqual(kfc_cookie.key, 'kfc')
        self.assertEqual(kfc_cookie.value, 'chicken')
        self.assertEqual(kfc_cookie['domain'], 'sweet.test.com')
        self.assertEqual(kfc_cookie['path'], '/help/me')

        happymeal_cookie = self.cookie_cache.get(happymeal_key)
        self.assertIsNotNone(happymeal_cookie)
        self.assertEqual(happymeal_cookie.key, 'happymeal')
        self.assertEqual(happymeal_cookie.value, 'meal')
        self.assertEqual(happymeal_cookie['domain'], 'sweet.test.com')
        self.assertEqual(happymeal_cookie['path'], '')


        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'happymeal': 'meal'})

        request = Request('http://sweet.test.com/help/me')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'kfc': 'chicken', 'happymeal': 'meal'})

        request = Request('http://sweet.test.com/')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'happymeal': 'meal'})


    def test_origin_cookies(self):
        """
        Test setting and getting origin cookies
        """

        # Cookie cache keys for convenience
        chipsahoy_key   = self.cookie_manager.get_origin_cookie_key('sweet.test.com', '', 'chipsahoy')
        coke_key        = self.cookie_manager.get_origin_cookie_key('pop.test.com', '', 'coke')
        squeeze_key     = self.cookie_manager.get_origin_cookie_key('test.com', '', 'squeeze')

        # Prepare test responses
        response0 = Response()
        response0.headers = {
            'Set-Cookie': 'chipsahoy=cookie;'
        }
        response0.url = 'http://sweet.test.com/path'

        response1 = Response()
        response1.headers = {
            'Set-Cookie': 'coke=soda;'
        }
        response1.url = 'http://pop.test.com/path'

        response2 = Response()
        response2.headers = {
            'Set-Cookie': 'squeeze=juice;'
        }
        response2.url = 'http://test.com/path'


        ##### Process response cookie ####
        self.cookie_manager.process_response(None, response0)    # Note that 'request' is not used (thus None param)
        self.cookie_manager.process_response(None, response1)
        self.cookie_manager.process_response(None, response2)

        # Test sweet.test.com cache
        sweet_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_origin_cookie_lookup_key('sweet.test.com'))
        self.assertIsNotNone(sweet_test_com_cookie_keys_set)
        self.assertEqual(sweet_test_com_cookie_keys_set, set([chipsahoy_key]))

        chipsahoy_cookie = self.cookie_cache.get(chipsahoy_key)
        self.assertIsNotNone(chipsahoy_cookie)
        self.assertEqual(chipsahoy_cookie.key, 'chipsahoy')
        self.assertEqual(chipsahoy_cookie.value, 'cookie')
        self.assertEqual(chipsahoy_cookie['domain'], '')
        self.assertEqual(chipsahoy_cookie['path'], '')

        # Test pop.test.com cache
        pop_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_origin_cookie_lookup_key('pop.test.com'))
        self.assertIsNotNone(pop_test_com_cookie_keys_set)
        self.assertEqual(pop_test_com_cookie_keys_set, set([coke_key]))

        coke_cookie = self.cookie_cache.get(coke_key)
        self.assertIsNotNone(coke_cookie)
        self.assertEqual(coke_cookie.key, 'coke')
        self.assertEqual(coke_cookie.value, 'soda')
        self.assertEqual(coke_cookie['domain'], '')
        self.assertEqual(coke_cookie['path'], '')

        # Test test.com cache
        test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_origin_cookie_lookup_key('test.com'))
        self.assertIsNotNone(test_com_cookie_keys_set)
        self.assertEqual(test_com_cookie_keys_set, set([squeeze_key]))

        squeeze_cookie = self.cookie_cache.get(squeeze_key)
        self.assertIsNotNone(squeeze_cookie)
        self.assertEqual(squeeze_cookie.key, 'squeeze')
        self.assertEqual(squeeze_cookie.value, 'juice')
        self.assertEqual(squeeze_cookie['domain'], '')
        self.assertEqual(squeeze_cookie['path'], '')


        ##### Process request ######
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie'})

        request = Request('http://pop.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'coke': 'soda'})

        request = Request('http://test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'squeeze': 'juice'})


    def test_origin_cookies_with_max_age(self):
        """
        Test setting and getting origin cookies with 'Max-Age' and/or 'Expires' attribute
        """

        # Cookie cache keys for convenience
        lookup_key      = self.cookie_manager.get_origin_cookie_lookup_key('sweet.test.com')
        chipsahoy_key   = self.cookie_manager.get_origin_cookie_key('sweet.test.com', '', 'chipsahoy')
        coke_key        = self.cookie_manager.get_origin_cookie_key('sweet.test.com', '', 'coke')
        squeeze_key     = self.cookie_manager.get_origin_cookie_key('sweet.test.com', '', 'squeeze')
        kitkat_key      = self.cookie_manager.get_origin_cookie_key('sweet.test.com', '', 'kitkat')

        # Prepare test responses
        response0 = Response()
        response0.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Max-Age=3;, ' +
                          'coke=soda; Max-Age=6;, ' +
                          'squeeze=juice; Expires=%s;, ' % _getdate(future=3) +
                          'kitkat=chocolate;'
        }
        response0.url = 'http://sweet.test.com/path'


        ##### Process response cookie ####
        self.cookie_manager.process_response(None, response0)    # Note that 'request' is not used (thus None param)


        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'coke': 'soda', 'squeeze': 'juice', 'kitkat': 'chocolate'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([chipsahoy_key, coke_key, squeeze_key, kitkat_key]))

        # 3 seconds pass by
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=3)

        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'coke': 'soda', 'kitkat': 'chocolate'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([coke_key, kitkat_key]))

        # 3 more seconds pass by
        dummycache_cache.datetime.now = lambda: datetime.now() + timedelta(seconds=6)

        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'kitkat': 'chocolate'})
        cookie_keys_set = self.cookie_cache.get(lookup_key)
        self.assertEqual(cookie_keys_set, set([kitkat_key]))


    def test_domain_and_origin_cookies(self):
        """
        Test setting and getting domain and origin cookies
        """

        # Cookie cache keys for convenience
        chipsahoy_key  = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'chipsahoy')
        cadbury_key    = self.cookie_manager.get_domain_cookie_key('sweet.test.com', '', 'cadbury')
        kfc_key        = self.cookie_manager.get_domain_cookie_key('food.test.com', '', 'kfc')
        happymeal_key  = self.cookie_manager.get_domain_cookie_key('test.com', '', 'happymeal')

        coke_key       = self.cookie_manager.get_origin_cookie_key('www.test.com', '', 'coke')
        squeeze_key    = self.cookie_manager.get_origin_cookie_key('test.com', '', 'squeeze')

        # Prepare test responses
        response0 = Response()
        response0.headers = {
            'Set-Cookie': 'chipsahoy=cookie; Domain=sweet.test.com;, ' +
                          'cadbury=chocolate; Domain=sweet.test.com;, ' +
                          'kfc=chicken; Domain=food.test.com;, ' +
                          'happymeal=meal; Domain=test.com;, ' +
                          'coke=soda;'
        }
        response0.url = 'http://www.test.com/path'

        response1 = Response()
        response1.headers = {
            'Set-Cookie': 'squeeze=juice;'
        }
        response1.url = 'http://test.com/path'


        ##### Process response cookie #####
        self.cookie_manager.process_response(None, response0)    # Note that 'request' is not used (thus None param)
        self.cookie_manager.process_response(None, response1)

        # Test sweet.test.com cache
        sweet_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('sweet.test.com'))
        self.assertIsNotNone(sweet_test_com_cookie_keys_set)
        self.assertEqual(sweet_test_com_cookie_keys_set, set([chipsahoy_key, cadbury_key]))

        chipsahoy_cookie = self.cookie_cache.get(chipsahoy_key)
        self.assertIsNotNone(chipsahoy_cookie)
        self.assertEqual(chipsahoy_cookie.key, 'chipsahoy')
        self.assertEqual(chipsahoy_cookie.value, 'cookie')
        self.assertEqual(chipsahoy_cookie['domain'], 'sweet.test.com')
        self.assertEqual(chipsahoy_cookie['path'], '')

        cadbury_cookie = self.cookie_cache.get(cadbury_key)
        self.assertIsNotNone(cadbury_cookie)
        self.assertEqual(cadbury_cookie.key, 'cadbury')
        self.assertEqual(cadbury_cookie.value, 'chocolate')
        self.assertEqual(cadbury_cookie['domain'], 'sweet.test.com')
        self.assertEqual(cadbury_cookie['path'], '')

        # Test food.test.com cache
        food_test_com_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('food.test.com'))
        self.assertIsNotNone(food_test_com_cookie_keys_set)
        self.assertEqual(food_test_com_cookie_keys_set, set([kfc_key]))

        kfc_cookie = self.cookie_cache.get(kfc_key)
        self.assertIsNotNone(kfc_cookie)
        self.assertEqual(kfc_cookie.key, 'kfc')
        self.assertEqual(kfc_cookie.value, 'chicken')
        self.assertEqual(kfc_cookie['domain'], 'food.test.com')
        self.assertEqual(kfc_cookie['path'], '')

        # Test www.test.com cache
        www_test_com_origin_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_origin_cookie_lookup_key('www.test.com'))
        self.assertIsNotNone(www_test_com_origin_cookie_keys_set)
        self.assertEqual(www_test_com_origin_cookie_keys_set, set([coke_key]))

        coke_cookie = self.cookie_cache.get(coke_key)
        self.assertIsNotNone(coke_cookie)
        self.assertEqual(coke_cookie.key, 'coke')
        self.assertEqual(coke_cookie.value, 'soda')
        self.assertEqual(coke_cookie['domain'], '')
        self.assertEqual(coke_cookie['path'], '')

        # Test test.com cache
        test_com_origin_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_domain_cookie_lookup_key('test.com'))
        self.assertIsNotNone(test_com_origin_cookie_keys_set)
        self.assertEqual(test_com_origin_cookie_keys_set, set([happymeal_key]))

        squeeze_cookie = self.cookie_cache.get(happymeal_key)
        self.assertIsNotNone(squeeze_cookie)
        self.assertEqual(squeeze_cookie.key, 'happymeal')
        self.assertEqual(squeeze_cookie.value, 'meal')
        self.assertEqual(squeeze_cookie['domain'], 'test.com')
        self.assertEqual(squeeze_cookie['path'], '')

        test_com_origin_cookie_keys_set = self.cookie_cache.get(self.cookie_manager.get_origin_cookie_lookup_key('test.com'))
        self.assertIsNotNone(test_com_origin_cookie_keys_set)
        self.assertEqual(test_com_origin_cookie_keys_set, set([squeeze_key]))

        squeeze_cookie = self.cookie_cache.get(squeeze_key)
        self.assertIsNotNone(squeeze_cookie)
        self.assertEqual(squeeze_cookie.key, 'squeeze')
        self.assertEqual(squeeze_cookie.value, 'juice')
        self.assertEqual(squeeze_cookie['domain'], '')
        self.assertEqual(squeeze_cookie['path'], '')
        

        ##### Process request #####
        request = Request('http://sweet.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'chipsahoy': 'cookie', 'cadbury': 'chocolate', 'happymeal': 'meal'})

        request = Request('http://food.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'kfc': 'chicken', 'happymeal': 'meal'})

        request = Request('http://www.test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'coke': 'soda', 'happymeal': 'meal'})

        request = Request('http://test.com/help')
        self.cookie_manager.process_request(request)
        self.assertEqual(request.cookies, {'happymeal': 'meal', 'squeeze': 'juice'})