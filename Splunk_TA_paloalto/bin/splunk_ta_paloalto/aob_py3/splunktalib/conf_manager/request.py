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

import splunktalib.rest as rest
from splunktalib.common import log


class ConfRequestException(Exception):
    pass


class ConfNotExistsException(ConfRequestException):
    pass


class ConfExistsException(ConfRequestException):
    pass


def content_request(uri, session_key, method, payload, err_msg):
    """
    :return: response content if successful otherwise raise
    ConfRequestException
    """

    resp = rest.splunkd_request(uri, session_key, method, data=payload, retry=3)
    if resp is None:
        return None

    if resp.status_code >= 200 and resp.status_code <= 204:
        return resp.text
    else:
        msg = "{}, status={}, reason={}, detail={}".format(
            err_msg,
            resp.status_code,
            resp.reason,
            resp.text,
        )

        if not (method == "GET" and resp.status_code == 404):
            log.logger.error(msg)

        if resp.status_code == 404:
            raise ConfNotExistsException(msg)
        if resp.status_code == 409:
            raise ConfExistsException(msg)
        else:
            if resp.text and "already exists" in resp.text:
                raise ConfExistsException(msg)
            raise ConfRequestException(msg)
