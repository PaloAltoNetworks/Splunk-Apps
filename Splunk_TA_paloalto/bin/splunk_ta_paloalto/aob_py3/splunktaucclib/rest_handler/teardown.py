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

"""REST Manager for cleaning configuration in add-on.

It will return endpoints that failed to be cleaned.

"""


import json
import logging
from inspect import ismethod
from itertools import chain as iter_chain
from urllib.parse import quote

from splunk import admin, rest
from splunktalib.rest import splunkd_request

from . import base
from .error_ctl import RestHandlerError as RH_Err

__all__ = ["DataInputHandler", "DataInputModel"]


class TeardownHandler(base.BaseRestHandler):
    """REST Handler for Splunk Add-on configuration Teardown."""

    def __init__(self, *args, **kwargs):
        admin.MConfigHandler.__init__(self, *args, **kwargs)

        assert hasattr(self, "targets") and self.targets, RH_Err.ctl(
            1002, msgx=f"{self._getHandlerName()}.targets", shouldPrint=False
        )
        assert hasattr(self, "getArgs") and ismethod(self.getArgs), RH_Err.ctl(
            1002, msgx="%s.getArgs" % (self._getHandlerName()), shouldPrint=False
        )
        assert hasattr(self, "distinguish") and ismethod(self.distinguish), RH_Err.ctl(
            1002, msgx="%s.distinguish" % (self._getHandlerName()), shouldPrint=False
        )

        if self.requestedAction != admin.ACTION_LIST:
            RH_Err.ctl(
                1101, msgx='Only "list" action is supported', logLevel=logging.INFO
            )

    def setup(self):
        for arg in self.requiredArgs:
            self.supportedArgs.addReqArg(arg)
        for arg in self.optionalArgs:
            self.supportedArgs.addOptArg(arg)

    def getArgs(self):
        """
        Get arguments used in "distinguish" method.
        :param endpoint:
        :return:
        """
        args = {}
        for arg in iter_chain(self.requiredArgs, self.optionalArgs):
            val = self.callerArgs.data.get(arg, [""])[0]
            val = "" if val is None else val
            args[arg] = val
        return args

    def handleList(self, confInfo):
        all_errs = {}
        for ep in self.targets:
            all_errs.update(self.clean(ep))

        if all_errs:
            RH_Err.ctl(1103, msgx=json.dumps(all_errs))

    def make_uri(self, endpoint, entry=None):
        user, app = self.user_app()
        endpoint = endpoint.strip("/ ")
        entry = "" if entry is None else "/" + quote(entry.strip("/"), safe="")
        uri = "{splunkd_uri}servicesNS/{user}/{app}/{endpoint}{entry}" "".format(
            splunkd_uri=rest.makeSplunkdUri(),
            user=user,
            app=app,
            endpoint=endpoint,
            entry=entry,
        )
        return uri

    def clean(self, endpoint):
        url = self.make_uri(endpoint) + "?count=-1"
        resp, cont = splunkd_request(
            url,
            self.getSessionKey(),
            method="GET",
            data={"output_mode": "json"},
            retry=3,
        )

        if resp is None:
            return {url: "Unknown reason"}
        if resp.status != 200:
            return {url: self.convertErrMsg(cont)}

        cont = json.loads(cont)
        ents = [ent["name"] for ent in cont.get("entry", [])]
        errs = {}
        for ent in ents:
            args = self.getArgs()
            if not self.distinguish(endpoint, ent, **args):
                continue
            url_ent = self.make_uri(endpoint, entry=ent)
            resp, cont = splunkd_request(
                url_ent,
                self.getSessionKey(),
                method="DELETE",
                data={"output_mode": "json"},
                retry=3,
            )

            if resp is None:
                errs[url_ent] = "Unknown reason"
            if resp.status != 200:
                errs[url_ent] = self.convertErrMsg(cont)
        return errs

    def convertErrMsg(self, errMsg):
        err = json.loads(errMsg)
        return err["messages"][0]["text"]


class TeardownModel(base.BaseModel):
    """Base Class of Data Input Model."""

    # target endpoints to tear down a dict:
    # key ==> endpoint, value ==> needed to be filtered (boolean)
    targets = set()

    def distinguish(self, endpoint, name, **kwargs):
        """
        Determine if an item should be cleared.
        Override it if need.
        :param endpoint:
        :param name:
        :param kwargs:
        :return: True/False
        """
        return True


def ResourceHandler(model, handler=TeardownHandler):
    return type(handler.__name__, (handler, model), {})
