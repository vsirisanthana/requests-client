from Queue import Queue
from threading import Thread

from . import api


DEFAULT_TIMEOUT = 60 * 5    # in seconds


def get(requests):
    """
    Each request in requests is a tuple of (url, kwargs).
    """
    queues = []         # A list of queues to hold return values
    threads = []        # A list to hold spawned threads
    for url, kwargs in requests:
        q = Queue()
        queues.append(q)

        call_kwargs = dict(kwargs)
        call_kwargs.update({
            'url': url,
            'queue': q,
        })

        t = Thread(target=api.get, kwargs=call_kwargs)
        t.start()
        threads.append(t)

    return [q.get(timeout=DEFAULT_TIMEOUT) for q in queues]