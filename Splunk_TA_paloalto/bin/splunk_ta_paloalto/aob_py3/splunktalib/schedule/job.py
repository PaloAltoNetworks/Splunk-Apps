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


class Job:
    """
    Timer wraps the callback and timestamp related stuff
    """

    _ident = 0
    _lock = threading.Lock()

    def __init__(self, func, job_props, interval, when=None, job_id=None):
        """
        @job_props: dict like object
        @func: execution function
        @interval: execution interval
        @when: seconds from epoch
        @job_id: a unique id for the job
        """

        self._props = job_props
        self._func = func
        if when is None:
            self._when = time.time()
        else:
            self._when = when
        self._interval = interval

        if job_id is not None:
            self._id = job_id
        else:
            with Job._lock:
                self._id = Job._ident + 1
                Job._ident = Job._ident + 1
        self._stopped = False

    def ident(self):
        return self._id

    def get_interval(self):
        return self._interval

    def set_interval(self, interval):
        self._interval = interval

    def get_expiration(self):
        return self._when

    def set_initial_due_time(self, when):
        if self._when is None:
            self._when = when

    def update_expiration(self):
        self._when += self._interval

    def get(self, key, default):
        return self._props.get(key, default)

    def get_props(self):
        return self._props

    def set_props(self, props):
        self._props = props

    def __cmp__(self, other):
        if other is None:
            return 1

        self_k = (self.get_expiration(), self.ident())
        other_k = (other.get_expiration(), other.ident())

        if self_k == other_k:
            return 0
        elif self_k < other_k:
            return -1
        else:
            return 1

    def __eq__(self, other):
        return isinstance(other, Job) and (self.ident() == other.ident())

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __gt__(self, other):
        return self.__cmp__(other) == 1

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __hash__(self):
        return self.ident()

    def __call__(self):
        self._func(self)

    def stop(self):
        self._stopped = True

    def stopped(self):
        return self._stopped
