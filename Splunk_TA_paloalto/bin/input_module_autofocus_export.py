
# encoding = utf-8

import os
import sys
import time
import datetime

libpath = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(libpath, 'lib')]
import common
import pan.afapi
import json

from kvstore import KvStoreHandler

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    opt_label = definition.parameters.get('label', None)
    pass


def collect_events(helper, ew):
    # Implement your data collection logic here

    # The following examples get the arguments of this input.
    # Note, for single instance mod input, args will be returned as a dict.
    # For multi instance mod input, args will be returned as a single value.
    opt_label = helper.get_arg('label')

    # In single instance mode, to get arguments of a particular input, use
    # opt_label = helper.get_arg('label', stanza_name)

    # get input type
    # helper.get_input_type()

    # The following examples get input stanzas.
    # get all detailed input stanzas
    # helper.get_input_stanza()
    # get specific input stanza with stanza name
    # helper.get_input_stanza(stanza_name)
    # get all stanza names
    # helper.get_input_stanza_names()

    # The following examples get options from setup page configuration.
    # get the loglevel from the setup page
    loglevel = helper.get_log_level()
    # get proxy setting configuration
    # proxy_settings = helper.get_proxy()
    # get global variable configuration
    global_autofocus_api_key = helper.get_global_setting("autofocus_api_key")
    sessionKey = helper.context_meta['session_key']

    # The following examples show usage of logging related helper functions.
    # write to the log for this modular input using configured global log level or INFO as default
    # helper.log("log message")
    # write to the log using specified log level
    # helper.log_debug("log message")
    # helper.log_info("log message")
    # helper.log_warning("log message")
    # helper.log_error("log message")
    # helper.log_critical("log message")
    # set the log level for this modular input
    # (log_level can be "debug", "info", "warning", "error" or "critical", case insensitive)
    helper.set_log_level(loglevel)


    # sessionKey = inputs.metadata.get('session_key')
    for label in opt_label:
        helper.log_debug("Current Label: " + label)
        # Check if Label already exsist and get last submit date
        helper.log_debug("Getting AutoFocus Export for results")
        # Use API to get entries in Export List from AutoFocus
        values = {
            "apiKey": global_autofocus_api_key,
            # "panosFormatted": "true",
            "exportMetadata": "true",
            "label": label
        }
        try:
            afapi = pan.afapi.PanAFapi(api_key=global_autofocus_api_key)
            jsAfapi = afapi.export(json.dumps(values)).json
            af_export = jsAfapi['export_list']
            # helper.log_debug(jsAfapi)
        except pan.afapi.PanAFapiError as e:
            helper.log_debug(e)
            sys.exit(1)

        sync_kvstore = sync_to_kvstore(helper, sessionKey, label, af_export)
        helper.log_debug(sync_kvstore)
        # Label does not exsist in KVstore go ahead and batch import.
        if sync_kvstore == 1:
            helper.log_debug("New to KVSTORE")
            send_to_kvstore(helper, sessionKey, jsAfapi['export_list'])
        # Label does exsist in KVstore. Change Detected.
        elif sync_kvstore == -1:
            helper.log_debug("Update KVSTORE")
            # Delete entries for given label
            options = {
                "app": "Splunk_TA_paloalto",
                "owner": "nobody",
                "collection": "autofocus_export"
            }
            query = {"label": label}
            delete = True
            helper.log_debug("Delete entries for this label.")
            remove = KvStoreHandler.query(query, sessionKey, options, delete)
            helper.log_debug("Add entries with this label to kvstore")
            send_to_kvstore(helper, sessionKey, jsAfapi['export_list'])
        # NO CHANGE TO EXPORT LIST
        else:
            helper.log_debug("No Change")

    """
    # The following examples send rest requests to some endpoint.
    response = helper.send_http_request(url, method, parameters=None, payload=None,
                                        headers=None, cookies=None, verify=True, cert=None,
                                        timeout=None, use_proxy=True)
    # get the response headers
    r_headers = response.headers
    # get the response body as text
    r_text = response.text
    # get response body as json. If the body text is not a json string, raise a ValueError
    r_json = response.json()
    # get response cookies
    r_cookies = response.cookies
    # get redirect history
    historical_responses = response.history
    # get response status code
    r_status = response.status_code
    # check the response status, if the status is not sucessful, raise requests.HTTPError
    response.raise_for_status()
# The following examples show usage of check pointing related helper functions.
    # save checkpoint
    helper.save_check_point(key, state)
    # delete checkpoint
    helper.delete_check_point(key)
    # get checkpoint
    state = helper.get_check_point(key)

    # To create a splunk event
    helper.new_event(data, time=None, host=None, index=None, source=None, sourcetype=None, done=True, unbroken=True)
    """

    '''
    # The following example writes a random number as an event. (Multi Instance Mode)
    # Use this code template by default.
    import random
    data = str(random.randint(0,100))
    event = helper.new_event(source=helper.get_input_type(), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
    ew.write_event(event)
    '''

    '''
    # The following example writes a random number as an event for each input config. (Single Instance Mode)
    # For advanced users, if you want to create single instance mod input, please use this code template.
    # Also, you need to uncomment use_single_instance_mode() above.
    import random
    input_type = helper.get_input_type()
    for stanza_name in helper.get_input_stanza_names():
        data = str(random.randint(0,100))
        event = helper.new_event(source=input_type, index=helper.get_output_index(stanza_name), sourcetype=helper.get_sourcetype(stanza_name), data=data)
        ew.write_event(event)
    '''


def sync_to_kvstore(helper, sessionKey, label, af_export):
    helper.log_debug("checking KVSTORE")
    url_options = {
        "app": "Splunk_TA_paloalto",
        "owner": "nobody",
        "collection": "autofocus_export"
    }
    query = {"label": label}
    arg = {
        "query": query
    }
    response = KvStoreHandler.adv_query(arg, url_options, sessionKey)
    # helper.log_debug(response)
    results = 0
    kv_export = json.loads(response[1])
    # helper.log_debug("kv_export:")
    # helper.log_debug(kv_export)
    # helper.log_debug("af_export:")
    # helper.log_debug(af_export)

    # Check to see if we have entries in the KVstore already.
    if kv_export:
        helper.log_debug("Label Exist")
        # Check if list are same size
        if len(kv_export) == len(af_export):
            for entry in kv_export:
                # Remove fields from kv_export so dicts will match.
                if '_key' in entry:
                    del(entry['_key'])
                if '_user' in entry:
                    del(entry['_user'])
                if entry not in af_export:
                    helper.log_debug("not a match")
                    helper.log_debug(entry)
                    results = -1
                    return results
                else:
                    helper.log_debug("Match")
        else:
            helper.log_debug("List count not same.")
            results = -1
            return results
    else:
        helper.log_debug("Label return empty")
        results = 1
    return results


def send_to_kvstore(helper, sessionKey, export_list):
    helper.log_debug("Inside Send to KVSTORE")
    url_options = {
        "app": "Splunk_TA_paloalto",
        "owner": "nobody",
        "collection": "autofocus_export"
    }
    helper.log_debug(export_list)
    response = KvStoreHandler.batch_create(export_list, sessionKey, url_options)
    helper.log_debug(response)