"""
    jsonspec.reference.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""


class NotFound(Exception):
    """raises when a document is not found"""
    pass


class Forbidden(object):
    """raises when a trying to replace <local> document"""
    pass
