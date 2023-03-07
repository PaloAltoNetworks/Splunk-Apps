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

"""
Error Handling.
"""


__all__ = ["STATUS_CODES", "RestError"]


# HTTP status codes
STATUS_CODES = {
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    411: "Length Required",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


class RestError(Exception):
    """
    REST Error.
    """

    def __init__(self, status, message):
        self.status = status
        self.reason = STATUS_CODES.get(
            status,
            "Unknown Error",
        )
        self.message = message
        err_msg = "REST Error [{status}]: {reason} -- {message}".format(
            status=self.status,
            reason=self.reason,
            message=self.message,
        )
        super().__init__(err_msg)
