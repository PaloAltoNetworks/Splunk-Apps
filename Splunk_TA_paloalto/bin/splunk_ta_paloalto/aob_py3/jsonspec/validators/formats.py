"""
    jsonspec.validators.formats
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import

import logging
from functools import partial
from pkg_resources import iter_entry_points, DistributionNotFound
from .exceptions import CompilationError

__all__ = ['register', 'FormatRegistry']

logger = logging.getLogger(__name__)


class FormatRegistry(object):
    """
    Declare callables that must validate strings.

    Callables are be injected in two ways:

    -   Using the instance register method:

        .. code-block:: python

            registry = FormatRegistry()
            registry.register('foo', bar)

    -   Using the class register method:

        .. code-block:: python

            FormatRegistry.register('foo', bar)
            registry = FormatRegistry()
            assert 'foo' in registry

    -   Every callables declared into setuptools ``entry_points``
        are automatically loaded.

        For example, with this setup.cfg:

        .. code-block:: ini

            [entry_points]
            jsonspec.validators.formats =
                date-time = jsonspec.validators.util:validate_datetime
                email = jsonspec.validators.util:validate_email
                hostname = jsonspec.validators.util:validate_hostname
                ipv4 = jsonspec.validators.util:validate_ipv4
                ipv6 = jsonspec.validators.util:validate_ipv6
                uri = jsonspec.validators.util:validate_uri

        .. code-block:: python

            registry = FormatRegistry()
            assert 'date-time' in registry

    """

    namespace = 'jsonspec.validators.formats'
    custom = {}

    def __init__(self, data=None, namespace=None):
        self.custom = data or self.custom
        self.loaded = {}
        self.fallback = {}
        self.namespace = namespace or self.namespace

    def __getitem__(self, name):
        if name in self.custom:
            return self.custom[name]
        if name in self.loaded:
            return self.loaded[name]
        if name in self.fallback:
            return self.fallback[name]
        return self.load(name)

    def __contains__(self, name):
        return name in self.custom or name in self.loaded

    def load(self, name):
        error = None

        for entrypoint in iter_entry_points(self.namespace):
            try:
                if entrypoint.name == name:
                    self.loaded[name] = entrypoint.load()
                    return self.loaded[name]
            except DistributionNotFound as error:
                pass

        if error:
            logger.warn('Unable to load %s: %s is missing', name, error)
        else:
            logger.warn('%s is not defined', name)

        def fallback(obj):
            logger.info('Unable to validate %s: %s is missing', name, error)
            return obj
        fallback.__doc__ = 'fallback for {!r} validation'.format(name)
        self.fallback[name] = fallback
        return self.fallback[name]

    @classmethod
    def register(cls, name, func):
        cls.custom[name] = func


def register(func=None, name=None):
    """
    Expose compiler to factory.

    :param func: the callable to expose
    :type func: callable
    :param name: name of format
    :type name: str

    It can be used as a decorator::

        @register(name='my:validator')
        def my_validator(obj):
            if obj is True:
                return obj
            raise ValidationError('obj is not true')

    or as a function::

        def my_validator(obj):
            if obj is True:
                return obj
            raise ValidationError('obj is not true')

        @register(name='my:validator')

    """
    if not name:
        raise CompilationError('Name is required')
    if not func:
        return partial(register, name=name)
    return FormatRegistry.register(name, func)
