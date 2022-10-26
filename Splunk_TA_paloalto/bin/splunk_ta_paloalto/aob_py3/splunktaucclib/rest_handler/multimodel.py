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

"""REST handler for multiple models with different structure in one *.conf.
It assumes that there are enumerable objects in every model,
and they will be listed in ``modelMap`` in advance, that means
it dose not allow to create object but update it.

It will return fields with default values, if the object never created
via REST or *.conf directly.

This handler is for some global settings like proxy, logging, etc.
"""


import logging

import splunk
from splunk import ResourceNotFound

from . import base
from .cred_mgmt import CredMgmt
from .error_ctl import RestHandlerError as RH_Err

__all__ = ["MultiModelRestHandler", "MultiModel", "ResourceHandler"]


class MultiModelRestHandler(base.BaseRestHandler):
    """Rest handler for multiple models with different fields,
    and different validation.
    """

    def __init__(self, *args, **kwargs):
        splunk.admin.MConfigHandler.__init__(self, *args, **kwargs)
        self._log_request()

        # check required attributes
        assert hasattr(self, "endpoint"), RH_Err.ctl(
            1002,
            msgx="%s.endpoint" % self.__class__.__name__,
            shouldPrint=False,
            shouldRaise=False,
        )
        assert hasattr(self, "modelMap") and isinstance(
            self.modelMap, dict
        ), RH_Err.ctl(
            1002,
            msgx="%s.modelMap" % self.__class__.__name__,
            shouldPrint=False,
            shouldRaise=False,
        )

        # Check custom actions
        self.check_caps()
        if self.customAction == "_sync":
            self.exist4sync = True

        # set model for requested object
        self.model = None
        if self.callerArgs.id:
            self.setModel(self.callerArgs.id)

    def setModel(self, name):
        """Get data model for specified object."""
        # get model for object
        if name not in self.modelMap:
            RH_Err.ctl(
                404,
                msgx=f"object={name}",
            )
        self.model = self.modelMap[name]

        # load attributes from model
        obj = self.model()
        attrs = {
            attr: getattr(obj, attr, None)
            for attr in dir(obj)
            if not attr.startswith("__")
            and attr not in ("endpoint", "rest_prefix", "cap4endpoint", "cap4get_cred")
        }
        self.__dict__.update(attrs)

        # credential fields
        self.encryptedArgs = {
            (self.keyMap.get(arg) or arg) for arg in self.encryptedArgs
        }
        user, app = self.user_app()
        self._cred_mgmt = CredMgmt(
            sessionKey=self.getSessionKey(),
            user=user,
            app=app,
            endpoint=self.endpoint,
            encryptedArgs=self.encryptedArgs,
        )
        return

    def handleRemove(self, confInfo):
        try:
            self.delete(self.callerArgs.id)
        except ResourceNotFound as exc:
            if self.callerArgs.id not in self.modelMap:
                RH_Err.ctl(-1, exc, logLevel=logging.INFO)
        except Exception as exc:
            RH_Err.ctl(-1, exc, logLevel=logging.INFO)
        self._cred_mgmt.delete(self._makeStanzaName(self.callerArgs.id))

    def all(self):
        return {name: self.get(name) for name in self.modelMap}

    def get(self, name):
        # set model attribute for normalize response data
        self.setModel(name)
        try:
            return base.BaseRestHandler.get(self, name)
        except splunk.ResourceNotFound:
            return self.defaultVals or {}

    def update(self, name, **params):
        user, app = self.user_app()
        try:
            ent = splunk.entity.getEntity(
                self.endpoint,
                name,
                namespace=app,
                owner=user,
                sessionKey=self.getSessionKey(),
            )

            for arg, val in list(params.items()):
                ent[arg] = val
            splunk.entity.setEntity(ent, sessionKey=self.getSessionKey())
        except splunk.ResourceNotFound:
            try:
                args = self.encode(self.callerArgs.data)
                self.create(self.callerArgs.id, **args)
            except Exception as exc:
                RH_Err.ctl(-1, exc, logLevel=logging.INFO)
        except Exception as exc:
            RH_Err.ctl(-1, exc, logLevel=logging.INFO)

    def _getHandlerName(self):
        return f"{self.__class__.__name__}.{self.model.__name__}"


class MultiModel:
    """Mapping from object name to model, which means stanzas with
    different structure will be stored in same endpoint.
    """

    # REST prefix. Default is lower-case app name.
    # Change it if needed.
    rest_prefix = base.APP_NAME

    # Endpoint, specifies the conf name, in form:
    # configs/conf-<conf_file_name>
    endpoint = ""

    # mapping object name to handler model class
    modelMap = {}

    # Required capabilities for this REST Endpoint.
    # Empty string means no need to check capability.
    # It will add ``rest_prefix`` automatically.
    #   cap4endpoint: basic capability for this endpoint.
    #   cap4get_cred: capability to get credential info.
    cap4endpoint = "endpoint"
    cap4get_cred = "get_credential"


def ResourceHandler(multimodel, handler=MultiModelRestHandler):
    return type(handler.__name__, (handler, multimodel), {})
