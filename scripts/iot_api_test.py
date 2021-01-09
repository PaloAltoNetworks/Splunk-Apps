import os
import sys
import time
import datetime
import json
import requests
import time



def validate_input(definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    customer_id = definition.parameters.get('customer_id', None)
    access_key_id = definition.parameters.get('access_key_id', None)
    secret_access_key = definition.parameters.get('secret_access_key', None)
    pass

def get_device_detail_api():
    api_url = '{0}/device'.format(global_url)
    new_params = global_url_params
    return(api_url, new_params)

def update_list_api():
    api_url = '/{0}/list'.format(global_url)
    new_params = global_url_params
    new_params.update({})
    return(api_url, new_params)

def query_api(url, params, api_type):
    global_page_length = 1000
    total = 1000
    page_offset = 0
    results = []
    start_time = time.time()
    if api_type == 'devices':
        items = 'devices'
        page = 1
        while page <= 20:
            response = requests.get(url, params)
            r_status = response.status_code
            if r_status == 200:
                entries = response.json()[items]
                results = results + entries
                total = len(entries)
                page_offset = page_offset + global_page_length
                params.update({'offset': page_offset})
                page += 1
                print("total entries: {0}".format(total))
                print("Current Offset: {0}".format(page_offset))
                print("Next Page: {0}".format(page))
            else:
                print(r_status)
    else:
        items = 'items'
        while total == global_page_length:
            response = requests.get(url, params)
            r_status = response.status_code
            if r_status == 200:
                entries = response.json()[items]
                results = results + entries
                # total = len(entries)
                page_offset = page_offset + global_page_length 
                print("Total Entries: {0}".format(total))
                print("Current Offset: {0}".format(page_offset))
                params.update({ 'offset': page_offset})
            else:
                print(r_status)
    print('End of results') 
    print("Function took", time.time() - start_time, "seconds to run")
    return (results)

def collect_events():
    # Work on Device Inventory List
    opt_customer_id = os.environ.get("CUSTOMERID")
    opt_access_key_id = os.environ.get("ACCESSKEY")
    opt_secret_access_key = os.environ.get("KEYID")

    global_url = "https://{0}.iot.paloaltonetworks.com/pub/v4.0".format(opt_customer_id)

    global_url_params= {
        'customerid': opt_customer_id,
        'access_key': opt_access_key_id,
        'key_id': opt_secret_access_key,
        'pagelength': 1000,
        'offset': 0,
    }
    try: 
        api_url = '{0}/device/list'.format(global_url)
        params = {
            'filter_monitored': 'yes',
            'detail': 'true',
        }
        params.update(global_url_params)
        devices = query_api(api_url, params, 'devices')
    except Exception as e:
        print(str(e))


    # Lets get Alerts
    # try: 
    #     alerts_url = '{0}/alert/list'.format(global_url)
    #     params = {
    #         'type': 'policy_alert',
    #         'resolved': 'no',
    #     }
    #     params.update(global_url_params)
    #     alerts = query_api(alerts_url, params, 'alerts')
    #     for data in alerts:
    #         print(data)
    #         timestamp = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
    #         final_time = (timestamp - datetime.datetime.fromtimestamp(0)).total_seconds()
    #         helper.log_debug(final_time)
    #         try:
    #             event = helper.new_event(
    #             host=global_url,
    #             source=helper.get_input_stanza_names(),
    #             index=helper.get_output_index(),
    #             sourcetype=helper.get_sourcetype(),
    #             time=final_time,
    #             data=json.dumps(data))
    #             ew.write_event(event)
    #         except Exception as e:
    #             ew.log_error('Error on parse event. ' + str(e))
    # except Exception as e:
    #     print(str(e))

    # # Vulnerabilities 
    # try: 
    #     vuln_url = '{0}/vulnerability/list'.format(global_url)
    #     params = {
    #         'groupby': 'device',
    #     }
    #     params.update(global_url_params)
    #     vulnerabilities = query_api(vuln_url, params, 'vulnerabilities')
    # except Exception as e:
    #     print(str(e))
    #     vuln_params = global_url_params

collect_events()
