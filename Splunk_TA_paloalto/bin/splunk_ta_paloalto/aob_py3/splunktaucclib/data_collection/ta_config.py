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

import os.path as op
import socket

import splunktalib.modinput as modinput
import splunktalib.splunk_cluster as sc
from splunktalib.common import util

import splunktaucclib.common.log as stulog

from . import ta_consts as c
from . import ta_helper as th


# methods can be overrided by subclass : process_task_configs
class TaConfig:
    _current_hostname = socket.gethostname()
    _appname = util.get_appname_from_path(op.abspath(__file__))

    def __init__(self, meta_config, client_schema, stanza_name=None, log_suffix=None):
        self._meta_config = meta_config
        self._stanza_name = stanza_name
        self._log_suffix = log_suffix
        if self._stanza_name and self._log_suffix:
            stulog.reset_logger(
                self._log_suffix
                + "_"
                + th.format_input_name_for_file(self._stanza_name)
            )
            stulog.logger.info(f"Start {self._stanza_name} task")
        self._task_configs = []
        self._client_schema = client_schema
        self._server_info = sc.ServerInfo(
            meta_config[c.server_uri], meta_config[c.session_key]
        )
        self._all_conf_contents = {}
        self._get_division_settings = {}
        self._load_task_configs()
        self._log_level = self._get_log_level()

    def is_shc_but_not_captain(self):
        return self._server_info.is_shc_member() and not self._server_info.is_captain()

    def get_meta_config(self):
        return self._meta_config

    def get_task_configs(self):
        return self._task_configs

    def get_all_conf_contents(self):
        return self._all_conf_contents

    def get_divide_settings(self):
        return self._divide_settings

    def get_log_level(self):
        return self._log_level

    def _load_task_configs(self):
        config_handler = th.ConfigSchemaHandler(self._meta_config, self._client_schema)
        self._all_conf_contents = config_handler.get_all_conf_contents()
        self._divide_settings = config_handler.get_division_settings()
        assert self._divide_settings, "division is empty"
        self._generate_task_configs(self._all_conf_contents, self._divide_settings)

    def _generate_task_configs(self, all_conf_contents, divide_settings):
        all_task_configs = list()
        for division_endpoint, divide_setting in divide_settings.items():
            task_configs = self._get_task_configs(
                all_conf_contents, division_endpoint, divide_setting
            )
            all_task_configs = all_task_configs + task_configs

        for task_config in all_task_configs:
            task_config[c.use_kv_store] = task_config.get(c.use_kv_store, False)
            task_config[c.appname] = TaConfig._appname
            task_config[c.index] = task_config.get(c.index, "default")
            if self._server_info.is_shc_member():
                task_config[c.use_kv_store] = True
            stulog.logger.debug("Task info: %s", task_config)
        self.process_task_configs(all_task_configs)
        # interval
        for task_config in all_task_configs:
            assert task_config.get(c.interval), "task config has no interval " "field"
            task_config[c.interval] = int(task_config[c.interval])
            if task_config[c.interval] <= 0:
                raise ValueError(
                    "The interval value {} is invalid. It "
                    "should be a positive integer".format(task_config[c.interval])
                )
        self._task_configs = all_task_configs
        stulog.logger.info(f"Totally generated {len(self._task_configs)} task configs")

    # Override this method if some transforms or validations needs to be done
    # before task_configs is exposed
    def process_task_configs(self, task_configs):
        if self._stanza_name:
            for task_config in task_configs:
                collection_interval = "collection_interval"
                task_config[c.interval] = task_config.get(collection_interval)

    def _get_log_level(self):
        if not self._client_schema["basic"].get("config_meta"):
            return "INFO"
        if not self._client_schema["basic"]["config_meta"].get("logging_setting"):
            return "INFO"
        paths = self._client_schema["basic"]["config_meta"]["logging_setting"].split(
            ">"
        )
        global_setting = self.get_all_conf_contents()[paths[0].strip()]
        if not global_setting:
            return "INFO"
        log_level = self.get_all_conf_contents()
        for i in range(len(paths)):
            log_level = log_level[paths[i].strip()]
        if not log_level:
            return "INFO"
        else:
            return log_level

    def _get_task_configs(self, all_conf_contents, division_endpoint, divide_setting):
        task_configs = list()
        orig_task_configs = all_conf_contents.get(division_endpoint)
        for (
            orig_task_config_stanza,
            orig_task_config_contents,
        ) in orig_task_configs.items():
            if util.is_true(orig_task_config_contents.get(c.disabled, False)):
                stulog.logger.debug("Stanza %s is disabled", orig_task_config_contents)
                continue
            orig_task_config_contents[c.divide_endpoint] = division_endpoint
            divide_tasks = self._divide_task_config(
                orig_task_config_stanza,
                orig_task_config_contents,
                divide_setting,
                all_conf_contents,
            )
            task_configs = task_configs + divide_tasks
        if self._stanza_name:
            for task_config in task_configs:
                if task_config[c.stanza_name] == self._stanza_name:
                    return [task_config]
        return task_configs

    def _divide_task_config(
        self,
        task_config_stanza,
        task_config_contents,
        divide_setting,
        all_conf_contents,
    ):
        task_config = dict()
        task_config[c.stanza_name] = [self._get_stanza_name(task_config_stanza)]
        multi = 1
        for key, value in task_config_contents.items():
            task_config[key] = [value]
            for divide_rule in divide_setting:
                if divide_rule.metric() == key:
                    if divide_rule.type() == th.ConfigSchemaHandler.TYPE_MULTI:
                        task_config[key] = value.split(divide_rule.separator())
                        multi = multi * len(task_config[key])
        scale_task_config = {}
        times = 0
        for key, value in task_config.items():
            count = multi // len(value)
            scale_task_config[key] = value * count
            if len(value) == 1:
                continue
            times += 1
            if times % 2 == 0:
                scale_task_config[key].sort()
        return self._build_task_configs(
            scale_task_config, all_conf_contents, divide_setting, multi
        )

    def _build_task_configs(
        self, raw_task_config, all_conf_contents, divide_setting, length
    ):
        task_configs = list()
        # split task configs
        for i in range(length):
            task_config = dict()
            # handle endpoint config
            for raw_key, raw_value in raw_task_config.items():
                value = raw_value[i]
                task_config[raw_key] = value
            # handle divide settings
            task_config[c.divide_key] = list()
            for divide_rule in divide_setting:
                task_config[c.divide_key].append(divide_rule.metric())
            task_config[c.divide_key].sort()
            task_configs.append(task_config)
        return task_configs

    def _get_stanza_name(self, input_item):
        if isinstance(input_item, str):
            in_name = input_item
        else:
            in_name = input_item[c.name]

        pos = in_name.find("://")
        if pos > 0:
            in_name = in_name[pos + 3 :]
        return in_name


def create_ta_config(settings, config_cls=TaConfig, log_suffix=None):
    meta_config, configs = modinput.get_modinput_configs_from_stdin()
    if configs and "://" in configs[0].get("name", ""):
        stanza_name = configs[0].get("name").split("://", 1)[1]
    else:
        stanza_name = None
    return config_cls(meta_config, settings, stanza_name, log_suffix)
