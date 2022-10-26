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

import splunktalib.common.util as util
from splunktalib.conf_manager.request import content_request

PROPERTY_ENDPOINT = "%s/servicesNS/%s/%s/properties/%s"


def _property_endpoint_ns(uri, owner, app, conf_name):
    return PROPERTY_ENDPOINT % (uri, owner, app, conf_name)


def create_properties(splunkd_uri, session_key, owner, app_name, conf_name, stanza):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param conf_name: the name of the conf file, e.g. "props"
    :param stanza: stanza name, e.g. "aws:cloudtrail"
    :return: None on success else raise exception
    """

    uri = _property_endpoint_ns(splunkd_uri, owner, app_name, conf_name)
    msg = "Properties: failed to create stanza={} in conf={}".format(stanza, conf_name)
    payload = {"__stanza": stanza}
    content_request(uri, session_key, "POST", payload, msg)


def get_property(splunkd_uri, session_key, owner, app_name, conf_name, stanza, key):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param conf_name: the name of the conf file, e.g. "props"
    :param stanza: stanza name, e.g. "aws:cloudtrail"
    :param key: the property name
    :return: the property value
    """

    uri = _property_endpoint_ns(splunkd_uri, owner, app_name, conf_name)
    uri += "/{}/{}".format(util.format_stanza_name(stanza), key)
    msg = "Properties: failed to get conf={}, stanza={}, key={}".format(
        conf_name,
        stanza,
        key,
    )
    return content_request(uri, session_key, "GET", None, msg)


def update_properties(
    splunkd_uri, session_key, owner, app_name, conf_name, stanza, key_values
):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param conf_name: the name of the conf file, e.g. "props"
    :param stanza: stanza name, e.g. "aws:cloudtrail"
    :param key_values: the key-value dict of the stanza
    :return: raise exception when failed
    """

    uri = _property_endpoint_ns(splunkd_uri, owner, app_name, conf_name)
    uri += "/" + util.format_stanza_name(stanza)
    msg = "Properties: failed to update conf={}, stanza={}".format(conf_name, stanza)

    has_name = False
    if "name" in key_values:
        has_name = True
        name = key_values["name"]
        del key_values["name"]

    content_request(uri, session_key, "POST", key_values, msg)

    if has_name:
        key_values["name"] = name
