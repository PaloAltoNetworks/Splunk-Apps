

"""
pyXDR - Unit Tests file for PyXDRClient
"""
import os
import io
import pytest  # type: ignore
import json
import Splunk_TA_paloalto.bin.input_module_cortex_xdr as input_cortex_xdr
from Splunk_TA_paloalto.bin.lib.pyxdr.pyxdr import PyXDRClient
from .mockhelper import MockHelper

DATA_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/test_data"

mock_base_url = "https://some_customer.xdr.us.paloaltonetworks.com"

class EventWriter():
    def write_event(self, event):
        pass

def util_load_json(path):
    """
    Loads a file with the JSON API data
    """
    with io.open(path, mode="r", encoding="utf-8") as f:
        return json.loads(f.read())

def test_fetch_xdr_incidents(mocker):
    """
    Test a get_incidents API call with sort and no filter
    """
    print("\nRunning test_fetch_xdr_incidents...")
    mock_mod_time = 1620199514577
    mock_data = util_load_json(f"{DATA_DIR}/get_incidents.json")
    mock_api_key = "B" * 32
    mock_api_key_id = 20
    mock_helper = MockHelper()

    # mock_helper = mocker.patch.object(
    #     log_debug, "log_debug", return_value=f"modification_time filter set"
    # )

    client = PyXDRClient(
        api_key_id=mock_api_key_id,
        api_key=mock_api_key,
        base_url=mock_base_url,
        helper=mock_helper
    )
    
    mocker.patch.object(
        client, "get_incidents", return_value=mock_data
    )
    response = input_cortex_xdr.fetch_xdr_incidents(mock_helper, client, mock_mod_time)
    assert response == mock_data
    client.get_incidents.assert_called_once_with(limit=50, sort_field="modification_time", sort_order="asc", filters=[{'field': 'modification_time', 'operator': 'gte', 'value': mock_mod_time}])

def test_handle_incidents(mocker):
    """
    Test handle incidents function in Cortex XDR input mod.
    """
    print("\nRunning test_handle_incidents...")
    mock_helper = mocker.create_autospec(MockHelper)
    mock_incidents = util_load_json(f"{DATA_DIR}/get_incidents.json")
    get_details = False
    mock_ew = mocker.create_autospec(EventWriter)
    input_cortex_xdr.handle_incidents(mock_helper, mock_ew, mock_incidents, get_details, mock_base_url)
    mock_helper.save_check_point.assert_called_once_with('latest_incident_modified', 1579132135407)
    assert mock_ew.write_event.call_count == 5
    
        
