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

"""Error control
"""


import logging
import re
import sys
import traceback

from splunk import RESTException

import splunktaucclib.common.log as stulog

__all__ = ["RestHandlerError", "ERROR_MAPPING"]


# Errors mapping for add-on.
# Edit it when you need to add new error type.
ERROR_MAPPING = {
    # splunkd internal error, occurred while calling splunkd REST API.
    400: "Bad Request",
    401: "Client is not authenticated",
    402: "Current license does not allow the requested action",
    403: "Unauthorized client for the requested action",
    404: "Resource/Endpoint requested dose not exist",
    409: "Conflict occurred due to existing object with the same name",
    500: "Splunkd internal error",
    # Rest handler predefined error in add-on.
    1000: "An Add-on Internal ERROR Occurred",
    1001: "Fatal Error",
    1002: "Some mandatory attributes are missing or unusable for the handler",
    1020: "Fail to encrypt credential information",
    1021: "Fail to decrypt the encrypted credential information",
    1022: "Fail to delete the encrypted credential information",
    1100: "Unsupported value in request arguments",
    1101: "Unsupported action on the requested endpoint",
    1102: "Failed to check object for _sync action",
    1103: "Failed to teardown configurations",
    1104: "Poster REST handler error",
}


class RestHandlerError:
    """Control Error in Splunk Add-on REST API.
    code-message mapping for errors:
        code < 1000: splunkd internal error, occurred while
            calling splunkd REST API,
        code >= 1000: Rest handler predefined error in add-on,
    """

    def __init__(self, code, msgx=""):
        if code == -1:
            self._conv(msgx)
        else:
            self._code = code
            self._msgx = msgx
            self._msg = RestHandlerError.map(code)

    def __str__(self):
        msgx = (self._msgx and self._msgx != self._msg) and " - %s" % self._msgx or ""
        return f"REST ERROR[{self._code}]: {self._msg}{msgx}"

    def _conv(self, exc):
        """Convert a Exception form 'splunk.rest.simpleRequest'"""
        if isinstance(exc, RESTException):
            self._code = exc.statusCode

            try:
                self._msg = RestHandlerError.map(self._code)
            except:
                self._msg = exc.get_message_text().strip()

            msgx = exc.get_extended_message_text().strip()
            if self._msg == msgx:
                self._msg = "Undefined Error"
            try:
                pattern = r"In handler \'\S+\': (?P<msgx>.*$)"
                m = re.match(pattern, msgx)
                groupDict = m.groupdict()
                self._msgx = groupDict["msgx"]
            except:
                self._msgx = msgx
        else:
            self._code = 500
            self._msg = RestHandlerError.map(self._code)
            self._msgx = str(exc)

    @staticmethod
    def map(code):
        """Map error code to message. Raise an exception
            if the code dose not exist.
        :param code: error code
        :returns: error message for the input code
        """
        msg = ERROR_MAPPING.get(code)
        assert msg, "Invalid error code is being used - code=%s" % code
        return msg

    @staticmethod
    def ctl(code, msgx="", logLevel=logging.ERROR, shouldPrint=True, shouldRaise=True):
        """Control error, including printing out the error message,
        logging it and raising an exception (BaseException).

        :param code: error code (it should be -1
            if 'msgx' is an splunkd internal error)
        :param msgx: extended message/detail, which will
            make it more clear (it is an exception of
            splunkd internal error if code=-1)
        :param logLevel: logging level (generally, it should be `
            `ERROR`` for Add-on internal error/bug,
            ``INFO`` for client request error)
        :param shouldPrint: is it required to print error info
            (the printed content will be shown to user)
        :param shouldRaise: is it required to raise an exception
            (the process will be terminated
            if an exception raised)
        :return: error content

        Some Use Cases:
        1. for splunkd internal exception/error (exc):
            ``RestHandlerError.ctl(code=-1, msgx=exc, logLevel=logging.INFO)``
        2. for bug in user-defined Rest handler in add-on:
            ``assert 'expression', \
            RestHandlerError.ctl(code=1000, msgx='some detail...',
                shouldPrint=False, shouldRaise=False)``
        3. for client request error:
            RestHandlerError.ctl(code=1100, msgx='some detail...',
            logLevel=logging.INFO)
        """
        err = RestHandlerError(code, msgx=msgx)
        tb = (
            "\r\n" + ("".join(traceback.format_stack()))
            if logLevel >= logging.ERROR or isinstance(msgx, Exception)
            else ""
        )

        stulog.logger.log(logLevel, f"{err}{tb}", exc_info=1)
        if shouldPrint:
            sys.stdout.write(str(err))
        if shouldRaise:
            raise BaseException(err)
        return err
