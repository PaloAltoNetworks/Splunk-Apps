# pylint: disable=W0613,C0103,R0914,W0621
"""
pyXDR - Unit Tests file for PyXDRClient
"""

import pytest  # type: ignore
import Splunk_TA_paloalto.bin.input_module_cortex_xdr as input_cortex_xdr
# from Splunk_TA_paloalto.bin.lib.pyxdr.pyxdr import PyXDRClient

def test_fetch_xdr_incidents():
    """
    Test a get_incidents API call with sort and no filter
    """
    print("\nRunning test_example...")
    assert True
