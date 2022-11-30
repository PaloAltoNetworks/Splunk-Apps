"""
    jsonspec.validators
    ~~~~~~~~~~~~~~~~~~~

"""

from .bases import Validator, ReferenceValidator
from .exceptions import CompilationError, ReferenceError, ValidationError
from .factorize import register, Factory, Context
from . import draft04  # noqa
from . import draft03  # noqa
from .draft03 import Draft03Validator  # noqa
from .draft04 import Draft04Validator  # noqa

__all__ = ['load', 'register', 'Factory', 'Context',
           'Validator', 'ReferenceValidator',
           'Draft03Validator', 'Draft04Validator',
           'CompilationError', 'ReferenceError', 'ValidationError']


def load(schema, uri=None, spec=None, provider=None):
    """Scaffold a validator against a schema.

    :param schema: the schema to compile into a Validator
    :type schema: Mapping
    :param uri: the uri of the schema.
                it may be ignored in case of not cross
                referencing.
    :type uri: Pointer, str
    :param spec: fallback to this spec if the schema does not provides ts own
    :type spec: str
    :param provider: the other schemas, in case of cross
                     referencing
    :type provider: Mapping, Provider...
    """
    factory = Factory(provider, spec)
    return factory(schema, uri or '#')
