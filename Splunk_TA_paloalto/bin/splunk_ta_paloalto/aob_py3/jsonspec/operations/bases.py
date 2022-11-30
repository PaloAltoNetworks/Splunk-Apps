"""
    jsonspec.operations.bases
    ~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from __future__ import absolute_import

__all__ = ['Target']

from copy import deepcopy
import logging
from jsonspec.pointer import Pointer
from collections import Mapping, MutableSequence
from jsonspec.pointer import ExtractError, OutOfBounds, OutOfRange, LastElement
from .exceptions import Error, NonexistentTarget
logger = logging.getLogger(__name__)


class Target(object):
    """

    :ivar document: the document base
    """

    def __init__(self, document):
        self.document = document

    def check(self, pointer, expected, raise_onerror=False):
        """Check if value exists into object.

        :param pointer: the path to search in
        :param expected: the expected value
        :param raise_onerror: should raise on error?
        :return: boolean
        """
        obj = self.document
        for token in Pointer(pointer):
            try:
                obj = token.extract(obj, bypass_ref=True)
            except ExtractError as error:
                if raise_onerror:
                    raise Error(*error.args)
                logger.exception(error)
                return False
        return obj == expected

    def remove(self, pointer):
        """Remove element from sequence, member from mapping.

        :param pointer: the path to search in
        :return: resolved document
        :rtype: Target
        """
        doc = deepcopy(self.document)
        parent, obj = None, doc
        try:
            # fetching
            for token in Pointer(pointer):
                parent, obj = obj, token.extract(obj, bypass_ref=True)

            # removing
            if isinstance(parent, Mapping):
                del parent[token]

            if isinstance(parent, MutableSequence):
                parent.pop(int(token))
        except Exception as error:
            raise Error(*error.args)

        return Target(doc)

    def add(self, pointer, value):
        """Add element to sequence, member to mapping.

        :param pointer: the path to add in it
        :param value: the new value
        :return: resolved document
        :rtype: Target


        The pointer must reference one of:

        -   The root of the target document - whereupon the specified value
            becomes the entire content of the target document.

        -   A member to add to an existing mapping - whereupon the supplied
            value is added to that mapping at the indicated location.  If the
            member already exists, it is replaced by the specified value.

        -   An element to add to an existing sequence - whereupon the supplied
            value is added to the sequence at the indicated location.
            Any elements at or above the specified index are shifted one
            position to the right.
            The specified index must no be greater than the number of elements
            in the sequence.
            If the "-" character is used to index the end of the sequence, this
            has the effect of appending the value to the sequence.

        """
        doc = deepcopy(self.document)
        parent, obj = None, doc
        try:
            for token in Pointer(pointer):
                parent, obj = obj, token.extract(obj, bypass_ref=True)
            else:
                if isinstance(parent, MutableSequence):
                    raise OutOfRange(parent)
                if isinstance(parent, Mapping):
                    raise OutOfBounds(parent)
                raise Error('already setted')
        except (OutOfBounds, OutOfRange, LastElement) as error:
            if not token.last:
                raise NonexistentTarget(obj)
            value = deepcopy(value)
            if isinstance(error, OutOfBounds):
                error.obj[str(token)] = value
            elif isinstance(error, OutOfRange):
                error.obj.insert(int(token), value)
            elif isinstance(error, LastElement):
                error.obj.append(value)

        return Target(doc)

    def replace(self, pointer, value):
        """Replace element from sequence, member from mapping.

        :param pointer: the path to search in
        :param value: the new value
        :return: resolved document
        :rtype: Target
        """
        doc = deepcopy(self.document)
        parent, obj = None, doc
        try:
            # fetching
            for token in Pointer(pointer):
                parent, obj = obj, token.extract(obj, bypass_ref=True)

            # replace
            value = deepcopy(value)
            if isinstance(parent, Mapping):
                parent[token] = value

            if isinstance(parent, MutableSequence):
                parent[int(token)] = value
        except Exception as error:
            raise Error(*error.args)

        return Target(doc)

    def move(self, dest, src):
        """Move element from sequence, member from mapping.

        :param dest: the destination
        :type dest: Pointer
        :param src: the source
        :type src: Pointer
        :return: resolved document
        :rtype: Target

        .. note::

            This operation is functionally identical to a "remove" operation on
            the "from" location, followed immediately by an "add" operation at
            the target location with the value that was just removed.

            The "from" location MUST NOT be a proper prefix of the "path"
            location; i.e., a location cannot be moved into one of its children

        """

        doc = deepcopy(self.document)

        # delete
        parent, fragment = None, doc
        for token in Pointer(src):
            parent, fragment = fragment, token.extract(fragment,
                                                       bypass_ref=True)

        if isinstance(parent, Mapping):
            del parent[token]

        if isinstance(parent, MutableSequence):
            parent.pop(int(token))

        # insert
        return Target(doc).add(dest, fragment)

    def copy(self, dest, src):
        """Copy element from sequence, member from mapping.

        :param dest: the destination
        :type dest: Pointer
        :param src: the source
        :type src: Pointer
        :return: resolved document
        :rtype: Target
        """
        doc = fragment = deepcopy(self.document)
        for token in Pointer(src):
            fragment = token.extract(fragment, bypass_ref=True)

        return Target(doc).add(dest, fragment)
