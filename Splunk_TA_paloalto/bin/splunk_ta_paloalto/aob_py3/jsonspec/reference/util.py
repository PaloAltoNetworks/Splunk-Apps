"""
    jsonspec.reference.util
    ~~~~~~~~~~~~~~~~~~~~~~~

"""

__all__ = ['ref', 'Mapping', 'MutableMapping']


def ref(obj):
    """Extracts $ref of object."""
    try:
        return obj['$ref']
    except (KeyError, TypeError):
        return None


try:
    # py3
    from collections.abc import MutableMapping, Mapping
except ImportError:
    # py2
    from collections import MutableMapping, Mapping
