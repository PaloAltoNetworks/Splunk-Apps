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
import splunktalib.common.xml_dom_parser as xdp
from splunktalib.conf_manager.request import content_request

INPUT_ENDPOINT = "%s/servicesNS/%s/%s/data/inputs/%s"


def _input_endpoint_ns(uri, owner, app, input_type):
    return INPUT_ENDPOINT % (uri, owner, app, input_type)


def reload_data_input(
    splunkd_uri, session_key, owner, app_name, input_type, throw=False
):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    """

    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    uri += "/_reload"
    msg = "Failed to reload data input in app={}: {}".format(app_name, input_type)
    try:
        content_request(uri, session_key, "GET", None, msg)
    except Exception:
        if throw:
            raise


def create_data_input(
    splunkd_uri, session_key, owner, app_name, input_type, name, key_values
):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    :param name: The name of the input stanza to create.
                 i.e. stanza [<input_type>://<name>] will be created.
    :param key_values: a K-V dict of details in the data input stanza.
    :return: None on success else raise exception
    """

    key_values["name"] = str(name).encode("utf-8")
    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    msg = "Failed to create data input in app={}: {}://{}".format(
        app_name,
        input_type,
        name,
    )
    content_request(uri, session_key, "POST", key_values, msg)


def get_data_input(splunkd_uri, session_key, owner, app_name, input_type, name=None):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    :param name: The name of the input stanza to create.
                 i.e. stanza [<input_type>://<name>] will be deleted.
    :return: a list of stanzas in the input type, including metadata
    """

    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    if name:
        uri += "/" + util.format_stanza_name(name)

    # get all the stanzas at one time
    uri += "?count=0&offset=0"

    msg = "Failed to get data input in app={}: {}://{}".format(
        app_name,
        input_type,
        name if name else name,
    )
    content = content_request(uri, session_key, "GET", None, msg)
    return xdp.parse_conf_xml_dom(content)


def update_data_input(
    splunkd_uri, session_key, owner, app_name, input_type, name, key_values
):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    :param name: The name of the input stanza to create.
                 i.e. stanza [<input_type>://<name>] will be updated.
    :param key_values: a K-V dict of details in the data input stanza.
    :return: raise exception when failure
    """

    if "name" in key_values:
        del key_values["name"]
    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    uri += "/" + util.format_stanza_name(name)
    msg = "Failed to update data input in app={}: {}://{}".format(
        app_name,
        input_type,
        name,
    )
    content_request(uri, session_key, "POST", key_values, msg)


def delete_data_input(splunkd_uri, session_key, owner, app_name, input_type, name):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    :param name: The name of the input stanza to create.
                 i.e. stanza [<input_type>://<name>] will be deleted.
    :return raise exception when failed
    """

    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    uri += "/" + util.format_stanza_name(name)
    msg = "Failed to delete data input in app={}: {}://{}".format(
        app_name,
        input_type,
        name,
    )
    content_request(uri, session_key, "DELETE", None, msg)


def operate_data_input(
    splunkd_uri, session_key, owner, app_name, input_type, name, operation
):
    """
    :param splunkd_uri: splunkd uri, e.g. https://127.0.0.1:8089
    :param session_key: splunkd session key
    :param owner: the owner (ACL user), e.g. "-", "nobody"
    :param app_name: the app"s name, e.g. "Splunk_TA_aws"
    :param input_type: name of the input type.
                       if it is a script input, the input is "script",
                       for modinput, say snow, the input is "snow"
    :param name: The name of the input stanza to create.
                 i.e. stanza [<input_type>://<name>] will be operated.
    :param operation: must be "disable" or "enable"
    """

    assert operation in ("disable", "enable")
    uri = _input_endpoint_ns(splunkd_uri, owner, app_name, input_type)
    uri += "/{}/{}".format(util.format_stanza_name(name), operation)
    msg = "Failed to {} data input in app={}: {}://{}".format(
        operation,
        app_name,
        input_type,
        name,
    )
    content_request(uri, session_key, "POST", None, msg)
