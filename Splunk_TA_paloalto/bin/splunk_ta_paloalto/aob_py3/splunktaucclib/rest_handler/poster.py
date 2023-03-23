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


import re
import urllib.error
import urllib.parse
import urllib.request

import requests
from splunk import admin, rest
from splunktalib.common.util import is_true
from splunktalib.rest import code_to_msg, splunkd_request

from . import base, util
from .error_ctl import RestHandlerError as RH_Err


class PosterHandler(base.BaseRestHandler):
    """REST handler for retransmitting request to a url.
    It is designed for avoiding cross-site request in front-end.
    It accepts POST request only for safety of credential information.
    """

    def __init__(self, *args, **kwargs):
        admin.MConfigHandler.__init__(self, *args, **kwargs)

        # check required attributes
        assert hasattr(self, "modelMap") and isinstance(
            self.modelMap, dict
        ), RH_Err.ctl(
            1002, msgx=f"{self.__class__.__name__}.modelMap", shouldPrint=False
        )

        if self.requestedAction != admin.ACTION_EDIT:
            RH_Err.ctl(1101, msgx='Only "edit" supported')
        self.setModel(self.callerArgs.id)
        self.requiredArgs.add("splunk_poster_url")
        self.requiredArgs.add("splunk_poster_method")

    def setModel(self, name):
        # get model for object
        if name not in self.modelMap:
            RH_Err.ctl(404, msgx=f"object={name}")
        self.model = self.modelMap[name]

        # load attributes from model
        obj = self.model()
        attrs = {
            attr: getattr(obj, attr, None)
            for attr in dir(obj)
            if not attr.startswith("__") and attr != "endpoint"
        }
        self.__dict__.update(attrs)

    def handleEdit(self, confInfo):
        user, app = self.user_app()
        proxy_info = self.getProxyInfo(
            splunkdMgmtUri=rest.makeSplunkdUri(),
            sessionKey=self.getSessionKey(),
            user=user,
            app=app,
        )
        proxy_enabled = proxy_info.get("proxy_enabled", False)
        proxy_uri = util.get_proxy_uri(proxy_info if proxy_enabled else {})
        proxies = {"http": proxy_uri, "https": proxy_uri}
        try:
            url = self.callerArgs.data["splunk_poster_url"][0]
            for regex in self.allowedURLs:
                if re.match(regex, url):
                    break
            else:
                RH_Err.ctl(1104, msgx="Unsupported url to be posted")

            method = self.callerArgs.data["splunk_poster_method"][0]
            if method not in self.allowedMethods:
                RH_Err.ctl(1104, msgx="Unsupported method to be posted")

            payload = {
                key: val[0]
                for key, val in self.callerArgs.data.items()
                if key in self.retransmittedArgs
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }

            resp = requests.request(  # nosemgrep: python.requests.best-practice.use-raise-for-status.use-raise-for-status  # noqa: E501
                method=method,
                url=url,
                headers=headers,
                data=urllib.parse.urlencode(payload),
                timeout=120,
                proxies=proxies,
                verify=True,
            )
            content = resp.json()
            if resp.status_code not in (200, 201):
                RH_Err.ctl(resp.status_code, msgx=content)

            for key, val in content.items():
                confInfo[self.callerArgs.id][key] = val
        except Exception as exc:
            RH_Err.ctl(1104, msgx=exc)


class PosterModel(base.BaseModel):
    """Model for request retransmitting target"""

    # Argument names:
    # arguments are required. It contains 'splunk_poster_url'
    # and 'splunk_poster_method' automatically.
    requiredArgs = set()
    # arguments are optional.
    optionalArgs = set()
    # arguments will be retransmitted.
    retransmittedArgs = set()

    # A white list for URLs regex.
    # If it is empty, it will reject all request.
    allowedURLs = ()

    # A white list for HTTP methods
    allowedMethods = ()


class PosterMapping:
    """Mapping from object name to poster model."""

    # mapping object name to handler model class
    modelMap = {}

    # Endpoint for Proxy Info, like:
    # <admin>/<endpoint>/<proxy>
    proxyInfoEndpoint = None

    def getProxyInfo(self, splunkdMgmtUri, sessionKey, user, app):
        """
        Get Proxy Information on given REST endpoint.
        It should be in form (if not, override the this method):
            {
               'proxy_url': '<proxy_url>',
               'proxy_port': '<proxy_port>',
               'proxy_username': '<proxy_username>',
               'proxy_password': '<proxy_password>',
               'proxy_enabled': '<proxy_enabled>',
               'proxy_rdns': '<proxy_rdns>',
               'proxy_type': '<proxy_type>'
            }
        :return:
        """
        if not self.proxyInfoEndpoint:
            RH_Err.ctl(1104, msgx="Empty endpoint for proxy is being used")
        url = "{splunkdMgmtUri}servicesNS/{user}/{app}/{proxyInfoEndpoint}".format(
            splunkdMgmtUri=splunkdMgmtUri,
            user=user,
            app=app,
            proxyInfoEndpoint=self.proxyInfoEndpoint,
        )
        data = {"output_mode": "json", "--get-clear-credential--": "1"}
        resp = splunkd_request(url, sessionKey, data=data, retry=3)
        if resp is None or resp.status_code != 200:
            RH_Err.ctl(1104, msgx=f"failed to load proxy info. {code_to_msg(resp)}")

        try:
            proxy_info = resp.json()["entry"][0]["content"]
        except IndexError | KeyError:
            proxy_info = {}

        return {
            "proxy_enabled": is_true(proxy_info.get("proxy_enabled", "false")),
            "proxy_url": proxy_info.get("proxy_url", ""),
            "proxy_port": proxy_info.get("proxy_port", ""),
            "proxy_username": proxy_info.get("proxy_username", ""),
            "proxy_password": proxy_info.get("proxy_password", ""),
            "proxy_rdns": proxy_info.get("proxy_rdns", "false"),
            "proxy_type": proxy_info.get("proxy_type", "http"),
        }


def ResourceHandler(poster_mapping, handler=PosterHandler):
    return type(handler.__name__, (handler, poster_mapping), {})
