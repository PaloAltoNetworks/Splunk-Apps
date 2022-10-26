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

import re

from defusedxml import ElementTree as et


def parse_conf_xml_dom(xml_content):
    """
    @xml_content: XML DOM from splunkd
    """
    xml_content = xml_content.decode("utf-8")
    m = re.search(r'xmlns="([^"]+)"', xml_content)
    ns = m.group(1)
    m = re.search(r'xmlns:s="([^"]+)"', xml_content)
    sub_ns = m.group(1)
    entry_path = "./{%s}entry" % ns
    stanza_path = "./{%s}title" % ns
    key_path = "./{{{}}}content/{{{}}}dict/{{{}}}key".format(ns, sub_ns, sub_ns)
    meta_path = "./{{{}}}dict/{{{}}}key".format(sub_ns, sub_ns)
    list_path = "./{{{}}}list/{{{}}}item".format(sub_ns, sub_ns)

    xml_conf = et.fromstring(xml_content)
    stanza_objs = []
    for entry in xml_conf.iterfind(entry_path):
        for stanza in entry.iterfind(stanza_path):
            stanza_obj = {"name": stanza.text, "stanza": stanza.text}
            break
        else:
            continue

        for key in entry.iterfind(key_path):
            if key.get("name") == "eai:acl":
                meta = {}
                for k in key.iterfind(meta_path):
                    meta[k.get("name")] = k.text
                stanza_obj[key.get("name")] = meta
            elif key.get("name") != "eai:attributes":
                name = key.get("name")
                if name.startswith("eai:"):
                    name = name[4:]
                list_vals = [k.text for k in key.iterfind(list_path)]
                if list_vals:
                    stanza_obj[name] = list_vals
                else:
                    stanza_obj[name] = key.text
                    if key.text == "None":
                        stanza_obj[name] = None
        stanza_objs.append(stanza_obj)
    return stanza_objs
