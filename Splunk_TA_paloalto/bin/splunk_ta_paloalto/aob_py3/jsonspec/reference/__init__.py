"""
    jsonspec.reference
    ~~~~~~~~~~~~~~~~~~

    A JSON Reference is a JSON object, which contains a member named
    "$ref", which has a JSON string value.  Example:

    { "$ref": "http://example.com/example.json#/foo/bar" }

    If a JSON value does not have these characteristics, then it SHOULD
    NOT be interpreted as a JSON Reference.

"""

from __future__ import absolute_import, print_function, unicode_literals

from .bases import Registry, LocalRegistry
from .exceptions import NotFound, Forbidden
from jsonspec.pointer import DocumentPointer

__all__ = ['resolve', 'Registry', 'LocalRegistry', 'NotFound', 'Forbidden']


def resolve(obj, pointer, registry=None):
    """resolve a local object

    :param obj: the local object.
    :param pointer: the pointer
    :type pointer: DocumentPointer, str
    :param registry: the registry.
                    It mays be omited if inner json references
                    document don't refer to other documents.
    :type registry: Provider, dict

    .. warning::

        Once pointer is extracted, it won't follow sub mapping /element!
        For example, the value of::

            value = resolve({
                'foo': {'$ref': '#/bar'},
                'bar': [{'$ref': '#/baz'}],
                'baz': 'quux',
            }, '#/foo')

        is::

            assert value == [{'$ref': '#/baz'}]

        and not::

            assert value == ['quux']

    """

    registry = LocalRegistry(obj, registry or {})
    local = DocumentPointer(pointer)

    if local.document:
        registry[local.document] = obj
    local.document = '<local>'
    return registry.resolve(local)
