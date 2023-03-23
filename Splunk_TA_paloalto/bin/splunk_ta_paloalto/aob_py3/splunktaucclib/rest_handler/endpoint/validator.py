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

"""
Validators for Splunk configuration.
"""


import json
import re
import warnings
from inspect import isfunction

__all__ = [
    "Validator",
    "ValidationError",
    "AnyOf",
    "AllOf",
    "RequiresIf",
    "UserDefined",
    "Enum",
    "Number",
    "String",
    "Pattern",
    "Host",
    "Port",
    "Datetime",
    "Email",
    "JsonString",
]


class Validator:
    """
    Base class of validators.
    """

    def __init__(self):
        self._msg = ""

    def validate(self, value, data):
        """
        Check if the given value is valid. It assumes that
        the given value is a string.

        :param value: value to validate.
        :param data: whole payload in request.
        :return If the value is invalid, return True.
            Or return False.
        """
        raise NotImplementedError('Function "validate" needs to be implemented.')

    @property
    def msg(self):
        """
        It will return the one with highest priority.

        :return:
        """
        return self._msg if self._msg else "Invalid input value"

    def put_msg(self, msg, *args, **kwargs):
        """
        Put message content into pool.

        :param msg: error message content
        :return:
        """
        if args or "high_priority" in kwargs:
            warnings.warn(
                "`high_priority` arg is deprecated and at a time a single message string is kept in memory."
                " The last message passed to `put_msg` is returned by `msg` property.",
                FutureWarning,
            )
        self._msg = msg


class ValidationFailed(Exception):
    """
    Validation error.
    """

    pass


class AnyOf(Validator):
    """
    A composite of validators that accepts values accepted by
    any of its component validators.
    """

    def __init__(self, *validators):
        """

        :param validators: A list of validators.
        """
        super().__init__()
        self._validators = validators

    def validate(self, value, data):
        msgs = []
        for validator in self._validators:
            if not validator.validate(value, data):
                msgs.append(validator.msg)
            else:
                return True
        else:
            self.put_msg(
                "At least one of the following errors need to be fixed: %s"
                % json.dumps(msgs)
            )
            return False


class AllOf(Validator):
    """
    A composite of validators that accepts values accepted by
    all of its component validators.
    """

    def __init__(self, *validators):
        """

        :param validators: A list of validators.
        """
        super().__init__()
        self._validators = validators

    def validate(self, value, data):
        msgs = []
        for validator in self._validators:
            if not validator.validate(value, data):
                msgs.append(validator.msg)
        if msgs:
            self.put_msg(
                "All of the following errors need to be fixed: %s" % json.dumps(msgs)
            )
            return False
        return True


class RequiresIf(Validator):
    """
    If the given field makes the specified condition as True,
    it requires some other fields are not empty
    in the payload of request.
    """

    def __init__(self, fields, condition=None):
        """

        :param fields: conditionally required field name list.
        :param condition: it can be:
            1. None means any non-empty string for given field
            2. A function takes value & data as parameters and
               returns a boolean value
        """
        assert isinstance(
            fields, (list, set, tuple)
        ), 'Argument "fields" should be list, set or tuple'
        super().__init__()
        self.fields = fields
        self.condition = condition

    @classmethod
    def _is_empty(cls, value):
        return value is None or value == ""

    def validate(self, value, data):
        if self.condition is None and not self._is_empty(value):
            need_validate = True
        else:
            assert isfunction(
                self.condition
            ), "Condition should be a function for RequiresIf validator"
            need_validate = self.condition(value, data)
        if not need_validate:
            return True

        fields = []
        for field in self.fields:
            val = data.get(field)
            if val is None or val == "":
                fields.append(field)
        if fields:
            self.put_msg("For given input, fields are required: %s" % ", ".join(fields))
            return False
        return True


class UserDefined(Validator):
    """
    A validator that defined by user.

    The user-defined validator function should be in form:
    ``def func(value, data, *args, **kwargs): ...``
    ValidationFailed will be raised if validation failed.

    Usage::
    >>> def my_validate(value, data, args):
    >>>     if value != args or not data:
    >>>         raise ValidationFailed('Invalid input')
    >>>
    >>> my_validator = UserDefined(my_validate, 'test_val')
    >>> my_validator.validate('value', {'key': 'value'}, 'value1')

    """

    def __init__(self, validator, *args, **kwargs):
        """

        :param validator: user-defined validating function
        """
        super().__init__()
        self._validator = validator
        self._args = args
        self._kwargs = kwargs

    def validate(self, value, data):
        try:
            self._validator(value, data, *self._args, **self._kwargs)
        except ValidationFailed as exc:
            self.put_msg(str(exc))
            return False
        else:
            return True


class Enum(Validator):
    """
    A validator that accepts only a finite set of values.
    """

    def __init__(self, values=()):
        """

        :param values: The collection of valid values
        """
        super().__init__()
        try:
            self._values = set(values)
        except TypeError:
            self._values = list(values)

        self.put_msg("Value should be in %s" % json.dumps(list(self._values)))

    def validate(self, value, data):
        return value in self._values


class Number(Validator):
    """
    A validator that accepts values within a certain range.
    This is for numeric value.

    Accepted condition: min_val <= value <= max_val
    """

    def __init__(self, min_val=None, max_val=None, is_int=False):
        """

        :param min_val: if not None, it requires min_val <= value
        :param max_val: if not None, it requires value < max_val
        :param is_int: the value should be integer or not
        """

        assert self._check(min_val) and self._check(
            max_val
        ), "{min_val} & {max_val} should be numbers".format(
            min_val=min_val,
            max_val=max_val,
        )

        super().__init__()
        self._min_val = min_val
        self._max_val = max_val
        self._is_int = is_int

    def _check(self, val):
        return val is None or isinstance(val, (int, float))

    def validate(self, value, data):
        try:
            value = int(value) if self._is_int else float(value)
        except ValueError:
            self.put_msg(
                "Invalid format for %s value"
                % ("integer" if self._is_int else "numeric")
            )
            return False

        msg = None
        if not self._min_val and self._max_val and value > self._max_val:
            msg = f"Value should be smaller than {self._max_val}"
        elif not self._max_val and self._min_val and value < self._min_val:
            msg = "Value should be no smaller than {min_val}".format(
                min_val=self._min_val
            )
        elif self._min_val and self._max_val:
            if value < self._min_val or value > self._max_val:
                msg = "Value should be between {min_val} and {max_val}".format(
                    min_val=self._min_val,
                    max_val=self._max_val,
                )
        if msg is not None:
            self.put_msg(msg)
            return False
        return True


class String(Validator):
    """
    A validator that accepts string values.

    Accepted condition: min_len <= len(value) < max_len
    """

    def __init__(self, min_len=None, max_len=None):
        """

        :param min_len: If not None,
            it should be shorter than ``min_len``
        :param max_len: If not None,
            it should be longer than ``max_len``
        """

        assert self._check(min_len) and self._check(
            max_len
        ), "{min_len} & {max_len} should be numbers".format(
            min_len=min_len,
            max_len=max_len,
        )

        super().__init__()
        self._min_len, self._max_len = min_len, max_len

    def _check(self, val):
        if val is None:
            return True
        return isinstance(val, int) and val >= 0

    def validate(self, value, data):
        if not isinstance(value, str):
            self.put_msg("Input value should be string")
            return False

        str_len = len(value)
        msg = None

        if not self._min_len and self._max_len and str_len > self._max_len:
            msg = "String should be shorter than {max_len}".format(
                max_len=self._max_len
            )
        elif self._min_len and not self._max_len and str_len < self._min_len:
            msg = "String should be no shorter than {min_len}".format(
                min_len=self._min_len
            )
        elif self._min_len and self._max_len:
            if str_len < self._min_len or str_len > self._max_len:
                msg = "String length should be between {min_len} and {max_len}".format(
                    min_len=self._min_len,
                    max_len=self._max_len,
                )
        if msg is not None:
            self.put_msg(msg)
            return False
        return True


class Datetime(Validator):
    """
    Date time validation.
    """

    def __init__(self, datetime_format):
        """

        :param datetime_format: Date time format,
            e.g. %Y-%m-%dT%H:%M:%S.%f
        """
        super().__init__()
        self._format = datetime_format

    def validate(self, value, data):
        import datetime

        try:
            datetime.datetime.strptime(value, self._format)
        except ValueError as exc:
            error = f'Wrong datetime with format "{self._format}": {str(exc)}'
            self.put_msg(error)
            return False
        return True


class Pattern(Validator):
    """
    A validator that accepts strings that match
    a given regular expression.
    """

    def __init__(self, regex, flags=0):
        """

        :param regex: The regular expression (string or compiled)
            to be matched.
        :param flags: flags value for regular expression.
        """
        super().__init__()
        self._regexp = re.compile(regex, flags=flags)
        self.put_msg("Not matching the pattern: %s" % regex)

    def validate(self, value, data):
        return self._regexp.match(value) and True or False


class Host(Pattern):
    """
    A validator that accepts strings that represent network hostname.
    """

    def __init__(self):
        regexp = (
            r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
            r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        )
        super().__init__(regexp, flags=re.I)
        self.put_msg("Invalid hostname")


class Port(Number):
    """
    Port number.
    """

    def __init__(self):
        super().__init__(
            min_val=0,
            max_val=65536,
            is_int=True,
        )
        self.put_msg(
            "Invalid port number, it should be a integer between 0 and 65535",
        )


class Email(Pattern):
    """
    A validator that accepts strings that represent network hostname.
    """

    def __init__(self):
        regexp = (
            r"^[A-Z0-9][A-Z0-9._%+-]{0,63}@"
            r"(?:[A-Z0-9](?:[A-Z0-9-]{0,62}[A-Z0-9])?\.){1,8}[A-Z]{2,63}$"
        )
        super().__init__(regexp, flags=re.I)
        self.put_msg("Invalid email address")


class JsonString(Validator):
    """
    Check if the given value is valid JSON string.
    """

    def validate(self, value, data):
        try:
            json.loads(value)
        except ValueError:
            self.put_msg("Invalid JSON string")
            return False
        return True
