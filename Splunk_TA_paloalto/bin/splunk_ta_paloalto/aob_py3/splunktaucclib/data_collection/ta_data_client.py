#!/usr/bin/python

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

import splunktaucclib.data_collection.ta_data_collector as tdc
from splunktaucclib.data_collection import ta_checkpoint_manager as cp


def build_event(
    host=None,
    source=None,
    sourcetype=None,
    time=None,
    index=None,
    raw_data="",
    is_unbroken=False,
    is_done=False,
):
    if is_unbroken is False and is_done is True:
        raise Exception("is_unbroken=False is_done=True is invalid")
    return tdc.event_tuple._make(
        [host, source, sourcetype, time, index, raw_data, is_unbroken, is_done]
    )


class TaDataClient:
    def __init__(
        self,
        all_conf_contents,
        meta_config,
        task_config,
        ckpt=None,
        checkpoint_mgr=None,
    ):
        self._all_conf_contents = all_conf_contents
        self._meta_config = meta_config
        self._task_config = task_config
        self._checkpoint_mgr = checkpoint_mgr
        self._ckpt = ckpt or {}
        self._stop = False

    def is_stopped(self):
        return self._stop

    def stop(self):
        self._stop = True

    def get(self):
        raise StopIteration


def create_data_collector(
    dataloader, tconfig, meta_configs, task_config, data_client_cls, checkpoint_cls=None
):
    checkpoint_manager_cls = checkpoint_cls or cp.TACheckPointMgr
    return tdc.TADataCollector(
        tconfig,
        meta_configs,
        task_config,
        checkpoint_manager_cls,
        data_client_cls,
        dataloader,
    )


def client_adapter(job_func):
    class TaDataClientAdapter(TaDataClient):
        def __init__(self, all_conf_contents, meta_config, task_config, ckpt, chp_mgr):
            super().__init__(all_conf_contents, meta_config, task_config, ckpt, chp_mgr)
            self._execute_times = 0
            self._gen = job_func(self._all_conf_contents, self._task_config, self._ckpt)

        def stop(self):
            """
            overwrite to handle stop control command
            """

            # normaly base class just set self._stop as True
            super().stop()

        def get(self):
            """
            overwrite to get events
            """
            self._execute_times += 1
            if self.is_stopped():
                # send stop signal
                self._gen.send(self.is_stopped())
                raise StopIteration
            if self._execute_times == 1:
                return next(self._gen)
            return self._gen.send(self.is_stopped())

    return TaDataClientAdapter
