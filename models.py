from requests import Response

class Request:

    def __init__(self, url, method='GET', **kwargs):
        self.path = url
        self.method = method
        self.headers = kwargs.get('headers', {})

    def get_full_path(self):
        return self.path

Response.has_header = lambda self, header: header in self.headers
Response.__getitem__ = lambda self, header: self.headers[header]