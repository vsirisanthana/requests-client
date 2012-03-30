from datetime import datetime

from dummycache import cache as dummycache_cache
from unittest import TestCase

from ..defaults import get_default_cache, get_default_cookie_cache, get_default_redirect_cache
from .datetimestub import DatetimeStub


class BaseTestCase(TestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        dummycache_cache.datetime = DatetimeStub()
        self.cache = get_default_cache()
        self.cache.clear()
        self.cookie_cache = get_default_cookie_cache()
        self.cookie_cache.clear()
        self.redirect_cache = get_default_redirect_cache()
        self.redirect_cache.clear()

    def tearDown(self):
        self.redirect_cache.clear()
        self.cookie_cache.clear()
        self.cache.clear()
        dummycache_cache.datetime = datetime
        super(BaseTestCase, self).tearDown()