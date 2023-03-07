"""
    jsonspec.reference.bases
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging
from .exceptions import NotFound, Forbidden
from .util import ref, MutableMapping, Mapping
from jsonspec.pointer import DocumentPointer

__all__ = ['LocalRegistry', 'Registry']

logger = logging.getLogger(__name__)


class Provider(Mapping):
    """Defines a generic way to provide external documents"""
    pass


class Registry(Provider, MutableMapping):
    """Register all documents.

    :ivar provider: all documents
    :ivar provider: Provider, dict
    """

    def __init__(self, provider=None):
        self.provider = provider or {}
        super(Registry, self).__init__()

    def prototype(self, dp):
        obj = self[dp.document]
        return self[dp.document], LocalRegistry(obj, self)

    def resolve(self, pointer):
        """Resolve from documents.

        :param pointer: foo
        :type pointer: DocumentPointer
        """

        dp = DocumentPointer(pointer)
        obj, fetcher = self.prototype(dp)

        for token in dp.pointer:
            obj = token.extract(obj, bypass_ref=True)
            reference = ref(obj)
            if reference:
                obj = fetcher.resolve(reference)
        return obj

    def __getitem__(self, uri):
        try:
            return self.provider[uri]
        except KeyError:
            raise NotFound('{!r} not registered'.format(uri))

    def __setitem__(self, uri, obj):
        self.provider[uri] = obj

    def __delitem__(self, uri):
        del self.provider[uri]

    def __len__(self):
        return len(self.provider)

    def __iter__(self):
        return iter(self.provider)


class LocalRegistry(Registry):
    """Scoped registry to a local document.

    :ivar doc: the local document
    :ivar provider: all documents
    :ivar provider: Provider, dict
    :ivar key: current document identifier

    """

    key = '<local>'

    def __init__(self, doc, provider=None):
        self.doc = doc
        self.provider = provider or {}

    def prototype(self, dp):
        if dp.is_inner():
            return self.doc, self
        else:
            obj = self[dp.document]
            return self[dp.document], LocalRegistry(obj, self)

    def __getitem__(self, uri):
        try:
            return self.doc if uri == self.key else self.provider[uri]
        except (NotFound, KeyError):
            raise NotFound('{!r} not registered'.format(uri))

    def __setitem__(self, uri, obj):
        if uri == self.key:
            raise Forbidden('setting {} is forbidden'.format(self.key))
        if uri not in self.provider:
            self.provider[uri] = obj

    def __delitem__(self, uri):
        if uri == self.key:
            raise Forbidden('deleting {} is forbidden'.format(self.key))
        del self.provider[uri]

    def __len__(self):
        return len(set(list(self.provider.keys()) + [self.key]))

    def __iter__(self):
        yield self.key
        for key in self.provider.keys():
            yield key
