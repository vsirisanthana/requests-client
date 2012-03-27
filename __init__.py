# -*- coding: utf-8 -*-

#   __           __
#  /  )  _   _  /__)    _/ / _  _
# /__/  (_) (/ /__) (/  / / (- /
#          _/

"""
DogButler
~~~~~~~~

:copyright: (c) 2012 by Vichaya/Euam Sirisanthana.
:license: ISC, see LICENSE for more details.

"""

__title__ = 'requests'
__version__ = '0.0.1'
__build__ = 0x001006
__author__ = 'Vichaya/Euam Sirisanthana'
__license__ = 'ISC'
__copyright__ = 'Copyright 2012 Vichaya/Euam Sirisanthana'


#from . import utils
#from .models import Request, Response
from .api import request, get, head, post, patch, put, delete, options
#from .sessions import session, Session
#from .status_codes import codes
#from .exceptions import (
#    RequestException, Timeout, URLRequired,
#    TooManyRedirects, HTTPError, ConnectionError
#    )
