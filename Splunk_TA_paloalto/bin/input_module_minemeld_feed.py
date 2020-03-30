
# encoding = utf-8

import base64
import functools
import json
import os
import requests.exceptions
import sys
import time

VERIFY_CERTIFICATE = True

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

def timer(desc):
    def outer(func):
        @functools.wraps(func)
        def inner(*args):
            """Decorator to time function execution.

            If an exception is raised during the function, then a time of "-1"
            will be saved for the given description.

            Note: Any function decorated with this should have the "stats" dict
            as the final argument in its arg list.

            """
            # Setup.
            stats = args[-1]
            stats[desc] = -1
            start = time.time()

            # Execute the function.
            ret_val = func(*args)

            # No exception, so save the runtime and return ret_val.
            stats[desc] = time.time() - start
            return ret_val
        return inner
    return outer


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # feed_url = definition.parameters.get('feed_url', None)
    # credentials = definition.parameters.get('credentials', None)
    pass


def collect_events(helper, ew):
    """Collect the kvstore events from the feed."""
    # Get the short name for this feed.
    name = helper.get_input_stanza_names()
    start = time.time()
    try:
        indicator_timeout = int(helper.get_arg('indicator_timeout')) * 3600
    except ValueError:
        # If this isn't set, timeout indicators immediately.
        indicator_timeout = 0
    stats = {'input_name': name}

    helper.log_info('START Splunk_TA_paloalto indicator retrieval for "{0}"'.format(
        name))

    # Get the current indicators.
    kvs_entries = pull_from_kvstore(helper, name, start, stats)
    stats['previous_indicators'] = len(kvs_entries)

    # Retrieve current entries from the MineMeld feed.
    mmf_entries = []
    try:
        mmf_entries = get_feed_entries(helper, name, start, stats)
    except requests.exceptions.HTTPError as e:
        helper.log_error('Failed to get entries for "{0}": {1}'.format(
            name, e))
        stats['error'] = str(e)
    stats['feed_indicators'] = len(mmf_entries)

    # Merge the two together, and determine which indicators should be expired.
    rm_entries, retained_indicators = merge_entries(
        mmf_entries, kvs_entries, start, indicator_timeout, stats)
    stats['expired_indicators'] = len(rm_entries)
    stats['indicators'] = len(mmf_entries) + retained_indicators

    # Save new/updated indicators to the kvstore.
    save_to_kvstore(helper, name, mmf_entries, stats)

    # Delete the expired indicators.
    remove_from_kvstore(helper, name, rm_entries, stats)

    # Write an event to the index giving some basic stats.
    stats['total_time'] = time.time() - start
    save_stats_as_event(helper, ew, stats)

    # Done
    helper.log_info('END Splunk_TA_paloalto indicator retrieval for "{0}"'.format(
        name))


@timer('read_kvstore')
def pull_from_kvstore(helper, name, start, stats):
    """Retrieves all current indicators."""
    resp = helper.send_http_request(
        url=_uri(helper),
        headers=_headers(helper),
        method='GET',
        verify=False,
        parameters={'query': json.dumps({'splunk_source': name})})
    resp.raise_for_status()

    ans = {}
    for v in resp.json():
        ans[v['indicator']] = {
            '_key': v['_key'],
            'is_present': False,
            'splunk_last_seen': v.get('splunk_last_seen', 0.0)}

    return ans


@timer('retrieve_indicators')
def get_feed_entries(helper, name, start, stats):
    """Pulls the indicators from the minemeld feed."""
    feed_url = helper.get_arg('feed_url')
    feed_creds = helper.get_arg('credentials')
    feed_headers = {}
    # If auth is specified, add it as a header.
    if feed_creds is not None:
        auth = '{0}:{1}'.format(feed_creds['username'], feed_creds['password'])
        auth = base64.encodestring(auth).replace('\n', '')
        feed_headers['Authorization'] = 'Basic {0}'.format(auth)

    # Pull events as json.
    resp = helper.send_http_request(
        url=feed_url,
        method='GET',
        parameters={'v': 'json', 'tr': 1},
        headers=feed_headers,
        verify=VERIFY_CERTIFICATE,
    )

    # Raise exceptions on problems.
    resp.raise_for_status()
    feed_entries = resp.json()

    # Return the normalized events to be saved to the kv store.
    return normalized(name, feed_entries, start)


@timer('merge_indicators')
def merge_entries(mmf_entries, kvs_entries, start, indicator_timeout, stats):
    """
    Merges the current indicators with previous, determining which should
    be expired.
    """
    rm_entries = []
    retained_indicators = 0

    for mmfe in mmf_entries:
        kvse = kvs_entries.get(mmfe['indicator'])
        if kvse is not None:
            kvse['is_present'] = True
            mmfe['_key'] = kvse['_key']

    for info in kvs_entries.itervalues():
        if info['is_present']:
            pass
        elif info['splunk_last_seen'] + indicator_timeout < start:
            rm_entries.append(info['_key'])
        else:
            retained_indicators += 1

    return rm_entries, retained_indicators


@timer('save_to_kvstore')
def save_to_kvstore(helper, name, entries, stats):
    """Saves all normalized entries as `name` events."""
    helper.log_info('Saving {0} entries for MineMeld feed "{1}"'.format(
        len(entries), name))
    url = '{0}/batch_save'.format(_uri(helper))

    # We need to batch in groups of 500, the default.
    for i in range(0, len(entries), 500):
        resp = helper.send_http_request(
            url=url,
            headers=_headers(helper),
            method='POST',
            verify=False,
            payload=entries[i:i+500])
        resp.raise_for_status()


@timer('remove_from_kvstore')
def remove_from_kvstore(helper, name, rm_entries, stats):
    """Removes the specified entries from the kvstore."""
    if not rm_entries:
        return

    helper.log_info('Removing {0} kvstore entries for MineMeld feed "{1}"'.format(
        len(rm_entries), name))
    url = _uri(helper)
    headers = _headers(helper)

    # Batch a few at a time, as splunk 414s if the URI is too long, or times
    # out if it's within the length limits but still hits too many entries to
    # finish on time.  From some tests, it seems like 500 is a good number,
    # which is nice since it matches the batch_save number.
    #
    # The _key field has been 24 characters in length on my system.
    for i in range(0, len(rm_entries), 500):
        rms = rm_entries[i:i+500]
        query = {'$or': list({'_key': x} for x in rms)}
        resp = helper.send_http_request(
            url=url,
            headers=headers,
            method='DELETE',
            verify=False,
            parameters={'query': json.dumps(query)})
        resp.raise_for_status()


def save_stats_as_event(helper, ew, stats):
    """Saves the stats of getting feed events to the index."""
    event = helper.new_event(
        source=helper.get_input_type(),
        index=helper.get_output_index(),
        sourcetype=helper.get_sourcetype(),
        data=json.dumps(stats),
    )
    ew.write_event(event)


def _uri(helper):
    """Returns the URL of the kvstore."""
    return '/'.join((
        helper.context_meta['server_uri'],
        'servicesNS',
        'nobody',
        'Splunk_TA_paloalto',
        'storage',
        'collections',
        'data',
        'minemeldfeeds'))


def _headers(helper):
    """Returns the auth header for Splunk."""
    return {
        'Authorization': 'Splunk {0}'.format(
            helper.context_meta['session_key'])}


def normalized(name, feed_entries, start):
    """Returns a list of normalized kvstore entries."""
    data = []
    for feed_entry in feed_entries:
        if 'indicator' not in feed_entry or 'value' not in feed_entry:
            continue

        # Make the entry dict.
        entry = feed_entry.copy()
        entry['splunk_source'] = name
        entry['splunk_last_seen'] = start

        data.append(entry)

    return data
