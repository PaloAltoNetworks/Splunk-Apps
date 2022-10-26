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

import os.path

from .error import RestError

try:
    from splunk import admin
except:
    print("Some functions will not be available outside of a splunk hosted process")

try:
    from splunktalib.common import util
except:
    print('Python Lib for Splunk add-on "splunktalib" is required')
    raise BaseException()

__all__ = [
    "get_base_app_name",
    "remove_http_proxy_env_vars",
    "makeConfItem",
    "getBaseAppName",
]


def getBaseAppName():
    """Base App name, which this script belongs to."""
    appName = util.get_appname_from_path(__file__)
    if appName is None:
        raise Exception("Cannot get app name from file: %s" % __file__)
    return appName


def makeConfItem(name, entity, confInfo, user="nobody", app="-"):
    confItem = confInfo[name]
    for key, val in list(entity.items()):
        if key not in ("eai:attributes", "eai:userName", "eai:appName"):
            confItem[key] = val
    confItem["eai:userName"] = entity.get("eai:userName") or user
    confItem["eai:appName"] = entity.get("eai:appName") or app
    confItem.setMetadata(
        admin.EAI_ENTRY_ACL,
        entity.get(admin.EAI_ENTRY_ACL)
        or {
            "owner": user,
            "app": app,
            "global": 1,
            "can_write": 1,
            "modifiable": 1,
            "removable": 1,
            "sharing": "global",
            "perms": {"read": ["*"], "write": ["admin"]},
        },
    )
    return confItem


def get_base_app_name():
    """
    Base App name, which this script belongs to.
    """
    import __main__

    main_name = __main__.__file__
    absolute_path = os.path.normpath(main_name)
    parts = absolute_path.split(os.path.sep)
    parts.reverse()
    for key in ("apps", "slave-apps", "master-apps"):
        try:
            idx = parts.index(key)
            if parts[idx + 1] == "etc":
                return parts[idx - 1]
        except (ValueError, IndexError):
            pass
    raise RestError(status=500, message="Cannot get app name from file: %s" % main_name)


def remove_http_proxy_env_vars():
    for k in ("http_proxy", "https_proxy"):
        if k in os.environ:
            del os.environ[k]
        elif k.upper() in os.environ:
            del os.environ[k.upper()]
