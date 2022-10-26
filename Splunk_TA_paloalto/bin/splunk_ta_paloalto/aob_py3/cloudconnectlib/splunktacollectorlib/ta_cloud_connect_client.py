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
from .data_collection.ta_data_client import TaDataClient
from ..splunktacollectorlib.common import log as stulog
from ..splunktacollectorlib.data_collection import ta_consts as c
from ..common.log import set_cc_logger


class TACloudConnectClient(TaDataClient):
    def __init__(self,
                 meta_config,
                 task_config,
                 checkpoint_mgr=None,
                 event_writer=None
                 ):
        super(TACloudConnectClient, self).__init__(meta_config,
                                                   task_config,
                                                   checkpoint_mgr,
                                                   event_writer)
        self._set_log()
        self._cc_config_file = self._meta_config["cc_json_file"]
        from ..core.pipemgr import PipeManager
        from ..client import CloudConnectClient as Client
        self._pipe_mgr = PipeManager(event_writer=event_writer)
        self._client = Client(self._task_config, self._cc_config_file,
                              checkpoint_mgr)

    def _set_log(self):
        pairs = ['{}="{}"'.format(c.stanza_name, self._task_config[
            c.stanza_name])]
        set_cc_logger(stulog.logger,
                          logger_prefix="[{}]".format(" ".join(pairs)))

    def is_stopped(self):
        return self._stop

    def stop(self):
        self._stop = True
        self._client.stop()

    def get(self):
        self._client.start()
        raise StopIteration
