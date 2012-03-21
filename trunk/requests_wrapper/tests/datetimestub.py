from datetime import datetime


class DatetimeStub(object):
    """
    A datetimestub object to replace methods from the datetime class.
    """

    @classmethod
    def now(cls):
        """
        Override the datetime.now() method to return a specific datetime.
        """
        return datetime.now()

    def __getattr__(self, attr):
        """
        Get the default implementation for the methods from datetime that are not replaced
        """
        return getattr(datetime, attr)