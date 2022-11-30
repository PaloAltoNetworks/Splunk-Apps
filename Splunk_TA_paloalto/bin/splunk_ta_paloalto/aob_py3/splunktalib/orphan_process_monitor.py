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

import os
import threading
import time
import traceback
import warnings

from splunktalib.common import log


class OrphanProcessChecker:
    def __init__(self, callback=None):
        """
        Only work for Linux platform. On Windows platform, is_orphan is always
        False
        """

        if os.name == "nt":
            self._ppid = 0
        else:
            self._ppid = os.getppid()
        self._callback = callback

    def is_orphan(self):
        if os.name == "nt":
            return False
        res = self._ppid != os.getppid()
        if res:
            log.logger.warn("Process=%s has become orphan", os.getpid())
        return res

    def check_orphan(self):
        res = self.is_orphan()
        if res and self._callback:
            self._callback()
        return res


class OrphanProcessMonitor:
    def __init__(self, callback):
        warnings.warn(
            "splunktalib's OrphanProcessMonitor is going to be deprecated and "
            "removed. Please switch to solnlib's "
            "(https://github.com/splunk/addonfactory-solutions-library-python) "
            "version of OrphanProcessMonitor located in orphan_process_monitor.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._checker = OrphanProcessChecker(callback)
        self._thr = threading.Thread(target=self._do_monitor)
        self._thr.daemon = True
        self._started = False

    def start(self):
        if self._started:
            return
        self._started = True

        self._thr.start()

    def stop(self):
        self._started = False

    def _do_monitor(self):
        while self._started:
            try:
                res = self._checker.check_orphan()
                if res:
                    break
                time.sleep(1)
            except Exception:
                log.logger.error(
                    "Failed to monitor orphan process, reason=%s",
                    traceback.format_exc(),
                )
