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
import warnings

import splunktalib.common.xml_dom_parser as xdp
import splunktalib.rest as rest


def _do_rest(uri, session_key):
    resp, content = rest.splunkd_request(uri, session_key)
    if resp is None:
        return None

    if resp.status not in (200, 201):
        return None

    stanza_objs = xdp.parse_conf_xml_dom(content)
    if not stanza_objs:
        return None

    return stanza_objs[0]


class ServerInfo:
    def __init__(self, splunkd_uri, session_key):
        warnings.warn(
            "splunktalib's ServerInfo is going to be deprecated and removed. "
            "Please switch to solnlib's "
            "(https://github.com/splunk/addonfactory-solutions-library-python) "
            "version of ServerInfo located in server_info.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        uri = "{}/services/server/info".format(splunkd_uri)
        server_info = _do_rest(uri, session_key)
        if server_info is None:
            raise Exception("Failed to init ServerInfo")

        self._server_info = server_info

    def is_captain(self):
        """
        :return: True if splunkd_uri is captain otherwise False
        """

        return "shc_captain" in self._server_info["server_roles"]

    def is_search_head(self):
        for sh in ("search_head", "cluster_search_head"):
            if sh in self._server_info["server_roles"]:
                return True
        return False

    def is_shc_member(self):
        for sh in ("shc_member", "shc_captain"):
            if sh in self._server_info["server_roles"]:
                return True
        return False

    def version(self):
        return self._server_info["version"]

    def to_dict(self):
        return self._server_info
