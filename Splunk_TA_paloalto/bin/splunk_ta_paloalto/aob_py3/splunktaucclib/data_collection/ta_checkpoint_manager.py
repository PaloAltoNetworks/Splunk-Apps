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

import re
import urllib.error
import urllib.parse
import urllib.request

import splunktalib.state_store as ss

import splunktaucclib.common.log as stulog

from . import ta_consts as c


class TACheckPointMgr:
    SEPARATOR = "___"

    def __init__(self, meta_config, task_config):
        self._task_config = task_config
        self._store = ss.get_state_store(
            meta_config, task_config[c.appname], use_kv_store=self._use_kv_store()
        )
        if isinstance(self._store, ss.CachedFileStateStore):
            stulog.logger.info("State store type is CachedFileStateStore")

    def _use_kv_store(self):
        use_kv_store = self._task_config.get(c.use_kv_store, False)
        if use_kv_store:
            stulog.logger.info(
                "Stanza={} Using KV store for checkpoint".format(
                    self._task_config[c.stanza_name]
                )
            )
        return use_kv_store

    def get_ckpt_key(self):
        return self.key_formatter()

    def get_ckpt(self):
        key = self.get_ckpt_key()
        return self._store.get_state(key)

    def update_ckpt(self, ckpt):
        key = self.get_ckpt_key()
        self._store.update_state(key, ckpt)

    def remove_ckpt(self):
        key = self.get_ckpt_key()
        self._store.delete_state(key)

    def key_formatter(self):
        divide_value = [self._task_config[c.stanza_name]]
        for key in self._task_config[c.divide_key]:
            divide_value.append(self._task_config[key])
        key_str = TACheckPointMgr.SEPARATOR.join(divide_value)
        qualified_key_str = ""
        for i in range(len(key_str)):
            if re.match(r"[^\w]", key_str[i]):
                qualified_key_str += urllib.parse.quote(key_str[i])
            else:
                qualified_key_str += key_str[i]
        return qualified_key_str
