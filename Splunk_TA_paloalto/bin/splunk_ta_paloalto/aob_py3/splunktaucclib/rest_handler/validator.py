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

"""Validators
"""


import json
import re

from . import error_ctl

__all__ = [
    "Validator",
    "ValidationError",
    "AnyOf",
    "AllOf",
    "Userdefined",
    "Enum",
    "Range",
    "String",
    "Pattern",
    "Host",
    "Port",
    "RequiredIf",
]


class Validator:
    """Base class of validators."""

    _name = None  # Validator name.
    _msg = "Validation Failed"  # Message when validation failed.

    def __init__(self):
        pass

    def validate(self, value, data):
        """Check if the value is valid.
        :param value: value to validate.
        :param data: payload in request.
        If it is valid, return a boolean value indicate if value is valid.
        """
        raise NotImplementedError

    @property
    def name(self):
        """name of validator."""
        return self._name or self.__class__.__name__

    @property
    def msg(self):
        """message when validation failed."""
        return self._msg


class ValidationError(Exception):
    """Exception from validation."""

    pass


class AnyOf(Validator):
    """A composite validator that accepts values accepted by
    any of its component validators.
    """

    def __init__(self, *validators):
        self._validators = validators

    def validate(self, value, data):
        for validator in self._validators:
            if validator.validate(value, data):
                return True
            else:
                self._msg = validator.msg
        return False


class AllOf(Validator):
    """A composite validator that accepts values accepted by
    all of its component validators.
    """

    def __init__(self, *validators):
        self._validators = validators

    def validate(self, value, data):
        for validator in self._validators:
            if not validator.validate(value, data):
                self._msg = validator.msg
                return False
        return True


class Userdefined(Validator):
    """A validator that defined by user itself.

    The user-defined validator function should be in form:
    ``def fun(value, *args, **kwargs): ...``
    It will be regarded as validation failed if a
    ``ValidationError`` occurred, the exception message
    will be set as exception content.
    And, it should return the validation result ``True`` or ``False``.
    """

    def __init__(self, validator, *args, **kwargs):
        """
        :param values: The collection of valid values
        """
        super().__init__()
        self._validator, self._args, self._kwargs = validator, args, kwargs

    def validate(self, value, data):
        try:
            return self._validator(value, *self._args, **self._kwargs)
        except ValidationError as exc:
            self._msg = exc
        except Exception as exc:
            error_ctl.RestHandlerError.ctl(1000, msgx=exc)
        return False


class Enum(Validator):
    """A validator that accepts only a finite set of values."""

    def __init__(self, values=()):
        """
        :param values: The collection of valid values
        """
        super().__init__()
        try:
            self._values = set(values)
        except:
            self._values = list(values)
        self._msg = "Value should be in " "".format(json.dumps(list(self._values)))

    def validate(self, value, data):
        return value in self._values


class Range(Validator):
    """A validator that accepts values within in a certain range.
    This is for numeric value.

    Condition: minVal <= value <= maxVal
    """

    def __init__(self, minVal=None, maxVal=None):
        """
        :param minVal: If not None, values less than ``minVal`` are invalid.
        :param maxVal: If not None, values larger than ``maxVal`` are invalid.
        """
        minVal_bool = isinstance(minVal, (int, float))
        maxVal_bool = isinstance(maxVal, (int, float))
        assert (minVal is None or minVal_bool) and (
            maxVal is None or maxVal_bool
        ), "``minVal`` & ``maxVal`` should be numeric"
        super().__init__()
        self._minVal, self._maxVal = minVal, maxVal

        if None not in (self._minVal, self._maxVal):
            self._msg = "Value should be between {} and {}" "".format(
                self._minVal, self._maxVal
            )
        elif self._minVal is not None:
            self._msg = "Value should be no smaller than {}" "".format(self._minVal)
        elif self._maxVal is not None:
            self._msg = "Value should be smaller than {}" "".format(self._maxVal)

    def validate(self, value, data):
        try:
            value = float(value)
        except ValueError:
            self._msg = "Invalid format for numeric value"
            return False
        failed = (self._minVal is not None and value < self._minVal) or (
            self._maxVal is not None and value > self._maxVal
        )
        return False if failed else True


class String(Validator):
    """A validator that accepts string values.

    Condition: minLen <= len(value) <= maxLen
    """

    def __init__(self, minLen=None, maxLen=None):
        """Instantiate a String validator.

        :param minLen: If not None,
            strings shorter than ``minLen`` are invalid.
        :param maxLen: If not None,
            strings longer than ``maxLen`` are invalid.
        """
        minLen_bool = isinstance(minLen, (int, float))
        maxLen_bool = isinstance(maxLen, (int, float))
        assert (minLen is None or minLen_bool) and (
            maxLen is None or maxLen_bool
        ), "``minLen`` & ``maxLen`` should be numeric"
        super().__init__()
        self._minLen = 0 if minLen is not None and minLen < 0 else minLen
        self._maxLen = 0 if maxLen is not None and maxLen < 0 else maxLen

        if None not in (self._minLen, self._maxLen):
            self._msg = "Value should be between {} and {}" "".format(
                self._minLen, self._maxLen
            )
        elif self._minLen is not None:
            self._msg = "Value should be no smaller than {}" "".format(self._minLen)
        elif self._maxLen is not None:
            self._msg = "Value should be smaller than {}" "".format(self._maxLen)

    def validate(self, value, data):
        failed = (self._minLen is not None and len(value) < self._minLen) or (
            self._maxLen is not None and len(value) > self._maxLen
        )
        return False if (not isinstance(value, str)) or failed else True


class Pattern(Validator):
    """A validator that accepts strings that match a given regular expression."""

    def __init__(self, regexp, flags=0):
        """
        :param regexp: The regular expression (string or compiled)
            to be matched.
        :param flags: flags value for regular expression.
        """
        super().__init__()
        self._regexp = re.compile(regexp, flags=flags)
        self._msg = "Not matching the pattern"

    def validate(self, value, data):
        return self._regexp.match(value) and True or False


class Host(Pattern):
    """A validator that accepts strings that represent network hostname."""

    def __init__(self):
        regexp = (
            r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
            r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        )
        super().__init__(regexp, flags=re.I)
        self._msg = "Invalid hostname"


class Port(Range):
    """Port number."""

    def __init__(self):
        super().__init__(0, 65535)
        self._msg = "Port number should be an integer between 0 and 65535"

    def validate(self, value, data):
        try:
            value = int(value)
        except ValueError:
            return False
        return super().validate(value, data)


class RequiredIf(Validator):
    """
    Some other fields are required in the payload data of request
    if this one is inputted as some specified values.
    """

    def __init__(self, fields, spec_vals=()):
        """

        :param fields: fields to be checked
        :param spec_vals: specified values for this field.
            If value list is empty, it means any non-empty value.
        :return:
        """
        self.fields = fields
        self.spec_vals = set(spec_vals)

    def validate(self, value, data):
        if self.spec_vals and value not in self.spec_vals:
            return True

        for field in self.fields:
            val = data.get(field, "")
            if not val:
                self._msg = '"%s" is required for input' % field
                return False
        return True
