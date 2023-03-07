"""
    jsonspec.pointer.stages
    ~~~~~~~~~~~~~~~~~~~~~~~

"""
from six import string_types
from collections import Mapping, Sequence, Set

class Staged(object):
    obj = None
    parent_obj = None
    parent_member = None

    def __init__(self, obj, parent=None, member=None):
        self.obj = obj
        self.parent_obj = parent
        self.parent_member = member

    def __getattribute__(self, name):
        if name in ('obj', 'parent_obj', 'parent_member'):
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, 'obj'), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, 'obj'), name)

    def __setattr__(self, name, value):
        if name in ('obj', 'parent_obj', 'parent_member'):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, 'obj'), name, value)

    def __iter__(self):
        return object.__getattribute__(self, 'obj').__iter__()

    def __getitem__(self, key):
        value = object.__getattribute__(self, 'obj').__getitem__(key)
        return Staged(value, self, key)

    def __len__(self):
        return object.__getattribute__(self, 'obj').__len__()

    def __eq__(self, other):
        return object.__getattribute__(self, 'obj') == other

    def __str__(self):
        return object.__getattribute__(self, 'obj').__str__()


def stage(obj, parent=None, member=None):
    """
    Prepare obj to be staged.

    This is almost used for relative JSON Pointers.
    """
    obj = Staged(obj, parent, member)

    if isinstance(obj, Mapping):
        for key, value in obj.items():
            stage(value, obj, key)
    elif isinstance(obj, Sequence) and not isinstance(obj, string_types):
        for index, value in enumerate(obj):
            stage(value, obj, index)
    elif isinstance(obj, Set):
        for value in obj:
            stage(value, obj, None)

    return obj
