
# encoding = utf-8

import json
from typing import List, Any
from traceback import format_exc
from datetime import datetime, timezone, timedelta
# from dateparser import parse

try:
    from pyxdr.pyxdr import PyXDRClient
except ImportError:
    import os
    import sys

    libpath = os.path.dirname(os.path.abspath(__file__))
    sys.path[:0] = [os.path.join(libpath, 'lib')]
    from pyxdr.pyxdr import PyXDRClient  # pylint: disable=C0412

DEFAULT_FIRST_FETCH = 7 # How long to back in time for first fetch if not specified by user (Days)

def ts_to_string(timestamp: int) -> str:
    """
    Used for debugging, converts a timestamp in ms to an ISO string
    """
    return datetime.fromtimestamp(int(timestamp / 1000), timezone.utc).isoformat()

def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    tenant = definition.parameters.get('xdr_tenant', None)
    region = definition.parameters.get('xdr_region', None)
    api_key_id = definition.parameters.get('xdr_key_id', None)
    api_key = definition.parameters.get('xdr_key', None)
    pass

def get_mod_time(helper):
    latest_modification_time = helper.get_check_point("latest_incident_modified")
    # latest_modification_time = None

    if latest_modification_time:
        mod_time = latest_modification_time + 1
    else:
        first_fetch = helper.get_arg("XDR_FIRST_FETCH")
        helper.log_debug("first_fetch: {0}".format(first_fetch))

        if first_fetch:
            parsed_dt = first_fetch
            # parsed_dt =  now - timedelta(days=DEFAULT_FIRST_FETCH)
        else:
            now = datetime.now()
            parsed_dt =  now - timedelta(days=DEFAULT_FIRST_FETCH)
            # helper.log_debug("parsed_dt: {0}".format(parsed_dt))

        mod_time = int(parsed_dt.timestamp() * 1000)
        # helper.log_debug("MOD TIME: {0}".format(mod_time))
    return mod_time


def fetch_xdr_incidents(helper, client, mod_time):
    filters: List[Any] = []

    helper.log_debug(
        f"modification_time filter set to: {ts_to_string(mod_time)}"
        )
    filters.append(
        {
            "field": "modification_time",
            "operator": "gte",
            "value": mod_time,
        }
    )

    incidents = client.get_incidents(
        limit=50,
        sort_field="modification_time",
        sort_order="asc",
        filters=filters,
    )
    return incidents

def fetch_incident_details(helper, client, incident):
    try:
        helper.log_debug('GET DETAILS PLEASE')
        incident_details = client.get_incident_extra_data(
            incident_id=int(incident["incident_id"])
        )
        helper.log_debug('FINISH DETAILS')
    except KeyError as ex:
        helper.log_debug(
            f"Skipping incident as incident_id is not found: {str(ex)}"
        )
    helper.log_debug(incident_details)
    return incident_details

def handle_incidents(helper, ew, incidents, get_details, base_url):
    # Save modification time to KVStore
    latest_modification_time = int(
        incidents[-1].get("modification_time"))
    latest_incident_id = int(incidents[-1].get("incident_id"))
    helper.save_check_point(
        "latest_incident_modified", latest_modification_time
    )
    # Send each incident to Splunk
    for incident in incidents:
        if get_details:
            incident_details = fetch_incident_details(helper, client, incident) 
            event = helper.new_event(
                host=base_url,
                source=helper.get_input_stanza_names(),
                index=helper.get_output_index(),
                sourcetype='pan:xdr_incident',
                data=json.dumps(incident_details))
            ew.write_event(event)
        else:
            event = helper.new_event(
                host=base_url,
                source=helper.get_input_stanza_names(),
                index=helper.get_output_index(),
                sourcetype='pan:xdr_incident',
                data=json.dumps(incident))
            ew.write_event(event)
    helper.log_debug(f"Got {len(incidents)} results")
    helper.log_debug(
        "Got the following incident IDs: "
        + " ".join([str(y) for y in incidents])
    )
    helper.log_debug(
        f"latest_modification_time: {ts_to_string(latest_modification_time)}"
    )
    helper.log_debug(f"latest_incident_id: {latest_incident_id}")


def collect_events(helper, ew):
    # Set debug level
    log_level = helper.get_log_level()
    helper.set_log_level(log_level)
    
    # Get input values and validate
    get_details = False 
    api_key_id = int(helper.get_arg("xdr_key_id"))
    api_key = helper.get_arg("xdr_key")
    tenant = helper.get_arg("xdr_tenant")
    region = helper.get_arg("xdr_region")
    # Uncomment this section if we decide to capture incident details.
    # if helper.get_arg("XDR_GET_DETAILS") == "True":
        # get_details = True

    if not api_key_id:
        helper.log_error("xdr_api_id environment not set")

    if not api_key:
        helper.log_error("xdr_api_key environment not set")

    if not tenant:
        helper.log_error("xdr_tenant environment variable not set")

    if not region:
        helper.log_error("xdr_region environment variable not set")

    # Set base_url based on tenant and region
    base_url = "https://api-{0}.xdr.{1}.paloaltonetworks.com".format(tenant, region)

    # Create Cortex XDR API Client
    client = PyXDRClient(
        api_key_id=api_key_id,
        api_key=api_key,
        base_url=base_url,
        helper=helper,
    )

    # Check KVStore for modification time
    mod_time = get_mod_time(helper)

    # Fetch incidents for Cortex XDR
    incidents = fetch_xdr_incidents(helper, client, mod_time)
    
    if incidents:
        handle_incidents(helper, ew, incidents, get_details, base_url)
    else:
        helper.log_debug("No Incidents")
        
