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

import splunktalib.common.log as stclog

_level_by_name = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.FATAL,
    "CRITICAL": logging.CRITICAL,
}


def _get_log_level(log_level, default_level=logging.INFO):
    if not log_level:
        return default_level
    if isinstance(log_level, str):
        log_level = log_level.upper()
        for k, v in _level_by_name.items():
            if k.startswith(log_level):
                return v
    if isinstance(log_level, int):
        if log_level in list(_level_by_name.values()):
            return log_level
    return default_level


def set_log_level(log_level):
    """
    Set log level.
    """
    stclog.Logs().set_level(_get_log_level(log_level))


# Global logger
logger = stclog.Logs().get_logger("ucc_lib")


def reset_logger(name):
    """
    Reset logger.
    """

    stclog.reset_logger(name)

    global logger
    logger = stclog.Logs().get_logger(name)
