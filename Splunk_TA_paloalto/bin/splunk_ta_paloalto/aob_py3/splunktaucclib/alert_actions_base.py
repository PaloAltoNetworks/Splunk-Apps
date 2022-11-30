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

import csv
import gzip
import logging
import sys

from solnlib import log

from splunktaucclib.cim_actions import ModularAction
from splunktaucclib.splunk_aoblib.rest_helper import TARestHelper
from splunktaucclib.splunk_aoblib.setup_util import Setup_Util

try:
    from splunk.clilib.bundle_paths import make_splunkhome_path
except ImportError:
    from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path

sys.path.insert(0, make_splunkhome_path(["etc", "apps", "Splunk_SA_CIM", "lib"]))


class ModularAlertBase(ModularAction):
    def __init__(self, ta_name, alert_name):
        self._alert_name = alert_name
        self._logger_name = alert_name + "_modalert"
        self._logger = log.Logs().get_logger(self._logger_name)
        super().__init__(sys.stdin.read(), self._logger, alert_name)
        self.setup_util_module = None
        self.setup_util = None
        self.result_handle = None
        self.ta_name = ta_name
        self.splunk_uri = self.settings.get("server_uri")
        self.setup_util = Setup_Util(self.splunk_uri, self.session_key, self._logger)

        self.rest_helper = TARestHelper(self._logger)

    def log_error(self, msg):
        self.message(msg, "failure", level=logging.ERROR)

    def log_info(self, msg):
        self.message(msg, "success", level=logging.INFO)

    def log_debug(self, msg):
        self.message(msg, None, level=logging.DEBUG)

    def log_warn(self, msg):
        self.message(msg, None, level=logging.WARN)

    def set_log_level(self, level):
        self._logger.setLevel(level)

    def get_param(self, param_name):
        return self.configuration.get(param_name)

    def get_global_setting(self, var_name):
        return self.setup_util.get_customized_setting(var_name)

    def get_user_credential(self, username):
        """
        if the username exists, return
        {
            "username": username,
            "password": credential
        }
        """
        return self.setup_util.get_credential_by_username(username)

    def get_user_credential_by_account_id(self, account_id):
        """
        if the account_id exists, return
        {
            "username": username,
            "password": credential
        }
        """
        return self.setup_util.get_credential_by_id(account_id)

    @property
    def log_level(self):
        return self.get_log_level()

    @property
    def proxy(self):
        return self.get_proxy()

    def get_log_level(self):
        return self.setup_util.get_log_level()

    def get_proxy(self):
        """if the proxy setting is set. return a dict like
        {
        proxy_url: ... ,
        proxy_port: ... ,
        proxy_username: ... ,
        proxy_password: ... ,
        proxy_type: ... ,
        proxy_rdns: ...
        }
        """
        return self.setup_util.get_proxy_settings()

    def _get_proxy_uri(self):
        uri = None
        proxy = self.get_proxy()
        if proxy and proxy.get("proxy_url") and proxy.get("proxy_type"):
            uri = proxy["proxy_url"]
            if proxy.get("proxy_port"):
                uri = "{}:{}".format(uri, proxy.get("proxy_port"))
            if proxy.get("proxy_username") and proxy.get("proxy_password"):
                uri = "{}://{}:{}@{}/".format(
                    proxy["proxy_type"],
                    proxy["proxy_username"],
                    proxy["proxy_password"],
                    uri,
                )
            else:
                uri = "{}://{}".format(proxy["proxy_type"], uri)
        return uri

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
        use_proxy=True,
    ):
        return self.rest_helper.send_http_request(
            url=url,
            method=method,
            parameters=parameters,
            payload=payload,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            timeout=timeout,
            proxy_uri=self._get_proxy_uri() if use_proxy else None,
        )

    def build_http_connection(self, config, timeout=120, disable_ssl_validation=False):
        from httplib2 import Http, ProxyInfo, socks

        """
        :config: dict like, proxy and account information are in the following
                format {
                    "username": xx,
                    "password": yy,
                    "proxy_url": zz,
                    "proxy_port": aa,
                    "proxy_username": bb,
                    "proxy_password": cc,
                    "proxy_type": http,http_no_tunnel,sock4,sock5,
                    "proxy_rdns": 0 or 1,
                }
        :return: Http2.Http object
        """
        if not config:
            config = {}

        proxy_type_to_code = {
            "http": socks.PROXY_TYPE_HTTP,
            "http_no_tunnel": socks.PROXY_TYPE_HTTP_NO_TUNNEL,
            "socks4": socks.PROXY_TYPE_SOCKS4,
            "socks5": socks.PROXY_TYPE_SOCKS5,
        }
        if config.get("proxy_type") in proxy_type_to_code:
            proxy_type = proxy_type_to_code[config["proxy_type"]]
        else:
            proxy_type = socks.PROXY_TYPE_HTTP

        rdns = config.get("proxy_rdns")

        proxy_info = None
        if config.get("proxy_url") and config.get("proxy_port"):
            if config.get("proxy_username") and config.get("proxy_password"):
                proxy_info = ProxyInfo(
                    proxy_type=proxy_type,
                    proxy_host=config["proxy_url"],
                    proxy_port=int(config["proxy_port"]),
                    proxy_user=config["proxy_username"],
                    proxy_pass=config["proxy_password"],
                    proxy_rdns=rdns,
                )
            else:
                proxy_info = ProxyInfo(
                    proxy_type=proxy_type,
                    proxy_host=config["proxy_url"],
                    proxy_port=int(config["proxy_port"]),
                    proxy_rdns=rdns,
                )
        if proxy_info:
            http = Http(
                proxy_info=proxy_info,
                timeout=timeout,
                disable_ssl_certificate_validation=disable_ssl_validation,
            )
        else:
            http = Http(
                timeout=timeout,
                disable_ssl_certificate_validation=disable_ssl_validation,
            )

        if config.get("username") and config.get("password"):
            http.add_credentials(config["username"], config["password"])
        return http

    def process_event(self, *args, **kwargs):
        raise NotImplemented()

    def pre_handle(self, num, result):
        result.setdefault("rid", str(num))
        self.update(result)
        return result

    def get_events(self):
        try:
            self.result_handle = gzip.open(self.results_file, "rt")
            return (
                self.pre_handle(num, result)
                for num, result in enumerate(csv.DictReader(self.result_handle))
            )
        except OSError:
            msg = "Error: {}."
            self.log_error(msg.format("No search result. Cannot send alert action."))
            sys.exit(2)

    def prepare_meta_for_cam(self):
        with gzip.open(self.results_file, "rt") as rf:
            for num, result in enumerate(csv.DictReader(rf)):
                result.setdefault("rid", str(num))
                self.update(result)
                self.invoke()
                break

    def run(self, argv):
        status = 0
        if len(argv) < 2 or argv[1] != "--execute":
            msg = f'Error: argv="{argv}", expected="--execute"'
            print(msg, file=sys.stderr)
            sys.exit(1)

        # prepare meta first for permission lack error handling: TAB-2455
        self.prepare_meta_for_cam()
        try:
            level = self.get_log_level()
            if level:
                self._logger.setLevel(level)
        except Exception as e:
            if str(e) and "403" in str(e):  # Handled e.message with str(e)
                self.log_error("User does not have permissions")
            else:
                self.log_error("Unable to set log level")
            sys.exit(2)

        try:
            status = self.process_event()
        except OSError:
            msg = "Error: {}."
            self.log_error(msg.format("No search result. Cannot send alert action."))
            sys.exit(2)
        except Exception as e:
            msg = "Unexpected error: {}."
            if str(e):  # e.message handled
                self.log_error(msg.format(str(e)))  # e.message handled
            else:
                import traceback

                self.log_error(msg.format(traceback.format_exc()))
            sys.exit(2)
        finally:
            if self.result_handle:
                self.result_handle.close()

        return status
