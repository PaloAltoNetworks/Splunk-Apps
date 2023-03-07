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


class BaseHookMixin:
    """Base Hook Mixin class"""

    def create_hook(self, session_key, config_name, stanza_id, payload):
        """Create hook called before the actual create action

        Args:
            config_name: configuration name
            stanza_id: the id of the stanza to create
            payload: data dict
        """
        pass

    def edit_hook(self, session_key, config_name, stanza_id, payload):
        """Edit hook called before the actual create action

        Args:
            config_name: configuration name
            stanza_id: the id of the stanza to edit
            payload: data dict
        """
        pass

    def delete_hook(self, session_key, config_name, stanza_id):
        """Delete hook called before the actual create action

        Args:
            config_name: configuration name
            stanza_id: the id of the stanza to delete
        """
        pass
