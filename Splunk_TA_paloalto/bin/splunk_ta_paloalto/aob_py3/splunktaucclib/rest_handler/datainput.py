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

"""REST Manager for data inputs (a wrapper of data inputs).

Note: It manages inputs.conf

"""

import collections
import json
import logging
import sys
from urllib.parse import quote

from splunk import admin, rest

from . import base, util
from .error_ctl import RestHandlerError as RH_Err

__all__ = ["DataInputHandler", "DataInputModel"]


class DataInputHandler(base.BaseRestHandler):
    """A Wrapper of Splunk Data Input REST."""

    def __init__(self, *args, **kwargs):
        base.BaseRestHandler.__init__(self, *args, **kwargs)
        assert hasattr(self, "dataInputName") and self.dataInputName, RH_Err.ctl(
            1002,
            msgx=f"{self._getHandlerName()}.dataInputName",
            shouldPrint=False,
        )

        self._cred_mgmt = self.get_cred_mgmt(self.dataInputName)

    def handleCreate(self, confInfo):
        args = self.encode(self.callerArgs.data)
        args["name"] = self.callerArgs.id
        try:
            rest.simpleRequest(
                self.makeRequestURL(),
                sessionKey=self.getSessionKey(),
                postargs=args,
                method="POST",
                raiseAllErrors=True,
            )
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        return

    def handleEdit(self, confInfo):
        args = self.encode(self.callerArgs.data, setDefault=True)
        try:
            rest.simpleRequest(
                self.makeRequestURL(),
                sessionKey=self.getSessionKey(),
                postargs=args,
                method="POST",
                raiseAllErrors=True,
            )
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        return

    def handleList(self, confInfo):
        user, app = self.user_app()
        try:
            response, content = rest.simpleRequest(
                self.makeRequestURL(),
                sessionKey=self.getSessionKey(),
                method="GET",
                raiseAllErrors=True,
            )
            res = json.loads(content)
            if "entry" in res:
                for entry in res["entry"]:
                    name, ent = entry["name"], entry["content"]
                    ent[admin.EAI_ENTRY_ACL] = entry["acl"]
                    ent = self.decode(name, self.convert(ent))
                    util.makeConfItem(name, ent, confInfo, user=user, app=app)
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        return

    def handleRemove(self, confInfo):
        try:
            rest.simpleRequest(
                self.makeRequestURL(),
                sessionKey=self.getSessionKey(),
                method="DELETE",
                raiseAllErrors=True,
            )
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        self._cred_mgmt.delete(self._makeStanzaName(self.callerArgs.id))
        return

    def handleCustom(self, confInfo, **params):
        if self.customAction in ["acl"]:
            return self.handleACL(confInfo)

        if self.customAction == "disable":
            self.handleDisable(confInfo)
        elif self.customAction == "enable":
            self.handleEnable(confInfo)
        elif self.customAction == "sync":
            self.sync(confInfo, **params)
        else:
            RH_Err.ctl(-1, msgx="action=%s" % self.customAction, logLevel=logging.INFO)

    def handleDisable(self, confInfo):
        try:
            rest.simpleRequest(
                self.makeRequestURL().replace(
                    "?output_mode=json", "/disable?output_mode=json"
                ),
                sessionKey=self.getSessionKey(),
                method="POST",
                raiseAllErrors=True,
            )
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        return

    def handleEnable(self, confInfo):
        try:
            rest.simpleRequest(
                self.makeRequestURL().replace(
                    "?output_mode=json", "/enable?output_mode=json"
                ),
                sessionKey=self.getSessionKey(),
                method="POST",
                raiseAllErrors=True,
            )
        except Exception as exc:
            RH_Err.ctl(-1, msgx=exc, logLevel=logging.INFO)
        return

    def get(self, name):
        rest.simpleRequest(
            self.makeRequestURL(),
            sessionKey=self.getSessionKey(),
            method="GET",
            raiseAllErrors=True,
        )
        return

    def makeRequestURL(self):
        user, app = self.user_app()
        eid = (
            None
            if self.callerArgs.id is None
            else quote(self.callerArgs.id.encode("utf-8"), safe="")
        )
        actions = (admin.ACTION_EDIT, admin.ACTION_LIST, admin.ACTION_REMOVE)
        name = (
            (self.requestedAction in actions and self.callerArgs.id is not None)
            and ("/" + eid)
            or ""
        )
        return (
            rest.makeSplunkdUri()
            + "servicesNS/"
            + user
            + "/"
            + app
            + "/data/inputs/"
            + self.dataInputName
            + name
            + "?output_mode=json&count=-1"
        )

    def convertErrMsg(self, errMsg):
        err = json.loads(errMsg)
        return err["messages"][0]["text"]

    def convert(self, data):
        if isinstance(data, str):
            return data.encode("utf-8")
        elif isinstance(data, collections.Mapping):
            return dict(list(map(self.convert, iter(data.items()))))
        elif isinstance(data, collections.Iterable):
            return type(data)(list(map(self.convert, data)))
        else:
            return data

    def _makeStanzaName(self, name):
        return "{dataInputName}://{name}".format(
            dataInputName=self.dataInputName, name=name
        )


class DataInputModel(base.BaseModel):
    """Base Class of Data Input Model."""

    # For Splunkd data input TEST API:
    # servicesNS/<user>/<app>/data/inputs/<dataInputName>
    dataInputName = ""


def ResourceHandler(model, handler=DataInputHandler):
    return type(handler.__name__, (handler, model), {})
