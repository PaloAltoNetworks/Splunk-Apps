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
import threading
import time
from collections import namedtuple

from splunktalib.common import util as scu

from ..common import log as stulog
from . import ta_consts as c

evt_fmt = (
    "<stream><event><host>{0}</host>"
    "<source><![CDATA[{1}]]></source>"
    "<sourcetype><![CDATA[{2}]]></sourcetype>"
    "<time>{3}</time>"
    "<index>{4}</index><data>"
    "<![CDATA[{5}]]></data></event></stream>"
)

unbroken_evt_fmt = (
    "<stream>"
    '<event unbroken="1">'
    "<host>{0}</host>"
    "<source><![CDATA[{1}]]></source>"
    "<sourcetype><![CDATA[{2}]]></sourcetype>"
    "<time>{3}</time>"
    "<index>{4}</index>"
    "<data><![CDATA[{5}]]></data>"
    "{6}"
    "</event>"
    "</stream>"
)

event_tuple = namedtuple(
    "Event",
    [
        "host",
        "source",
        "sourcetype",
        "time",
        "index",
        "raw_data",
        "is_unbroken",
        "is_done",
    ],
)


class TADataCollector:
    def __init__(
        self,
        tconfig,
        meta_config,
        task_config,
        checkpoint_manager_cls,
        data_client_cls,
        data_loader,
    ):
        self._lock = threading.Lock()
        self._ta_config = tconfig
        self._meta_config = meta_config
        self._task_config = task_config
        self._stopped = False
        self._p = self._get_logger_prefix()
        self._checkpoint_manager = checkpoint_manager_cls(meta_config, task_config)
        self.data_client_cls = data_client_cls
        self._data_loader = data_loader
        self._client = None

    def get_meta_configs(self):
        return self._meta_config

    def get_task_config(self):
        return self._task_config

    def get_interval(self):
        return self._task_config[c.interval]

    def _get_logger_prefix(self):
        pairs = [f'{c.stanza_name}="{self._task_config[c.stanza_name]}"']
        return "[{}]".format(" ".join(pairs))

    def stop(self):
        self._stopped = True
        if self._client:
            self._client.stop()

    def __call__(self):
        self.index_data()

    def _build_event(self, events):
        if not events:
            return None
        if not isinstance(events, list):
            events = [events]
        evts = []
        for event in events:
            assert event.raw_data, "the raw data of events is empty"
            if event.is_unbroken:
                evt = unbroken_evt_fmt.format(
                    event.host or "",
                    event.source or "",
                    event.sourcetype or "",
                    event.time or "",
                    event.index or "",
                    scu.escape_cdata(event.raw_data),
                    "<done/>" if event.is_done else "",
                )
            else:
                evt = evt_fmt.format(
                    event.host or "",
                    event.source or "",
                    event.sourcetype or "",
                    event.time or "",
                    event.index or "",
                    scu.escape_cdata(event.raw_data),
                )
            evts.append(evt)
        return evts

    def _create_data_client(self):
        return self.data_client_cls(
            self._meta_config,
            self._task_config,
            self._checkpoint_manager,
            self._data_loader.get_event_writer(),
        )

    def index_data(self):
        if self._lock.locked():
            stulog.logger.debug(
                "Last round of stanza={} is not done yet".format(
                    self._task_config[c.stanza_name]
                )
            )
            return
        with self._lock:
            try:
                self._do_safe_index()
                self._checkpoint_manager.close()
            except Exception:
                stulog.logger.exception(f"{self._p} Failed to index data")
            stulog.logger.info(f"{self._p} End of indexing data")
            if not self._ta_config.is_single_instance():
                self._data_loader.tear_down()

    def _write_events(self, events):
        evts = self._build_event(events)
        if evts:
            if not self._data_loader.write_events(evts):
                stulog.logger.info(
                    "{} the event queue is closed and the "
                    "received data will be discarded".format(self._p)
                )
                return False
        return True

    def _do_safe_index(self):
        self._client = self._create_data_client()
        while not self._stopped:
            try:
                events = self._client.get()
                if not events:
                    continue
                else:
                    if not self._write_events(events):
                        break
            except StopIteration:
                stulog.logger.info(f"{self._p} Finished this round")
                return
            except Exception:
                stulog.logger.exception(f"{self._p} Failed to get msg")
                break
        # in case encounter exception or fail to write events
        if not self._stopped:
            self.stop()
