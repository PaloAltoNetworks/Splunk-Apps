"""
    jsonspec.pointer
    ~~~~~~~~~~~~

    JSON Pointer defines a string syntax for identifying a specific value
    within a JavaScript Object Notation (JSON) document.

"""

from __future__ import absolute_import, print_function, unicode_literals

__all__ = ['extract', 'stage', 'DocumentPointer', 'Pointer', 'PointerToken',
           'ExtractError', 'RefError', 'LastElement', 'OutOfBounds', 'OutOfRange']  # noqa

import logging
from .bases import DocumentPointer, Pointer, PointerToken
from .exceptions import ExtractError, RefError, LastElement, OutOfBounds, OutOfRange, WrongType, UnstagedError, ParseError  # noqa
from .stages import stage

logger = logging.getLogger(__name__)


def extract(obj, pointer, bypass_ref=False):
    """Extract member or element of obj according to pointer.

    :param obj: the object source
    :param pointer: the pointer
    :type pointer: Pointer, str
    :param bypass_ref: bypass JSON Reference event
    :type bypass_ref: boolean
    """

    return Pointer(pointer).extract(obj, bypass_ref)
