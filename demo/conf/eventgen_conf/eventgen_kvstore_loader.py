from __future__ import division
import json
import requests
import splunk.rest
import time
from outputplugin import OutputPlugin


class MyPlugin(OutputPlugin):
    name = 'eventgen_kvstore_loader'
    MAXQUEUELENGTH = 100
    validSettings = ['kvstore', ]

    def __init__(self, sample):
        OutputPlugin.__init__(self, sample)

        # Verify we were passed in a kvstore setting.
        if not hasattr(sample, 'kvstore'):
            raise ValueError('kvstore not defined for {0}'.format(
                sample.filePath))

        # Wait for the Rest service to come online.
        wait_for_services(sample.sessionKey, sample.kvstore)

        # Get the kvstore data.
        data = get_data(sample.filePath)

        # Delete the old entries.
        delete_from_kvstore(sample.sessionKey, sample.kvstore)

        # Save the new entries to the kvstore.
        save_to_kvstore(data, sample.sessionKey, sample.kvstore)

    def flush(self, *args, **kwargs):
        """Don't do anything with events sent to us from eventgen."""
        pass


def get_data(path):
    data = []
    with open(path, 'r') as fd:
        for line in [x.strip() for x in fd.readlines() if x.strip()]:
            t = json.loads(line)
            data.append(t)

    return data


def wait_for_services(skey, kvstore):
    timeout = time.time() + 60
    while True:
        r = requests.get(_uri(kvstore), headers=_headers(skey), verify=False)
        if r.status_code == 200:
            break
        if time.time() >= timeout:
            raise ValueError('Timeout reached: giving up')
        time.sleep(1)


def delete_from_kvstore(skey, kvstore):
    requests.delete(_uri(kvstore), headers=_headers(skey), verify=False)


def save_to_kvstore(data, skey, kvstore):
    for i in range(0, len(data), 500):
        requests.post(
            _uri(kvstore) + '/batch_save',
            data=json.dumps(data[i:i+500]),
            headers=_headers(skey),
            verify=False)


def _uri(kvstore):
    """Returns the URL of the kvstore."""
    return '/'.join((
        splunk.rest.makeSplunkdUri().rstrip('/'),
        'servicesNS',
        'nobody',
        'Splunk_TA_paloalto',
        'storage',
        'collections',
        'data',
        kvstore))


def _headers(skey):
    """Returns the auth header for Splunk."""
    return {
        'Authorization': 'Splunk {0}'.format(skey),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def load():
    """Returns an instance of the plugin."""
    return MyPlugin
