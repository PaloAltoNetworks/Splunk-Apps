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

    resp, content = rest.splunkd_request(
        uri, session_key, method, data=payload, retry=3
    )
    if resp is None and content is None:
        return None

    if resp.status >= 200 and resp.status <= 204:
        return content
    else:
        msg = "{}, status={}, reason={}, detail={}".format(
            err_msg,
            resp.status,
            resp.reason,
            content.decode("utf-8"),
        )

        if not (method == "GET" and resp.status == 404):
            log.logger.error(msg)

        if resp.status == 404:
            raise ConfNotExistsException(msg)
        if resp.status == 409:
            raise ConfExistsException(msg)
        else:
            if content and "already exists" in content:
                raise ConfExistsException(msg)
            raise ConfRequestException(msg)
