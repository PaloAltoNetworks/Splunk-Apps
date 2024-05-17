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

from solnlib import log


def set_log_level(log_level):
    """
    Set log level.
    """

    if isinstance(log_level, str):
        if log_level.upper() == "DEBUG":
            log.Logs().set_level(logging.DEBUG)
        elif log_level.upper() == "INFO":
            log.Logs().set_level(logging.INFO)
        elif log_level.upper() == "WARN":
            log.Logs().set_level(logging.WARN)
        elif log_level.upper() == "ERROR":
            log.Logs().set_level(logging.ERROR)
        elif log_level.upper() == "WARNING":
            log.Logs().set_level(logging.WARNING)
        elif log_level.upper() == "CRITICAL":
            log.Logs().set_level(logging.CRITICAL)
        else:
            log.Logs().set_level(logging.INFO)
    elif isinstance(log_level, int):
        if log_level in [
            logging.DEBUG,
            logging.INFO,
            logging.ERROR,
            logging.WARN,
            logging.WARNING,
            logging.CRITICAL,
        ]:
            log.Logs().set_level(log_level)
        else:
            log.Logs().set_level(logging.INFO)
    else:
        log.Logs().set_level(logging.INFO)


# Global logger
logger = log.Logs().get_logger("cloud_connect_engine")


def reset_logger(name):
    """
    Reset logger.
    """

    global logger
    logger = log.Logs().get_logger(name)
