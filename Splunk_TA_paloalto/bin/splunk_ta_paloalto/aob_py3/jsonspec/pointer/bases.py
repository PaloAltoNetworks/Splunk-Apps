"""
    jsonspec.pointer.bases
    ~~~~~~~~~~~~~~~~~~~~~~

"""


__all__ = ['DocumentPointer', 'Pointer', 'PointerToken']

import logging
from abc import abstractmethod, ABCMeta
from six import add_metaclass, string_types
from collections import Mapping, Sequence, MutableSequence
from .exceptions import ExtractError, RefError, LastElement, OutOfBounds, OutOfRange, WrongType, UnstagedError, ParseError  # noqa

logger = logging.getLogger(__name__)


class DocumentPointer(object):
    """Defines a document pointer

    :ivar document: document name
    :ivar pointer: pointer
    """

    def __init__(self, pointer):
        """
        :param pointer: a string or DocumentPointer instance
        """
        if isinstance(pointer, DocumentPointer):
            document, path = pointer
        elif '#' not in pointer:
            logger.debug('# is missing %r', pointer)
            document, path = pointer, ''
        else:
            document, path = pointer.split('#', 1)
        self.document = document
        self.pointer = Pointer(path)

    def extract(self, obj, bypass_ref=False):
        """
        Extract subelement from obj, according to pointer.
        It assums that document is the object.

        :param obj: the object source
        :param bypass_ref: disable JSON Reference errors
        """
        return self.pointer.extract(obj, bypass_ref)

    def is_inner(self):
        """Tells if pointer refers to an inner document
        """
        return self.document == ''

    def endswith(self, txt):
        """used by os.path.join"""
        return str(self).endswith(txt)

    def __iadd__(self, txt):
        """append fragments"""
        data = str(self) + txt
        return DocumentPointer(data)

    def __iter__(self):
        """Return document and pointer.
        """
        return iter([self.document, self.pointer])

    def __eq__(self, other):
        if isinstance(other, string_types):
            return other == self.__str__()
        return super(Pointer, self).__eq__(other)

    def __str__(self):
        return '{}#{}'.format(self.document, self.pointer)

    def __repr__(self):
        return '<DocumentPointer({})'.format(self)


class Pointer(object):
    """Defines a pointer

    :ivar tokens: list of PointerToken
    """

    def __init__(self, pointer):
        """
        :param pointer: a string or Pointer instance
        """
        self.tokens = self.parse(pointer)

        if self.tokens:
            self.tokens[-1].last = True

    def parse(self, pointer):
        """parse pointer into tokens"""
        if isinstance(pointer, Pointer):
            return pointer.tokens[:]
        elif pointer == '':
            return []

        tokens = []
        staged, _, children = pointer.partition('/')
        if staged:
            try:
                token = StagesToken(staged)
                token.last = False
                tokens.append(token)
            except ValueError:
                raise ParseError('pointer must start with / or int', pointer)

        if _:
            for part in children.split('/'):
                part = part.replace('~1', '/')
                part = part.replace('~0', '~')
                token = ChildToken(part)
                token.last = False
                tokens.append(token)

        return tokens

    def extract(self, obj, bypass_ref=False):
        """
        Extract subelement from obj, according to tokens.

        :param obj: the object source
        :param bypass_ref: disable JSON Reference errors
        """
        for token in self.tokens:
            obj = token.extract(obj, bypass_ref)
        return obj

    def __iter__(self):
        """Walk thru tokens.
        """
        return iter(self.tokens)

    def __eq__(self, other):
        if isinstance(other, string_types):
            return other == self.__str__()
        return super(Pointer, self).__eq__(other)

    def __str__(self):
        output = ''
        for part in self.tokens:
            if isinstance(part, StagesToken):
                output += part
                continue
            part = part.replace('~', '~0')
            part = part.replace('/', '~1')
            output += '/' + part
        return output

    def __repr__(self):
        return '<{}({!r})>'.format(self.__class__.__name__, self.__str__())


@add_metaclass(ABCMeta)
class PointerToken(str):
    """
    A single token
    """

    @abstractmethod
    def extract(self, obj, bypass_ref=False):
        """
        Extract parents or subelement from obj, according to current token.

        :param obj: the object source
        :param bypass_ref: disable JSON Reference errors
        """
        pass


class StagesToken(PointerToken):
    """
    A parent token
    """

    def __init__(self, value, *args, **kwargs):
        value = str(value)
        member = False
        if value.endswith('#'):
            value = value[:-1]
            member = True
        self.stages = int(value)
        self.member = member

    def extract(self, obj, bypass_ref=False):
        """
        Extract parent of obj, according to current token.

        :param obj: the object source
        :param bypass_ref: not used
        """
        for i in range(0, self.stages):
            try:
                obj = obj.parent_obj
            except AttributeError:
                raise UnstagedError(obj, '{!r} must be staged before '
                                         'exploring its parents'.format(obj))
        if self.member:
            return obj.parent_member
        return obj


class ChildToken(PointerToken):
    """
    A child token
    """
    def extract(self, obj, bypass_ref=False):
        """
        Extract subelement from obj, according to current token.

        :param obj: the object source
        :param bypass_ref: disable JSON Reference errors
        """
        try:
            if isinstance(obj, Mapping):
                if not bypass_ref and '$ref' in obj:
                    raise RefError(obj, 'presence of a $ref member')
                obj = self.extract_mapping(obj)
            elif isinstance(obj, Sequence) and not isinstance(obj, string_types):
                obj = self.extract_sequence(obj)
            else:
                raise WrongType(obj, '{!r} does not apply '
                                     'for {!r}'.format(str(self), obj))

            if isinstance(obj, Mapping):
                if not bypass_ref and '$ref' in obj:
                    raise RefError(obj, 'presence of a $ref member')
            return obj
        except ExtractError as error:
            logger.exception(error)
            raise
        except Exception as error:
            logger.exception(error)
            args = [arg for arg in error.args if arg not in (self, obj)]
            raise ExtractError(obj, *args)

    def extract_mapping(self, obj):
        if self in obj:
            return obj[self]

        if self.isdigit():
            key = int(self)
            if key in obj:
                return obj[key]

        raise OutOfBounds(obj, 'member {!r} not found'.format(str(self)))

    def extract_sequence(self, obj):
        if self == '-':
            raise LastElement(obj, 'last element is needed')
        if not self.isdigit():
            raise WrongType(obj, '{!r} does not apply '
                                 'for sequence'.format(str(self)))
        try:
            return obj[int(self)]
        except IndexError:
            raise OutOfRange(obj, 'element {!r} not found'.format(str(self)))

    def __repr__(self):
        return '<{}({!r})>'.format(self.__class__.__name__, str(self))
