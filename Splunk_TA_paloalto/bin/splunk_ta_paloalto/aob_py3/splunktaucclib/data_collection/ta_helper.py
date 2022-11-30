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
import hashlib
import json
import os.path as op
import re
from calendar import timegm
from datetime import datetime

from splunktalib.common import util

import splunktaucclib.config as sc
from splunktaucclib.data_collection import ta_consts as c


def utc2timestamp(human_time):
    regex1 = r"\d{4}-\d{2}-\d{2}.\d{2}:\d{2}:\d{2}"
    match = re.search(regex1, human_time)
    if match:
        formated = match.group()
    else:
        return None

    strped_time = datetime.strptime(formated, c.time_fmt)
    timestamp = timegm(strped_time.utctimetuple())

    regex2 = r"\d{4}-\d{2}-\d{2}.\d{2}:\d{2}:\d{2}(\.\d+)"
    match = re.search(regex2, human_time)
    if match:
        timestamp += float(match.group(1))
    else:
        timestamp += float("0.000000")
    return timestamp


def get_md5(data):
    """
    function name is not change, actually use sha1 instead
    :param data:
    :return:
    """
    assert data is not None, "The input cannot be None"
    string_type = isinstance(data, str)
    if string_type:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    elif isinstance(data, (list, tuple, dict)):
        return hashlib.sha256(json.dumps(data).encode("utf-8")).hexdigest()


def format_input_name_for_file(name):
    import base64

    base64_name = base64.b64encode(name.encode("utf-8"), b"__").decode("ascii")
    qualified_name_str = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    return f"{qualified_name_str}_B64_{base64_name}"


class ConfigSchemaHandler:
    _app_name = util.get_appname_from_path(op.abspath(__file__))
    # Division schema keys.
    TYPE = "type"

    TYPE_SINGLE = "single"
    TYPE_MULTI = "multi"
    REFER = "refer"
    SEPARATOR = "separator"

    def __init__(self, meta_configs, client_schema):
        self._config = sc.Config(
            splunkd_uri=meta_configs[c.server_uri],
            session_key=meta_configs[c.session_key],
            schema=json.dumps(client_schema[c.config]),
            user="nobody",
            app=ConfigSchemaHandler._app_name,
        )
        self._client_schema = client_schema
        self._all_conf_contents = {}
        self._load_conf_contents()
        self._division_settings = self._divide_settings()

    def get_endpoints(self):
        return self._config.get_endpoints()

    def get_all_conf_contents(self):
        return self._all_conf_contents

    def get_single_conf_contents(self, endpoint):
        return self._all_conf_contents.get(endpoint)

    def get_division_settings(self):
        return self._division_settings

    def _divide_settings(self):
        division_schema = self._client_schema[c.division]
        division_settings = dict()
        for division_endpoint, division_contents in division_schema.items():
            division_settings[division_endpoint] = self._process_division(
                division_endpoint, division_contents
            )
        return division_settings

    def _load_conf_contents(self):
        self._all_conf_contents = self._config.load()

    def _process_division(self, division_endpoint, division_contents):
        division_metrics = []
        assert isinstance(division_contents, dict)
        for division_key, division_value in division_contents.items():
            try:
                assert (
                    self.TYPE in division_value
                    and division_value[self.TYPE] in [self.TYPE_SINGLE, self.TYPE_MULTI]
                    and self.SEPARATOR in division_value
                    if division_value[self.TYPE] == self.TYPE_MULTI
                    else True
                )
            except Exception:
                raise Exception("Invalid division schema")
            division_metrics.append(
                DivisionRule(
                    division_endpoint,
                    division_key,
                    division_value[self.TYPE],
                    division_value.get(
                        self.SEPARATOR,
                    ),
                    division_value.get(
                        self.REFER,
                    ),
                )
            )
        return division_metrics


class DivisionRule:
    def __init__(self, endpoint, metric, type, separator, refer):
        self._endpoint = endpoint
        self._metric = metric
        self._type = type
        self._separator = separator
        self._refer = refer

    def endpoint(self):
        return self._endpoint

    def metric(self):
        return self._metric

    def type(self):
        return self._type

    def separator(self):
        return self._separator

    def refer(self):
        return self._refer
