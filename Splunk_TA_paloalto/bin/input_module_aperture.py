
# encoding = utf-8

import os
import sys
import time
import datetime
import json
import base64

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single
instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''

REGION_DOMAIN = {
    'us': 'api.aperture.paloaltonetworks.com',
    'eu': 'api.aperture-eu.paloaltonetworks.com',
    'apac': 'api.aperture-apac.paloaltonetworks.com',
}


def validate_input(helper, definition):
    """Implement your own validation logic to
        validate the input stanza configurations"""
    # This example accesses the modular input variable
    opt_global_account = definition.parameters.get('global_account', None)
    pass


def get_auth_token(helper, opt_global_account, proxy_enabled):
    helper.log_debug("Start get_auth_token.")
    client_id = opt_global_account['username']
    secret = opt_global_account['password']
    region = helper.get_arg('region')
    url_domain = REGION_DOMAIN[region]
    url = "https://{0}/oauth/token".format(url_domain)
    method = "POST"
    parameters = {'scope': 'api_access',
                  'grant_type': 'client_credentials'}
    auth = base64.encodestring('{0}:{1}'.format(client_id, secret)) \
        .replace('\n', '')
    header = {'Authorization': 'Basic ' + auth,
              'Content-Type': 'application/x-www- \
              form-urlencoded; charset=ISO-8859-1',
              'Accept': 'application/json'}
    response = helper.send_http_request(url, method, parameters=parameters,
                                        payload=None, headers=header,
                                        cookies=None, verify=True, cert=None,
                                        timeout=30, use_proxy=proxy_enabled)
    r_status = response.status_code
    if r_status == 200:
        helper.log_debug('Token recieved')
        token = response.json()['access_token']
        return token
    elif r_status == 401:
        helper.log_error('ERROR: Invalid credentials.')
        raise ValueError(r_status)
    else:
        helper.log_error('ERROR: Unable to retrieve token.')
        helper.log_debug(r_status)
        raise ValueError(r_status)


def collect_events(helper, ew):
    log_level = helper.get_log_level()
    helper.set_log_level(log_level)
    opt_global_account = helper.get_arg('global_account')
    region = helper.get_arg('region')
    url_domain = REGION_DOMAIN[region]
    proxy_settings = helper.get_proxy()
    proxy_enabled = bool(proxy_settings)
    helper.log_debug("Checking if Proxy is enabled")
    helper.log_debug(proxy_enabled)
    helper.log_debug("Current input type is set to:")
    helper.log_debug(helper.get_input_stanza_names())
    token = get_auth_token(helper, opt_global_account, proxy_enabled)
    headers = {'Authorization': 'Bearer ' + token}
    method = 'GET'
    url = "https://{0}/api/v1/log_events_bulk".format(url_domain)
    r_status = 200
    while r_status != 204:
        response = helper.send_http_request(
            url, method, parameters=None, payload=None,
            headers=headers, cookies=None, verify=True, cert=None,
            timeout=30, use_proxy=proxy_enabled)
        r_status = response.status_code
        helper.log_debug('API status code is:')
        helper.log_debug(r_status)
        if r_status == 200:
            helper.log_debug("Adding data to index.")
            events = response.json()['events']
            for data in events:
                helper.log_debug(data)
                timestamp = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                final_time = (timestamp - datetime.datetime.fromtimestamp(0)).total_seconds()
                helper.log_debug(final_time)
                try:
                    event = helper.new_event(
                        host=url_domain,
                        source=helper.get_input_stanza_names(),
                        index=helper.get_output_index(),
                        sourcetype=helper.get_sourcetype(),
                        time=final_time,
                        data=json.dumps(data))
                    ew.write_event(event)
                except Exception as e:
                    ew.log_error('Error on parse event. ' + str(e))
        elif r_status == 204:
            helper.log_debug("STATUS 204: No new events were found.")
            break
        elif r_status >= 400:
            helper.log_debug("ERROR Status is:")
            helper.log_debug(r_status)
            raise ValueError(r_status)
        else:
            helper.log_error('There was a problem when trying to collect events using the aperture API call.')
