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
"""
This module provides Read-Write lock.
"""

from builtins import object
import threading


class _ReadLocker(object):
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock.acquire_read()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release_read()
        return False


class _WriteLocker(object):
    def __init__(self, lock):
        self.lock = lock

    def __enter__(self):
        self.lock.acquire_write()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release_write()
        return False


class RWLock(object):
    """ Simple Read-Write lock.

    Allow multiple read but only one writing concurrently.
    """

    def __init__(self):
        self._condition = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        self._condition.acquire()
        self._readers += 1
        self._condition.release()

    def release_read(self):
        self._condition.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._condition.notifyAll()
        finally:
            self._condition.release()

    def acquire_write(self):
        self._condition.acquire()
        while self._readers > 0:
            self._condition.wait()

    def release_write(self):
        self._condition.release()

    @property
    def reader_lock(self):
        return _ReadLocker(self)

    @property
    def writer_lock(self):
        return _WriteLocker(self)

