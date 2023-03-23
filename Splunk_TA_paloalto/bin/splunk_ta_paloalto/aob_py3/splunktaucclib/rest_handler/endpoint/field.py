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


from ..error import RestError

__all__ = ["RestField"]


class RestField:
    """
    REST Field.
    """

    def __init__(
        self,
        name,
        required=False,
        encrypted=False,
        default=None,
        validator=None,
        converter=None,
    ):
        self.name = name
        self.required = required
        self.encrypted = encrypted
        self.default = default
        self.validator = validator
        self.converter = converter

    def validate(self, data, existing=None):
        # update case: check required field in data
        if existing and self.name in data and not data.get(self.name) and self.required:
            raise RestError(400, "Required field is missing: %s" % self.name)
        value = data.get(self.name)
        if not value and existing is None:
            if self.required:
                raise RestError(400, "Required field is missing: %s" % self.name)
            return
        if self.validator is None or not value:
            return

        res = self.validator.validate(value, data)
        if not res:
            raise RestError(400, self.validator.msg)

    def encode(self, data):
        value = data.get(self.name)
        if not value or self.converter is None:
            return
        data[self.name] = self.converter.encode(value, data)

    def decode(self, data):
        value = data.get(self.name)
        if not value or self.converter is None:
            return
        data[self.name] = self.converter.decode(value, data)
