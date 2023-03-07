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


# EAI fields

EAI_ACL = "eai:acl"
EAI_ATTRIBUTES = "eai:attributes"
EAI_USER = "eai:userName"
EAI_APP = "eai:appName"

EAI_FIELD_PREFIX = "eai:"
EAI_FIELDS = [EAI_ACL, EAI_ATTRIBUTES, EAI_USER, EAI_APP]

# elements of eai:attributes
EAI_ATTRIBUTES_OPTIONAL = "optionalFields"
EAI_ATTRIBUTES_REQUIRED = "requiredFields"
EAI_ATTRIBUTES_WILDCARD = "wildcardFields"


class RestEAI:
    def __init__(self, model, user, app, acl=None):
        self.model = model
        default_acl = {
            "owner": user,
            "app": app,
            "global": 1,
            "can_write": 1,
            "modifiable": 1,
            "removable": 1,
            "sharing": "global",
            "perms": {"read": ["*"], "write": ["admin"]},
        }
        self.acl = acl or default_acl
        self.user = user
        self.app = app
        self.attributes = self._build_attributes()

    @property
    def content(self):
        return {
            EAI_ACL: self.acl,
            EAI_USER: self.user,
            EAI_APP: self.app,
            EAI_ATTRIBUTES: self.attributes,
        }

    def _build_attributes(self):
        optional_fields = []
        required_fields = []
        for field in self.model.fields:
            if field.required:
                required_fields.append(field.name)
            else:
                optional_fields.append(field.name)
        return {
            EAI_ATTRIBUTES_OPTIONAL: optional_fields,
            EAI_ATTRIBUTES_REQUIRED: required_fields,
            EAI_ATTRIBUTES_WILDCARD: [],
        }
