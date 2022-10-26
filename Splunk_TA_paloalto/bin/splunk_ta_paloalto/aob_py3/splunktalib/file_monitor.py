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
import traceback
import warnings

from splunktalib.common import log


class FileMonitor:
    def __init__(self, callback, files):
        """
        :files: files to be monidtored with full path
        """
        warnings.warn(
            "This class is deprecated. "
            "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
            DeprecationWarning,
            stacklevel=2,
        )

        self._callback = callback
        self._files = files

        self.file_mtimes = {file_name: None for file_name in self._files}
        for k in self.file_mtimes:
            if not op.exists(k):
                continue

            try:
                if not op.exists(k):
                    continue
                self.file_mtimes[k] = op.getmtime(k)
            except OSError:
                log.logger.error(
                    "Getmtime for %s, failed: %s", k, traceback.format_exc()
                )

    def __call__(self):
        return self.check_changes()

    def check_changes(self):
        log.logger.debug("Checking files=%s", self._files)
        file_mtimes = self.file_mtimes
        changed_files = []
        for f, last_mtime in file_mtimes.items():
            try:
                if not op.exists(f):
                    continue

                current_mtime = op.getmtime(f)
                if current_mtime != last_mtime:
                    file_mtimes[f] = current_mtime
                    changed_files.append(f)
                    log.logger.info("Detect %s has changed", f)
            except OSError:
                pass

        if changed_files:
            if self._callback:
                self._callback(changed_files)
            return True
        return False
