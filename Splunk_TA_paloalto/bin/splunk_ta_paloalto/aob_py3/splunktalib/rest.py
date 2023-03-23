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
import urllib.parse
from traceback import format_exc
from typing import Optional

import requests

import splunktalib.common.log as log


def splunkd_request(
    splunkd_uri,
    session_key,
    method="GET",
    headers=None,
    data=None,
    timeout=30,
    retry=1,
    verify=False,
) -> Optional[requests.Response]:

    headers = headers if headers is not None else {}
    headers["Authorization"] = "Splunk {}".format(session_key)
    content_type = headers.get("Content-Type")
    if not content_type:
        content_type = headers.get("content-type")

    if not content_type:
        content_type = "application/x-www-form-urlencoded"
        headers["Content-Type"] = content_type

    if data is not None:
        if content_type == "application/json":
            data = json.dumps(data)
        else:
            data = urllib.parse.urlencode(data)

    msg_temp = "Failed to send rest request=%s, errcode=%s, reason=%s"
    resp = None
    for _ in range(retry):
        try:
            resp = requests.request(
                method=method,
                url=splunkd_uri,
                data=data,
                headers=headers,
                timeout=timeout,
                verify=verify,
            )
        except Exception:
            log.logger.error(msg_temp, splunkd_uri, "unknown", format_exc())
        else:
            if resp.status_code not in (200, 201):
                if not (method == "GET" and resp.status_code == 404):
                    log.logger.debug(
                        msg_temp, splunkd_uri, resp.status_code, code_to_msg(resp)
                    )
            else:
                return resp
    else:
        return resp


def code_to_msg(response: requests.Response):
    code_msg_tbl = {
        400: "Request error. reason={}".format(response.text),
        401: "Authentication failure, invalid access credentials.",
        402: "In-use license disables this feature.",
        403: "Insufficient permission.",
        404: "Requested endpoint does not exist.",
        409: "Invalid operation for this endpoint. reason={}".format(response.text),
        500: "Unspecified internal server error. reason={}".format(response.text),
        503: (
            "Feature is disabled in the configuration file. "
            "reason={}".format(response.text)
        ),
    }

    return code_msg_tbl.get(response.status_code, response.text)
