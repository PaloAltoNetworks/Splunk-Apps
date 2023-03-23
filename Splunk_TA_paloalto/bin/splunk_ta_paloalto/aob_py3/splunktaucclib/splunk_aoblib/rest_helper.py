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

import requests


class TARestHelper:
    def __init__(self, logger=None):
        self.logger = logger
        self.http_session = None
        self.requests_proxy = None

    def _init_request_session(self, proxy_uri=None):
        self.http_session = requests.Session()
        self.http_session.mount("http://", requests.adapters.HTTPAdapter(max_retries=3))
        self.http_session.mount(
            "https://", requests.adapters.HTTPAdapter(max_retries=3)
        )
        if proxy_uri:
            self.requests_proxy = {"http": proxy_uri, "https": proxy_uri}

    def send_http_request(
        self,
        url,
        method,
        parameters=None,
        payload=None,
        headers=None,
        cookies=None,
        verify=True,
        cert=None,
        timeout=None,
        proxy_uri=None,
    ):
        if self.http_session is None:
            self._init_request_session(proxy_uri)
        requests_args = {"timeout": (10.0, 5.0), "verify": verify}
        if parameters:
            requests_args["params"] = parameters
        if payload:
            if isinstance(payload, (dict, list)):
                requests_args["json"] = payload
            else:
                requests_args["data"] = str(payload)
        if headers:
            requests_args["headers"] = headers
        if cookies:
            requests_args["cookies"] = cookies
        if cert:
            requests_args["cert"] = cert
        if timeout is not None:
            requests_args["timeout"] = timeout
        if self.requests_proxy:
            requests_args["proxies"] = self.requests_proxy
        return self.http_session.request(method, url, **requests_args)
