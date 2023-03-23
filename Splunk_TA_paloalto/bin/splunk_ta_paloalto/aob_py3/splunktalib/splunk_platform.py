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

import os
import warnings

from splunktalib.common import util as scu


def make_splunkhome_path(parts):
    """
    create a path string by the several parts of the path
    """
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    relpath = os.path.normpath(os.path.join(*parts))

    basepath = os.environ["SPLUNK_HOME"]  # Assume SPLUNK_HOME env has been set

    fullpath = os.path.normpath(os.path.join(basepath, relpath))

    # Check that we haven't escaped from intended parent directories.
    if os.path.relpath(fullpath, basepath)[0:2] == "..":
        raise ValueError(
            'Illegal escape from parent directory "{}": {}'.format(basepath, fullpath)
        )

    return fullpath


def get_splunk_bin():
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    if os.name == "nt":
        splunk_bin = "splunk.exe"
    else:
        splunk_bin = "splunk"
    return make_splunkhome_path(("bin", splunk_bin))


def get_appname_from_path(absolute_path):
    return scu.get_appname_from_path(absolute_path)
