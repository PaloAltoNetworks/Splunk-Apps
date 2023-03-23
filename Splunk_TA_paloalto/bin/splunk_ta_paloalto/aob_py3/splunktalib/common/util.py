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
Copyright (C) 2005-2019 Splunk Inc. All Rights Reserved.
"""

import datetime
import gc
import os
import os.path as op
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings


def handle_tear_down_signals(callback):
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    import signal

    signal.signal(signal.SIGTERM, callback)
    signal.signal(signal.SIGINT, callback)

    if os.name == "nt":
        signal.signal(signal.SIGBREAK, callback)


def datetime_to_seconds(dt):
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    epoch_time = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch_time).total_seconds()


def is_true(val):
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def is_false(val):
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    value = str(val).strip().upper()
    if value in ("0", "FALSE", "F", "N", "NO", "NONE", ""):
        return True
    return False


def remove_http_proxy_env_vars():
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    for k in ("http_proxy", "https_proxy"):
        if k in os.environ:
            del os.environ[k]
        elif k.upper() in os.environ:
            del os.environ[k.upper()]


def get_appname_from_path(absolute_path):
    absolute_path = op.normpath(absolute_path)
    parts = absolute_path.split(os.path.sep)
    parts.reverse()
    for key in ("apps", "slave-apps", "master-apps"):
        try:
            idx = parts.index(key)
        except ValueError:
            continue
        else:
            try:
                if parts[idx + 1] == "etc":
                    return parts[idx - 1]
            except IndexError:
                pass
            continue
    return "-"


def escape_cdata(data):
    data = data.encode("utf-8", errors="xmlcharrefreplace").decode("utf-8")
    data = data.replace("]]>", "]]&gt;")
    if data.endswith("]"):
        data = data[:-1] + "%5D"
    return data


def extract_datainput_name(stanza_name):
    """
    stansa_name: string like aws_s3://my_s3_data_input
    """

    sep = "://"
    try:
        idx = stanza_name.index(sep)
    except ValueError:
        return stanza_name

    return stanza_name[idx + len(sep) :]


def disable_stdout_buffer():
    os.environ["PYTHONUNBUFFERED"] = "1"
    sys.stdout = os.fdopen(sys.stdout.fileno(), "wb", 0)
    gc.garbage.append(sys.stdout)


def format_stanza_name(name):
    return urllib.parse.quote(name.encode("utf-8"), "")
