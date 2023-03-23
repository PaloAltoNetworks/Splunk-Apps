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

import subprocess
import sys
import traceback

import splunktalib.splunk_platform as sp
from splunktalib.common import log


def _parse_modinput_configs(root, outer_block, inner_block):
    """
    When user splunkd spawns modinput script to do config check or run

    <?xml version="1.0" encoding="UTF-8"?>
    <input>
      <server_host>localhost.localdomain</server_host>
      <server_uri>https://127.0.0.1:8089</server_uri>
      <session_key>xxxyyyzzz</session_key>
      <checkpoint_dir>ckpt_dir</checkpoint_dir>
      <configuration>
        <stanza name="snow://alm_asset">
          <param name="duration">60</param>
            <param name="host">localhost.localdomain</param>
            <param name="index">snow</param>
            <param name="priority">10</param>
        </stanza>
        ...
      </configuration>
    </input>

    When user create an stanza through data input on WebUI

    <?xml version="1.0" encoding="UTF-8"?>
    <items>
      <server_host>localhost.localdomain</server_host>
      <server_uri>https://127.0.0.1:8089</server_uri>
      <session_key>xxxyyyzzz</session_key>
      <checkpoint_dir>ckpt_dir</checkpoint_dir>
      <item name="abc">
        <param name="duration">60</param>
        <param name="exclude"></param>
        <param name="host">localhost.localdomain</param>
        <param name="index">snow</param>
        <param name="priority">10</param>
      </item>
    </items>
    """

    confs = root.getElementsByTagName(outer_block)
    if not confs:
        log.logger.error("Invalid config, missing %s section", outer_block)
        raise Exception(f"Invalid config, missing {outer_block} section")

    configs = []
    stanzas = confs[0].getElementsByTagName(inner_block)
    for stanza in stanzas:
        config = {}
        stanza_name = stanza.getAttribute("name")
        if not stanza_name:
            log.logger.error("Invalid config, missing name")
            raise Exception("Invalid config, missing name")

        config["name"] = stanza_name
        params = stanza.getElementsByTagName("param")
        for param in params:
            name = param.getAttribute("name")
            if (
                name
                and param.firstChild
                and param.firstChild.nodeType == param.firstChild.TEXT_NODE
            ):
                config[name] = param.firstChild.data
        configs.append(config)
    return configs


def parse_modinput_configs(config_str):
    """
    @config_str: modinput XML configuration feed by splunkd
    @return: meta_config and stanza_config
    """

    import defusedxml.minidom as xdm

    meta_configs = {
        "server_host": None,
        "server_uri": None,
        "session_key": None,
        "checkpoint_dir": None,
    }
    root = xdm.parseString(config_str)
    doc = root.documentElement
    for tag in meta_configs.keys():
        nodes = doc.getElementsByTagName(tag)
        if not nodes:
            log.logger.error("Invalid config, missing %s section", tag)
            raise Exception("Invalid config, missing %s section", tag)

        if nodes[0].firstChild and nodes[0].firstChild.nodeType == nodes[0].TEXT_NODE:
            meta_configs[tag] = nodes[0].firstChild.data
        else:
            log.logger.error("Invalid config, expect text ndoe")
            raise Exception("Invalid config, expect text ndoe")

    if doc.nodeName == "input":
        configs = _parse_modinput_configs(doc, "configuration", "stanza")
    else:
        configs = _parse_modinput_configs(root, "items", "item")
    return meta_configs, configs


def get_modinput_configs_from_cli(modinput, modinput_stanza=None):
    """
    @modinput: modinput name
    @modinput_stanza: modinput stanza name, for multiple instance only
    """

    assert modinput

    splunkbin = sp.get_splunk_bin()
    cli = [splunkbin, "cmd", "splunkd", "print-modinput-config", modinput]
    if modinput_stanza:
        cli.append(modinput_stanza)

    out, err = subprocess.Popen(
        cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if err:
        log.logger.error("Failed to get modinput configs with error: %s", err)
        return None, None
    else:
        return parse_modinput_configs(out)


def get_modinput_config_str_from_stdin():
    """
    Get modinput from stdin which is feed by splunkd
    """

    try:
        return sys.stdin.read(5000)
    except Exception:
        log.logger.error(traceback.format_exc())
        raise


def get_modinput_configs_from_stdin():
    config_str = get_modinput_config_str_from_stdin()
    return parse_modinput_configs(config_str)
