# pylint: disable=W0613,C0103,R0914,W0621
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
    helper = MockHelper()
    mod_time = 1620199514577
    MOCK_DATA = util_load_json(f"{DATA_DIR}/get_incidents.json")
    MOCKED_API_KEY = "B" * 32
    MOCKED_API_KEY_ID = 20
    MOCKED_BASE_URL = "https://some_customer.xdr.us.paloaltonetworks.com"
    MOCKED_HELPER = MockHelper()

    client = PyXDRClient(
        api_key_id=MOCKED_API_KEY_ID,
        api_key=MOCKED_API_KEY,
        base_url=MOCKED_BASE_URL,
        helper=MOCKED_HELPER,
    )

    mock_get_incidents = mocker.patch.object(
        client, "get_incidents", return_value=MOCK_DATA
    )
    response = input_cortex_xdr.fetch_xdr_incidents(helper, client, mod_time)
    assert response == MOCK_DATA
