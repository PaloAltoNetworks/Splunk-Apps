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
import warnings


class Timer:
    """
    Timer wraps the callback and timestamp related stuff
    """

    _ident = 0
    _lock = threading.Lock()

    def __init__(self, callback, when, interval, ident=None):
        warnings.warn(
            "This class is deprecated. "
            "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
            DeprecationWarning,
            stacklevel=2,
        )
        self._callback = callback
        self._when = when
        self._interval = interval

        if ident is not None:
            self._id = ident
        else:
            with Timer._lock:
                self._id = Timer._ident + 1
                Timer._ident = Timer._ident + 1

    def get_interval(self):
        return self._interval

    def set_interval(self, interval):
        self._interval = interval

    def get_expiration(self):
        return self._when

    def set_initial_due_time(self, when):
        self._when = when

    def update_expiration(self):
        self._when += self._interval

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
        return isinstance(other, Timer) and (self.ident() == other.ident())

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
        self._callback()

    def ident(self):
        return self._id
