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
from jinja2 import Template
import re

# This pattern matches the template with only one token inside like "{{
# token1}}", "{{ token2 }"
PATTERN = re.compile(r"^\{\{\s*(\w+)\s*\}\}$")


def compile_template(template):
    _origin_template = template
    _template = Template(template)

    def translate_internal(context):
        match = re.match(PATTERN, _origin_template)
        if match:
            context_var = context.get(match.groups()[0])
            return context_var if context_var else ''
        return _template.render(context)

    return translate_internal
