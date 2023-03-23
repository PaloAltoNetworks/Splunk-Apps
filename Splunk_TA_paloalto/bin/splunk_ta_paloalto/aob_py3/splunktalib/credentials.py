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
Handles credentials related stuff
"""

import re
import warnings

import defusedxml.minidom as xdm

import splunktalib.common.util as util
import splunktalib.common.xml_dom_parser as xdp
import splunktalib.rest as rest

# Splunk can only encrypt string when length <=255
SPLUNK_CRED_LEN_LIMIT = 255


class CredException(Exception):
    pass


class CredNotFound(CredException):
    """
    Credential information not exists
    """

    pass


def create_credential_manager(username, password, splunkd_uri, app, owner, realm):
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    session_key = CredentialManager.get_session_key(username, password, splunkd_uri)
    return CredentialManager(splunkd_uri, session_key, app, owner, realm)


class CredentialManager:
    """
    Credential related interfaces
    """

    def __init__(self, splunkd_uri, session_key, app="-", owner="nobody", realm=None):
        """
        :app: when creating/upating/deleting app is required
        """
        warnings.warn(
            "This class is deprecated. "
            "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
            DeprecationWarning,
            stacklevel=2,
        )

        self._app = app
        self._splunkd_uri = splunkd_uri
        self._owner = owner
        self._sep = "``splunk_cred_sep``"

        if realm:
            self._realm = realm
        else:
            self._realm = app

        self._session_key = session_key

    def set_appname(self, app):
        """
        This are cases we need edit/remove/create confs in different app
        context. call this interface to switch app context before manipulate
        the confs in different app context
        """

        self._app = app

    @staticmethod
    def get_session_key(username, password, splunkd_uri="https://localhost:8089"):
        """
        Get session key by using login username and passwrod
        :return: session_key if successful, None if failed
        """

        eid = "".join((splunkd_uri, "/services/auth/login"))
        postargs = {
            "username": username,
            "password": password,
        }

        response = rest.splunkd_request(eid, None, method="POST", data=postargs)

        if response is None:
            raise CredException("Get session key failed.")

        xml_obj = xdm.parseString(response.text)
        session_nodes = xml_obj.getElementsByTagName("sessionKey")
        if not session_nodes:
            raise CredException("Invalid username or password.")
        session_key = session_nodes[0].firstChild.nodeValue
        if not session_key:
            raise CredException("Get session key failed.")
        return session_key

    def update(self, stanza):
        """
        Update or Create credentials based on the stanza
        :stanza: nested dict object. The outlayer keys are stanza name, and
                 inner dict is user/pass key/value pair to be encrypted
         {
         "stanza_name": {"tommy": "tommypasswod", "jerry": "jerrypassword"}
         }
        :return: raise on failure
        """

        for name, encr_dict in list(stanza.items()):
            encrypts = []
            for key, val in list(encr_dict.items()):
                encrypts.append(key)
                encrypts.append(val)
            self._update(name, self._sep.join(encrypts))

    def _update(self, name, str_to_encrypt):
        """
        Update the string for the name.
        :return: raise on failure
        """

        if len(str_to_encrypt) <= SPLUNK_CRED_LEN_LIMIT:
            self._do_update(name, str_to_encrypt)
            return

        # split the str_to_encrypt when len > 255
        length = SPLUNK_CRED_LEN_LIMIT
        i = 0
        while length < len(str_to_encrypt) + SPLUNK_CRED_LEN_LIMIT:
            curr_str = str_to_encrypt[length - SPLUNK_CRED_LEN_LIMIT : length]
            length += SPLUNK_CRED_LEN_LIMIT

            stanza_name = self._sep.join((name, str(i)))
            self._do_update(stanza_name, curr_str)
            i += 1

    def _do_update(self, name, password):
        try:
            self._create(name, password)
        except CredException:
            payload = {"password": password}
            endpoint = self._get_endpoint(name)
            response = rest.splunkd_request(
                endpoint, self._session_key, method="POST", data=payload
            )
            if not response or response.status_code not in (200, 201):
                raise CredException(
                    "Unable to update password for username={}, status={}".format(
                        name, response.status_code
                    )
                )

    def _create(self, name, str_to_encrypt):
        """
        Create a new stored credential.
        :return: raise on failure
        """

        payload = {
            "name": name,
            "password": str_to_encrypt,
            "realm": self._realm,
        }

        endpoint = self._get_endpoint(name)
        resp = rest.splunkd_request(
            endpoint, self._session_key, method="POST", data=payload
        )
        if not resp or resp.status_code not in (200, 201):
            raise CredException("Failed to encrypt username {}".format(name))

    def delete(self, name, throw=False):
        """
        Delete the encrypted entry
        """

        try:
            self._delete(name, throw=True)
        except CredNotFound:
            # try to delete the split stanzas
            try:
                stanzas = self._get_all_passwords()
            except Exception:
                raise

            prefix = self._realm + ":" + name + self._sep
            for stanza in stanzas:
                stanza_name = stanza.get("name")
                match = True
                try:
                    if stanza_name[: len(prefix)] != prefix:
                        match = False
                    num = stanza_name[len(prefix) : -1]
                    int(num)
                except (IndexError, ValueError):
                    match = False
                if match:
                    try:
                        delete_name = name + self._sep + num
                        self._delete(delete_name, throw=True)
                    except CredNotFound:
                        pass
                    except CredException:
                        raise
        except CredException:
            raise

    def _delete(self, name, throw=False):
        """
        Delete the encrypted entry
        """

        endpoint = self._get_endpoint(name)
        response = rest.splunkd_request(endpoint, self._session_key, method="DELETE")

        if response is not None and response.status_code == 404:
            if throw:
                raise CredNotFound("Credential stanza not exits - {}".format(name))
        elif not response or response.status_code not in (200, 201):
            if throw:
                raise CredException(
                    "Failed to delete credential stanza {}".format(name)
                )

    def get_all_passwords(self):
        results = {}
        all_stanzas = self._get_all_passwords()
        for stanza in all_stanzas:
            name = stanza.get("name")
            match = re.match(r"(.+){}(\d+)".format(self._sep), name)
            if match:
                actual_name = match.group(1) + ":"
                index = int(match.group(2))
                if results.get(actual_name):
                    exist_stanza = results.get(actual_name)
                else:
                    exist_stanza = stanza
                    exist_stanza["name"] = actual_name
                    exist_stanza["username"] = exist_stanza["username"].split(
                        self._sep
                    )[0]
                    exist_stanza["clears"] = {}
                    exist_stanza["encrs"] = {}

                try:
                    exist_stanza["clears"][index] = stanza.get("clear_password")
                    exist_stanza["encrs"][index] = stanza.get("encr_password")
                except KeyError:
                    exist_stanza["clears"] = {}
                    exist_stanza["encrs"] = {}
                    exist_stanza["clears"][index] = stanza.get("clear_password")
                    exist_stanza["encrs"][index] = stanza.get("encr_password")

                results[actual_name] = exist_stanza

            else:
                results[name] = stanza

        # merge the stanzas by index
        for name, stanza in list(results.items()):
            field_clear = stanza.get("clears")
            field_encr = stanza.get("encrs")
            if isinstance(field_clear, dict):
                clear_password = ""
                encr_password = ""
                for index in sorted(field_clear.keys()):
                    clear_password += field_clear.get(index)
                    encr_password += field_encr.get(index)
                stanza["clear_password"] = clear_password
                stanza["encr_password"] = encr_password

                del stanza["clears"]
                del stanza["encrs"]
        return list(results.values())

    def _get_all_passwords(self):
        """
        :return: a list of dict when successful, None when failed.
        the dict at least contains
        {
            "realm": xxx,
            "username": yyy,
            "clear_password": zzz,
        }
        """

        endpoint = self._get_endpoint()
        response = rest.splunkd_request(endpoint, self._session_key, method="GET")
        if response and response.status_code in (200, 201) and response.text:
            return xdp.parse_conf_xml_dom(response.text)
        raise CredException("Failed to get credentials")

    def get_clear_password(self, name=None):
        """
        :return: clear password(s)
        {
        stanza_name: {"user": pass}
        }
        """

        return self._get_credentials("clear_password", name)

    def get_encrypted_password(self, name=None):
        """
        :return: encyrpted password(s)
        """

        return self._get_credentials("encr_password", name)

    def _get_credentials(self, prop, name=None):
        """
        :return: clear or encrypted password for specified realm, user
        """

        all_stanzas = self.get_all_passwords()
        results = {}

        for stanza in all_stanzas:
            if name and not stanza.get("name").endswith(":" + name + ":"):
                continue
            if stanza.get("realm") == self._realm:
                values = stanza[prop].split(self._sep)
                if len(values) % 2 == 1:
                    continue
                result = {values[i]: values[i + 1] for i in range(0, len(values), 2)}
                results[stanza.get("username")] = result
        return results

    @staticmethod
    def _build_name(realm, name):
        return util.format_stanza_name(
            "".join(
                (
                    CredentialManager._escape_string(realm),
                    ":",
                    CredentialManager._escape_string(name),
                    ":",
                )
            )
        )

    @staticmethod
    def _escape_string(string_to_escape):
        r"""
        Splunk secure credential storage actually requires a custom style of
        escaped string where all the :'s are escaped by a single \.
        But don't escape the control : in the stanza name.
        """

        return string_to_escape.replace(":", "\\:")

    def _get_endpoint(self, name=None, query=False):
        app = self._app
        owner = self._owner
        if query:
            app = "-"
            owner = "-"

        if name:
            realm_user = self._build_name(self._realm, name)
            rest_endpoint = "{}/servicesNS/{}/{}/storage/passwords/{}".format(
                self._splunkd_uri, owner, app, realm_user
            )
        else:
            rest_endpoint = "{}/servicesNS/{}/{}/storage/passwords?count=-1" "".format(
                self._splunkd_uri, owner, app
            )
        return rest_endpoint
