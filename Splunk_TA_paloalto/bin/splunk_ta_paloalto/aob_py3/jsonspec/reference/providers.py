"""
    jsonspec.reference.providers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import json
import logging
import os
import pkg_resources
from .bases import Provider
from .exceptions import NotFound
from pathlib import Path

__all__ = ['Provider', 'FilesystemProvider', 'PkgProvider', 'SpecProvider']

logger = logging.getLogger(__name__)


class PkgProvider(Provider):
    """
    Autoload providers declared into setuptools ``entry_points``.

    For example, with this setup.cfg:

    .. code-block:: ini

        [entry_points]
        jsonspec.reference.contributions =
            spec = jsonspec.misc.providers:SpecProvider

    """

    namespace = 'jsonspec.reference.contributions'

    def __init__(self, namespace=None, configuration=None):
        self.namespace = namespace or self.namespace
        self.configuration = configuration or {}
        self.loaded = False

    def load(self):
        providers = {}
        for entrypoint in pkg_resources.iter_entry_points(self.namespace):
            kwargs = self.configuration.get(entrypoint.name, {})
            providers[entrypoint.name] = entrypoint.load()(**kwargs)
            logger.debug('loaded %s from %s', entrypoint, entrypoint.dist)
        self.providers = providers
        self.loaded = True

    def __getitem__(self, uri):
        if not self.loaded:
            self.load()

        for name, provider in self.providers.items():
            try:
                value = provider[uri]
                logger.info('got %s from %s', uri, name)
                return value
            except (KeyError, NotFound):
                pass
        raise NotFound('no providers could return {!r}'.format(uri))

    def __iter__(self):
        if not self.loaded:
            self.load()
        for name in self.providers.keys():
            yield name

    def __len__(self):
        if not self.loaded:
            self.load()
        return len(self.providers)


class FilesystemProvider(Provider):
    """
    Exposes json documents stored into filesystem.

    for example, with ``prefix=my:pref:`` and ``directory=my/directory``,
    this filesystem will be loaded as::

        my/directory/
            foo.json        -> my:pref:foo#
            bar.json        -> my:pref:bar#
            baz/
                quux.json   -> my:pref:baz/quux#

    """

    def __init__(self, directory, prefix=None, aliases=None):
        self.directory = directory
        self.prefix = prefix or ''
        self.loaded = False
        self.aliases = aliases or {}

    def _spec_name(self, schema, filename):
        # Let's assume the schema knows its name more accurately than
        # its path can provide.
        if schema.get('id'):
            return schema['id']
        else:
            return filename.as_posix()[len(self.directory):-5].lstrip('/')

    @property
    def data(self):
        if not self.loaded:
            data = {}

            for filename in Path(self.directory).glob('**/*.json'):
                with filename.open() as file:
                    schema = json.load(file)

                # Let's assume the schema knows its name more accurately than
                # its path can provide.
                spec = self._spec_name(schema, filename)
                data[spec] = schema
            # set the fallbacks
            for spec in sorted(data.keys(), reverse=True):
                if spec.startswith('draft-'):
                    metaspec = spec.split('/', 1)[1]
                    if metaspec not in data:
                        data[metaspec] = data[spec]

            self._data = data
            self.loaded = True
        return self._data

    def __getitem__(self, uri):
        spec = uri
        if uri.startswith(self.prefix):
            spec = uri[len(self.prefix):]
            if spec.endswith('#'):
                spec = spec[:-1]

        spec = self.aliases.get(spec, spec)
        try:
            return self.data[spec]
        except (KeyError, UnboundLocalError):
            raise NotFound(uri)

    def __iter__(self):
        for spec in self.data.keys():
            yield '{}{}#'.format(self.prefix, spec)

    def __len__(self):
        return len(self.data.keys())


class SpecProvider(FilesystemProvider):
    """
    Provides specs of http://json-schema.org/
    """

    def __init__(self):
        from jsonspec.misc import __file__ as misc
        base = os.path.realpath(os.path.dirname(misc))
        src = os.path.join(base, 'schemas/')
        prefix = 'http://json-schema.org/'
        super(SpecProvider, self).__init__(src, prefix, aliases={
            'hyper-schema': 'draft-04/hyper-schema',
            'schema': 'draft-04/schema'
        })

    def _spec_name(self, schema, filename):
        return filename.as_posix()[len(self.directory):-5].lstrip('/')


class ProxyProvider(Provider):
    def __init__(self, provider):
        self.provider = provider
        self.local = {}

    def __getitem__(self, uri):
        try:
            return self.local[uri]
        except KeyError:
            return self.provider[uri]

    def __setitem__(self, uri, schema):
        self.local[uri] = schema

    def __iter__(self):
        keys = set(self.local.keys())
        keys.update(self.provider.keys())
        for key in sorted(keys):
            yield key

    def __len__(self):
        keys = set(self.local.keys())
        keys.update(self.provider.keys())
        return len(keys)
