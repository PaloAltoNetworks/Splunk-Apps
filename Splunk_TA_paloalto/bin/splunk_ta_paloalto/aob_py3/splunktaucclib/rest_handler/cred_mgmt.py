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

"""Credential Management for REST Endpoint
"""


import json

import splunk
from splunk import rest
from splunktalib.credentials import CredentialManager as CredMgr

from .error_ctl import RestHandlerError
from .util import getBaseAppName

__all__ = ["CredMgmt"]


class CredMgmt:
    """Credential Management stored in app.conf

    Note: Override it if customized form of ``realm``, ``username``,
        and ``password``.
        If so, override method ``context``.
    """

    PASSWORD_MASK = "********"
    REALM_TEMPLATE = "__REST_CREDENTIAL__#{baseApp}#{endpoint}#{stanzaName}"

    def __init__(self, sessionKey, user, app, endpoint, encryptedArgs):
        self._splunkMgmtUri = rest.makeSplunkdUri()
        self._sessionKey = sessionKey
        self._user, self._app = user, app
        self._endpoint = endpoint
        self._encryptedArgs = set(encryptedArgs)

    def context(self, stanzaName, data=None):
        """Get context for credential, including ``realm``, ``username``
            and ``password``.
        It will be stored in ``app.conf`` in form:
            [credential:<realm>:<username>]
            password = <password>

        Note: Override it if customized form of context needed.

        :param stanzaName: stanza name to be encrypted
        :param data: data to be encrypted which is a dict. It is ``None``
            for decrypt & delete.
        :return: a tuple (realm, username, password)
        """
        realm = CredMgmt.REALM_TEMPLATE.format(
            baseApp=getBaseAppName(), endpoint=self._endpoint, stanzaName=stanzaName
        )
        username = "username"
        password = "" if data is None else json.dumps(data)
        return realm, username, password

    def encrypt(self, stanzaName, data):
        """Encrypt data with given fields.

        :param stanzaName: the stanza name for external information
            of the data in some *.conf
        :param data: data to encrypt, a dict.
        :return:
        """
        cred_data_new = {
            key: ("" if val is None else val)
            for key, val in data.items()
            if key in self._encryptedArgs and val != CredMgmt.PASSWORD_MASK
        }
        if not cred_data_new:
            return data

        try:
            cred_data = self.decrypt(stanzaName, {})
        except splunk.ResourceNotFound:
            cred_data = {}

        cred_data.update(cred_data_new)
        realm, username, password = self.context(stanzaName, data=cred_data)
        cred_mgr = CredMgr(
            self._splunkMgmtUri,
            self._sessionKey,
            app=self._app,
            owner=self._user,
            realm=realm,
        )
        try:
            # since the size of the to-be-encrypted data is not fixed,
            # if the new data have smaller size than the previous one,
            # part of the old data won't be updated, then the updated data will be corrupted.
            # we have to delete the old data first.
            cred_mgr.delete(username, throw=True)
            cred_mgr.update({username: cred_data})
            for arg in data:
                if arg in self._encryptedArgs:
                    data[arg] = CredMgmt.PASSWORD_MASK
        except Exception as exc:
            RestHandlerError.ctl(1020, msgx=exc, shouldPrint=False, shouldRaise=False)
        return data

    def decrypt(self, stanzaName, data):
        """Decrypt data with given fields.
        If a field is not magic token in data, it will be ignored.

        :param stanzaName: the stanza name for external information
            of the data in some *.conf
        :param data: container to store the result, a dict.
        :return:
        """
        if not self._encryptedArgs:
            return data
        realm, username, password = self.context(stanzaName)
        cred_mgr = CredMgr(
            self._splunkMgmtUri,
            self._sessionKey,
            app=self._app,
            owner=self._user,
            realm=realm,
        )

        try:
            creds = cred_mgr.get_clear_password(username)
        except Exception as exc:
            RestHandlerError.ctl(1021, msgx=exc, shouldPrint=True, shouldRaise=True)
        cred = creds.get(username, {})

        for arg, val in list(cred.items()):
            data[arg] = val if arg in self._encryptedArgs else data[arg]
        return data

    def delete(self, stanzaName):
        """Delete encrypted data.

        :param stanzaName: the stanza name for external information of
            the data in some *.conf
        :return:
        """
        if len(self._encryptedArgs) <= 0:
            return

        realm, username, password = self.context(stanzaName)
        cred_mgr = CredMgr(
            self._splunkMgmtUri,
            self._sessionKey,
            app=self._app,
            owner=self._user,
            realm=realm,
        )
        try:
            cred_mgr.delete(username, throw=True)
        except Exception as exc:
            RestHandlerError.ctl(1022, msgx=exc, shouldPrint=False, shouldRaise=False)
            return False
        return True

    def setEncryptedArgs(self, encryptedArgs):
        self._encryptedArgs = set(encryptedArgs)
