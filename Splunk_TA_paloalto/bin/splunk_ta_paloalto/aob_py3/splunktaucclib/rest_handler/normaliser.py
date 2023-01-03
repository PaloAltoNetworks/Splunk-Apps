#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Normalisers
"""


__all__ = ["Normaliser", "Boolean", "StringLower", "StringUpper"]


class Normaliser:
    """Base class of Normaliser."""

    _name = None

    def __init__(self):
        pass

    def normalize(self, value):
        """Normalize a given value.

        :param value: value to normalize.
        :returns: normalized value.
        """
        raise NotImplementedError

    @property
    def name(self):
        """name of normaliser."""
        return self._name or self.__class__.__name__


class Userdefined(Normaliser):
    """A Normaliser that defined by user itself.

    The user-defined normaliser function should be in form:
    ``def fun(value, *args, **kwargs): ...``
    It will return the original data if any exception occurred.
    """

    def __init__(self, normaliser, *args, **kwargs):
        """
        :param values: The collection of valid values
        """
        super().__init__()
        self._normaliser, self._args, self._kwargs = normaliser, args, kwargs

    def normalize(self, value):
        try:
            return self._normaliser(value, *self._args, **self._kwargs)
        except:
            return value


class Boolean(Normaliser):
    """Normalize a boolean field.

    Normalize given value to boolean: ``0`` or ``1``.
    ``default`` means the return for unrecognizable input of boolean.
    """

    def __init__(self, default=True):
        super().__init__()
        self._default = "1" if default else "0"

    def normalize(self, value):
        if isinstance(value, (bool, int)):
            return value and "1" or "0"
        if not isinstance(value, str):
            return self._default
        value = value.strip().lower()

        vals = {
            "1": {"true", "t", "1", "yes", "y"},
            "0": {"false", "f", "0", "no", "n"},
        }
        revDef = {"1": "0", "0": "1"}[self._default]
        return revDef if value in vals[revDef] else self._default


class StringLower(Normaliser):
    """Normalize a string to all lower cases."""

    def normalize(self, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class StringUpper(Normaliser):
    """Normalize a string to all upper cases."""

    def normalize(self, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value
