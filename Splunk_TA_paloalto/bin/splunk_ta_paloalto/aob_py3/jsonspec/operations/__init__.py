"""
    jsonspec.operations
    ~~~~~~~~~~~~~~~~~~~
"""

from __future__ import absolute_import

__all__ = ['check', 'remove', 'add', 'replace', 'move', 'copy',
           'Error', 'NonexistentTarget', 'Target']

from .exceptions import Error, NonexistentTarget
from .bases import Target


def check(doc, pointer, expected, raise_onerror=False):
    """Check if value exists into object.

    :param doc: the document base
    :param pointer: the path to search in
    :param expected: the expected value
    :param raise_onerror: should raise on error?
    :return: boolean
    """
    return Target(doc).check(pointer, expected, raise_onerror)


def remove(doc, pointer):
    """Remove element from sequence, member from mapping.

    :param doc: the document base
    :param pointer: the path to search in
    :return: the new object
    """

    return Target(doc).remove(pointer).document


def add(doc, pointer, value):
    """Add element to sequence, member to mapping.

    :param doc: the document base
    :param pointer: the path to add in it
    :param value: the new value
    :return: the new object
    """
    return Target(doc).add(pointer, value).document


def replace(doc, pointer, value):
    """Replace element from sequence, member from mapping.

    :param doc: the document base
    :param pointer: the path to search in
    :param value: the new value
    :return: the new object

    .. note::

        This operation is functionally identical to a "remove" operation for
        a value, followed immediately by an "add" operation at the same
        location with the replacement value.
    """

    return Target(doc).replace(pointer, value).document


def move(doc, dest, src):
    """Move element from sequence, member from mapping.

    :param doc: the document base
    :param dest: the destination
    :type dest: Pointer
    :param src: the source
    :type src: Pointer
    :return: the new object

    .. note::

        it delete then it add to the new location
        soo the dest must refer to the middle object.

    """

    return Target(doc).move(dest, src).document


def copy(doc, dest, src):
    """Copy element from sequence, member from mapping.

    :param doc: the document base
    :param dest: the destination
    :type dest: Pointer
    :param src: the source
    :type src: Pointer
    :return: the new object
    """

    return Target(doc).copy(dest, src).document
