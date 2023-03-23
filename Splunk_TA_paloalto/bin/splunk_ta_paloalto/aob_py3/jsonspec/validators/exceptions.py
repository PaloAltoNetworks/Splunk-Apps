"""
    jsonspec.validators.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import

__all__ = ['CompilationError', 'ReferenceError', 'ValidationError']

from collections import defaultdict


class CompilationError(Exception):
    """Raised while schema parsing"""
    def __init__(self, message, schema):
        super(CompilationError, self).__init__(message, schema)
        self.schema = schema


class ReferenceError(Exception):
    """Raised while reference error"""
    def __init__(self, *args):
        super(ReferenceError, self).__init__(*args)


class ValidationError(ValueError):
    """Raised when validation fails"""
    def __init__(self, reason, obj=None, pointer=None, errors=None):
        """
        :param reason: the reason failing
        :param obj: the obj that fails
        :param errors: sub errors, if they exists
        """
        super(ValidationError, self).__init__(reason, obj)
        self.obj = obj
        self.pointer = pointer

        self.errors = set()
        if isinstance(errors, (list, tuple, set)):
            self.errors.update(errors)
        elif isinstance(errors, Exception):
            self.errors.add(errors)

    def flatten(self):
        """
        Flatten nested errors.

        {pointer: reasons}
        """
        return flatten(self)


def flatten(error):
    def iter_it(src):
        if isinstance(src, (list, set, tuple)):
            for error in src:
                for pointer, reason in iter_it(error):
                    yield pointer, reason
        if isinstance(src, ValidationError):
            if src.errors:
                for pointer, reason in iter_it(src.errors):
                    yield pointer, reason
            if src.pointer:
                yield src.pointer, src.args[0]

    data = defaultdict(set)
    for pointer, reason in iter_it(error):
        data[pointer].add(reason)
    return dict(data)
