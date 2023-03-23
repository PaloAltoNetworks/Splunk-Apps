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
import time
import traceback
import requests

import munch
from requests import PreparedRequest, Session, utils
from solnlib.utils import is_true

from cloudconnectlib.common import util
from cloudconnectlib.common.log import get_cc_logger
from cloudconnectlib.core import defaults
from cloudconnectlib.core.exceptions import HTTPError

_logger = get_cc_logger()


class HTTPResponse:
    """
    HTTPResponse class wraps response of HTTP request for later use.
    """

    def __init__(self, response, content):
        """Construct a HTTPResponse from response and content returned
        with requests.Session() request"""
        self._status_code = response.status_code
        self._header = response
        self._body = self._decode_content(response.headers, content)

    @staticmethod
    def _decode_content(response, content):
        if not content:
            return ""

        charset = utils.get_encoding_from_headers(response)

        if charset is None:
            charset = defaults.charset
            _logger.info(
                "Unable to find charset in response headers," ' set it to default "%s"',
                charset,
            )

        _logger.info("Decoding response content with charset=%s", charset)

        try:
            return content.decode(charset, errors="replace")
        except Exception as ex:
            _logger.warning(
                "Failure decoding response content with charset=%s,"
                " decode it with utf-8: %s",
                charset,
                ex,
            )

        return content.decode("utf-8", errors="replace")

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        """
        Return response body as a `string`.
        :return: A `string`
        """
        return self._body

    @property
    def status_code(self):
        """
        Return response status code.
        :return: A `integer`
        """
        return self._status_code


def _make_prepare_url_func():
    """Expose prepare_url in `PreparedRequest`"""
    pr = PreparedRequest()

    def prepare_url(url, params=None):
        """Prepare the given HTTP URL with ability provided in requests lib.
        For some illegal characters in URL or parameters like space(' ') will
        be escaped to make sure we can request the correct URL."""
        pr.prepare_url(url, params=params)
        return pr.url

    return prepare_url


def get_proxy_info(proxy_config: dict) -> dict:
    """
    @proxy_config: dict like object of the format -
    {
        "proxy_url": my-proxy.server.com,
        "proxy_port": 0000,
        "proxy_username": username,
        "proxy_password": password,
        "proxy_type": http or sock5,
        "proxy_rdns": 0 or 1,
    }
    """
    proxy_info = {}

    if not proxy_config or not is_true(proxy_config.get("proxy_enabled")):
        _logger.info("Proxy is not enabled")
        return {}

    proxy_type = proxy_config.get("proxy_type", "").lower()
    if proxy_type not in ("http", "socks5"):
        proxy_type = "http"
        _logger.info('Proxy type not found, set to "HTTP"')

    if is_true(proxy_config.get("proxy_rdns")) and proxy_type == "socks5":
        proxy_type = "socks5h"

    url = proxy_config.get("proxy_url")
    port = proxy_config.get("proxy_port")

    if url or port:
        if not url:
            raise ValueError('Proxy "url" must not be empty')
        if not util.is_valid_port(port):
            raise ValueError('Proxy "port" must be in range [1,65535]: %s' % port)

    proxy_info["http"] = f"{proxy_type}://{url}:{int(port)}"
    user = proxy_config.get("proxy_username")
    password = proxy_config.get("proxy_password")

    if all((user, password)):
        proxy_info["http"] = f"{proxy_type}://{user}:{password}@{url}:{int(port)}"
    else:
        _logger.info("Proxy has no credentials found")

    proxy_info["https"] = proxy_info["http"]
    return proxy_info


def standardize_proxy_config(proxy_config):
    """
    This function is used to standardize the proxy information structure to
    get it evaluated through `get_proxy_info` function
    """

    if not isinstance(proxy_config, dict):
        raise ValueError(
            "Received unexpected format of proxy configuration. "
            "Expected format: object, Actual format: {}".format(type(proxy_config))
        )

    standard_proxy_config = {
        "proxy_enabled": proxy_config.get("enabled", proxy_config.get("proxy_enabled")),
        "proxy_username": proxy_config.get(
            "username", proxy_config.get("proxy_username")
        ),
        "proxy_password": proxy_config.get(
            "password", proxy_config.get("proxy_password")
        ),
        "proxy_url": proxy_config.get("host", proxy_config.get("proxy_url")),
        "proxy_type": proxy_config.get("type", proxy_config.get("proxy_type")),
        "proxy_port": proxy_config.get("port", proxy_config.get("proxy_port")),
        "proxy_rdns": proxy_config.get("rdns", proxy_config.get("proxy_rdns")),
    }

    return standard_proxy_config


class HttpClient:
    def __init__(self, proxy_info=None, verify=True):
        """
        Constructs a `HTTPRequest` with a optional proxy setting.
        :param proxy_info: a dictionary of proxy details. It could directly match the input signature
            of `requests` library, otherwise will be standardized and converted to match the input signature.
        :param verify: same as the `verify` parameter of requests.request() method
        """
        self._connection = None
        self.requests_verify = verify

        if proxy_info:
            if isinstance(proxy_info, munch.Munch):
                proxy_info = dict(proxy_info)

            if all((len(proxy_info) == 2, "http" in proxy_info, "https" in proxy_info)):
                # when `proxy_info` already matches the input signature of `requests` library's proxy dict
                self._proxy_info = proxy_info
            else:
                # Updating the proxy_info object to make it compatible for getting evaluated
                # through `get_proxy_info` function
                proxy_info = standardize_proxy_config(proxy_info)
                self._proxy_info = get_proxy_info(proxy_info)
        else:
            self._proxy_info = proxy_info
        self._url_preparer = PreparedRequest()

    def _send_internal(self, uri, method, headers=None, body=None):
        """Do send request to target URL, validate SSL cert by default and return the response."""
        return self._connection.request(
            url=uri,
            data=body,
            method=method,
            headers=headers,
            timeout=defaults.timeout,
            verify=self.requests_verify,
        )

    def _retry_send_request_if_needed(self, uri, method="GET", headers=None, body=None):
        """Invokes request and auto retry with an exponential backoff
        if the response status is configured in defaults.retry_statuses."""
        retries = max(defaults.retries, 0)
        _logger.info("Invoking request to [%s] using [%s] method", uri, method)
        for i in range(retries + 1):
            try:
                resp = self._send_internal(
                    uri=uri, body=body, method=method, headers=headers
                )
                content = resp.content
                response = resp
            except requests.exceptions.SSLError as err:
                _logger.error(
                    "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verification failed. "
                    "The certificate of the https server [%s] is not trusted, "
                    "You may need to check the certificate and "
                    "refer to the documentation and add it to the trust list. %s",
                    uri,
                    traceback.format_exc(),
                )
                raise HTTPError(f"HTTP Error {err}") from err
            except Exception as err:
                _logger.exception(
                    "Could not send request url=%s method=%s", uri, method
                )
                raise HTTPError(f"HTTP Error {err}") from err

            status = resp.status_code

            if self._is_need_retry(status, i, retries):
                delay = 2**i
                _logger.warning(
                    "The response status=%s of request which url=%s and"
                    " method=%s. Retry after %s seconds.",
                    status,
                    uri,
                    method,
                    delay,
                )
                time.sleep(delay)
                continue

            return HTTPResponse(response, content)

    def _prepare_url(self, url, params=None):
        self._url_preparer.prepare_url(url, params)
        return self._url_preparer.url

    def _initialize_connection(self):
        if self._proxy_info:
            _logger.info("Proxy is enabled for http connection.")
        else:
            _logger.info("Proxy is not enabled for http connection.")
        self._connection = self._build_http_connection(self._proxy_info)

    def send(self, request):
        if not request:
            raise ValueError("The request is none")
        if request.body and not isinstance(request.body, str):
            raise TypeError(f"Invalid request body type: {request.body}")

        if self._connection is None:
            self._initialize_connection()

        try:
            url = self._prepare_url(request.url)
        except Exception:
            _logger.warning(
                "Failed to encode url=%s: %s", request.url, traceback.format_exc()
            )
            url = request.url

        return self._retry_send_request_if_needed(
            url, request.method, request.headers, request.body
        )

    @staticmethod
    def _build_http_connection(
        proxy_info=None,
        disable_ssl_cert_validation=defaults.disable_ssl_cert_validation,
    ):
        """
        Creates a `request.Session()` object, sets the verify
        and proxy_info parameter and returns this object
        """
        s = Session()
        s.verify = not disable_ssl_cert_validation
        s.proxies = proxy_info or {}
        return s

    @staticmethod
    def _is_need_retry(status, retried, maximum_retries):
        return retried < maximum_retries and status in defaults.retry_statuses
