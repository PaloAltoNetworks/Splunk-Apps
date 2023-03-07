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
from solnlib.pattern import Singleton


class PipeManager(metaclass=Singleton):
    def __init__(self, event_writer=None):
        self._event_writer = event_writer

    def write_events(self, events):
        if not self._event_writer:
            print(events, flush=True)
            return True
        return self._event_writer.write_events(events)
