from requests import Response
from requests.structures import CaseInsensitiveDict

class Request(object):

    def __init__(self, url, method='GET', **kwargs):
        self.url = url
        self.method = method
        self.cookies = kwargs.get('cookies', {})
        self.headers = CaseInsensitiveDict(kwargs.get('headers', {}))

    @property
    def path(self):
        return self.url

    def get_full_path(self):
        return self.path

Response.has_header = lambda self, header: header in self.headers
Response.__getitem__ = lambda self, header: self.headers[header]