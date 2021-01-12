
# encoding = utf-8

import os
import sys
import time
import datetime
import json

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''

def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    customer_id = definition.parameters.get('customer_id', None)
    access_key_id = definition.parameters.get('access_key_id', None)
    secret_access_key = definition.parameters.get('secret_access_key', None)
    pass

def query_api(helper, url, parameters, api_type, proxy_enabled):
    global_page_length = 1000
    total = 1000
    results = []
    start_time = time.time()
    page_offset = 0
    
    if api_type == 'devices':
        items = 'devices'
        page_offset = helper.get_check_point("offset")
        if not page_offset:
            page_offset = 1000
        page = 0
        max_pages = 20
        
        while page < max_pages:
            method = 'GET'
            response = helper.send_http_request(url, method, parameters,
                                                payload=None, headers=None,
                                                cookies=None, verify=True, cert=None,
                                                timeout=30, use_proxy=proxy_enabled)
            r_status = response.status_code
            if r_status == 200:
                entries = response.json()[items]
                results = results + entries
                total = len(entries)
                page_offset = page_offset + global_page_length
                parameters.update({'offset': page_offset})
                page += 1
                helper.log_debug("Current Offset: {0}, Total Entries: {1}, Next Page: {2}".format(page_offset, total, page) )
                if total < global_page_length:
                    helper.delete_check_point("offset")
                    helper.delete_check_point("last_run_end")
                    helper.log_debug("End of device list. Cleared checkpoint data.")
                    break
            else:
                helper.log_debug(r_status)
                break
        else: 
            now = datetime.datetime.now()
            helper.save_check_point("offset", page_offset)
            helper.save_check_point("last_run_timestamp", datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S"))
            helper.log_debug("We have reached max_page. Saved offset: {0} last_run_end: {1}".format(page_offset, now))

            
    else:
        items = 'items'
        while total == global_page_length:
            method = 'GET'
            response = helper.send_http_request(url, method, parameters,
                                                payload=None, headers=None,
                                                cookies=None, verify=True, cert=None,
                                                timeout=30, use_proxy=proxy_enabled)
            r_status = response.status_code
            if r_status == 200:
                entries = response.json()[items]
                results = results + entries
                total = len(entries)
                page_offset = page_offset + global_page_length
                helper.log_debug("Current Offset: {0}, Total Entries: {1}".format(page_offset, total) )
                parameters.update({'offset': page_offset})
            else:
                helper.log_debug(r_status)
                break
    run_time = time.time() - start_time
    helper.log_debug("End of {0} results. Function took {1} to run".format(api_type, run_time))
    return (results)

def collect_events(helper, ew):
    # Set debug level
    log_level = helper.get_log_level()
    helper.set_log_level(log_level)
    # Get Proxy Settings
    proxy_settings = helper.get_proxy()
    proxy_enabled = bool(proxy_settings)
    # helper.log_debug("Checking if Proxy is enabled")
    # helper.log_debug(proxy_enabled) 

    opt_customer_id = helper.get_arg('customer_id')
    opt_access_key_id = helper.get_arg('access_key_id')
    opt_secret_access_key = helper.get_arg('secret_access_key')

    global_url = "https://{0}.iot.paloaltonetworks.com/pub/v4.0".format(
        opt_customer_id)
    global_url_params = {
        'customerid': opt_customer_id,
        'key_id': opt_access_key_id,
        'access_key': opt_secret_access_key,
        'pagelength': 1000,
        'offset': 0,
    }

    last_device_pull = helper.get_check_point("last_run_timestamp")

    # Device inventory takes a long time to fetch because there can be tens of
    # thousands of devices. It can take longer than the poll interval to get all
    # the devices. So at each poll interval, we fetch maximum 20,000 devices
    # (20 pages of 1000 devices each). We also wait 5 minutes between each fetch
    # just in case a crazy pull interval like 5 seconds was used.
    if not last_device_pull or datetime.datetime.strptime(last_device_pull, "%Y-%m-%d %H:%M:%S") < datetime.datetime.now() - datetime.timedelta(minutes=5):
        # Lets get Device Inventory
        device_url = '{0}/device/list'.format(global_url)
        params = {
            'filter_monitored': 'yes',
            'detail': 'true',
        }
        params.update(global_url_params)
        devices = query_api(helper, device_url, params, 'devices', proxy_enabled)
        for data in devices:
            event = helper.new_event(
                host=global_url,
                source=helper.get_input_stanza_names(),
                index=helper.get_output_index(),
                sourcetype='pan:iot_device',
                data=json.dumps(data))
            ew.write_event(event)
    else:
        helper.log_debug("Skipping device inventory pull. Last pulled: {0}".format(last_device_pull))

    # Lets get Alerts
    alerts_url = '{0}/alert/list'.format(global_url)
    params = {
        'type': 'policy_alert',
    }
    params.update(global_url_params)
    alerts = query_api(helper, alerts_url, params, 'alerts', proxy_enabled)
    for data in alerts:
        event = helper.new_event(
            host=global_url,
            source=helper.get_input_stanza_names(),
            index=helper.get_output_index(),
            sourcetype='pan:iot_alert',
            data=json.dumps(data))
        ew.write_event(event)

    # # Vulnerabilities
    vuln_url = '{0}/vulnerability/list'.format(global_url)
    params = {
        'groupby': 'device',
    }
    params.update(global_url_params)
    vulnerabilities = query_api(helper, vuln_url, params, 'vulnerabilities', proxy_enabled)
    for data in vulnerabilities:
        data['customerId'] = opt_customer_id
        event = helper.new_event(
            host=global_url,
            source=helper.get_input_stanza_names(),
            index=helper.get_output_index(),
            sourcetype='pan:iot_vulnerability',
            data=json.dumps(data))
        ew.write_event(event)
