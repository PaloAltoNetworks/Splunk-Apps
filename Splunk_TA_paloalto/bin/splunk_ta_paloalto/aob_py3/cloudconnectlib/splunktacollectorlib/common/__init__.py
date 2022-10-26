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
import json
import hashlib


def load_schema_file(schema_file):
    """
    Load schema file.
    """

    with open(schema_file) as f:
        ret = json.load(f)

    common = ret.get("_common_", dict())
    if common:
        for k, v in list(ret.items()):
            if k == "_common_" or not isinstance(v, dict):
                continue
            # merge common into other values
            for _k, _v in list(common.items()):
                if _k not in v:
                    v[_k] = _v
            ret[k] = v

    return ret


def md5_of_dict(data):
    """
    MD5 of dict data.
    """

    md5 = hashlib.sha256()
    if isinstance(data, dict):
        for key in sorted(data.keys()):
            md5.update(repr(key))
            md5.update(md5_of_dict(data[key]))
    elif isinstance(data, list):
        for item in sorted(data):
            md5.update(md5_of_dict(item))
    else:
        md5.update(repr(data))

    return md5.hexdigest()


class UCCException(Exception):
    """
    Dispatch engine exception.
    """

    pass

