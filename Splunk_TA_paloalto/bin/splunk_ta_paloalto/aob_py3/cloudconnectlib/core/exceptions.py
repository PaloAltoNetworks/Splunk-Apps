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
"""APP Cloud Connect errors"""


class CCEError(Exception):
    pass


class ConfigException(CCEError):
    """Config exception"""
    pass


class FuncException(CCEError):
    """Ext function call exception"""
    pass


class HTTPError(CCEError):
    """ HTTPError raised when HTTP request returned a error."""

    def __init__(self, reason=None):
        """
        Initialize HTTPError with `response` object and `status`.
        """
        self.reason = reason
        super(HTTPError, self).__init__(reason)


class StopCCEIteration(CCEError):
    """Exception to exit from the engine iteration."""
    pass


class CCESplitError(CCEError):
    """Exception to exit the job in Split Task"""
    pass


class QuitJobError(CCEError):
    pass
