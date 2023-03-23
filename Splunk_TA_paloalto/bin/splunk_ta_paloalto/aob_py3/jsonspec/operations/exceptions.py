"""
    jsonspec.operations.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from __future__ import absolute_import

__all__ = ['Error', 'NonexistentTarget']


class Error(LookupError):
    pass


class NonexistentTarget(Error):
    """Raised when trying to get a non existent target"""
    pass
