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
import logging
from splunktalib.common import log as stclog
import six


def set_log_level(log_level):
    """
    Set log level.
    """

    if isinstance(log_level, six.string_types):
        if log_level.upper() == "DEBUG":
            stclog.Logs().set_level(logging.DEBUG)
        elif log_level.upper() == "INFO":
            stclog.Logs().set_level(logging.INFO)
        elif log_level.upper() == "WARN":
            stclog.Logs().set_level(logging.WARN)
        elif log_level.upper() == "ERROR":
            stclog.Logs().set_level(logging.ERROR)
        elif log_level.upper() == "WARNING":
            stclog.Logs().set_level(logging.WARNING)
        elif log_level.upper() == "CRITICAL":
            stclog.Logs().set_level(logging.CRITICAL)
        else:
            stclog.Logs().set_level(logging.INFO)
    elif isinstance(log_level, int):
        if log_level in [logging.DEBUG, logging.INFO, logging.ERROR,
                         logging.WARN, logging.WARNING, logging.CRITICAL]:
            stclog.Logs().set_level(log_level)
        else:
            stclog.Logs().set_level(logging.INFO)
    else:
        stclog.Logs().set_level(logging.INFO)


# Global logger
logger = stclog.Logs().get_logger("cloud_connect_engine")


def reset_logger(name):
    """
    Reset logger.
    """

    stclog.reset_logger(name)

    global logger
    logger = stclog.Logs().get_logger(name)


