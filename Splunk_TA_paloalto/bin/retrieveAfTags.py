# Logs are written to $SPLUNK_HOME/var/log/splunk/python.log

import os
import sys

libpath = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(libpath, 'lib')]
sys.path[:0] = [os.path.join(libpath, 'lib', 'pan-python', 'lib')]

import common
import functools
import itertools
import json
import requests
import splunk.Intersplunk
import splunk.mining.dcutils as dcu
import splunk.rest
import time

import pan.afapi


logger = dcu.getLogger()
MAX_PAGE_SIZE = 200


def main():
    logger.info('START AutoFocus tag retrieval')

    # Init.
    results, dummy, settings = splunk.Intersplunk.getOrganizedResults()
    skey = settings['sessionKey']
    connector = common.SplunkConnector(skey, logger)
    apikey = connector.get_autofocus_apikey()
    stats = {
        'daily_points': 0,
        'daily_points_remaining': 0,
        'tags': 0,
    }

    # Retrieve all tags from AutoFocus.
    try:
        all_tags = pull_tags(apikey, stats)
    except Exception as e:
        logger.error('Exception in pull_tags: {0}'.format(e))
        all_tags = []
    stats['tags'] = len(all_tags)

    # Delete old entries from the kvstore.
    delete_from_kvstore(all_tags, skey, stats)

    # Save new entries to the kvstore.
    save_to_kvstore(all_tags, skey, stats)

    # Done.
    # | panautofocustags | collect index=default source="panautofocustags" sourcetype="autofocus"
    splunk.Intersplunk.outputResults([stats, ])
    logger.info('END AutoFocus tag retrieval')


def timer(desc):
    def outer(func):
        @functools.wraps(func)
        def inner(*args):
            """Decorator to time function execution.

            The final argument to any function decorated with this decorator
            should be a dictionary.  The timing of the decorated function is
            then saved as a difference of time.time() values into the dict,
            using "desc" as the dict key.

            If an exception is raised during the function, then a time of "-1"
            will be saved for the given description.

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


@timer('retrieve_tags')
def pull_tags(apikey, stats):
    logger.info('Retrieving tag metadata')
    c = pan.afapi.PanAFapi(
        api_key=apikey, hostname='autofocus.paloaltonetworks.com')

    bucket_keys = (
        'daily_points',
        'daily_points_remaining')
    all_tags = []
    counter = itertools.count()
    while True:
        req = {'pageSize': MAX_PAGE_SIZE, 'pageNum': counter.next()}

        # Perform the operation
        r = c.tags(data=json.dumps(req))

        # Update stats
        for key in bucket_keys:
            if stats[key] != r.json['bucket_info'][key]:
                stats[key] = r.json['bucket_info'][key]

        # Save the tags
        all_tags.extend(r.json['tags'])

        # Done if we didn't get MAX_PAGE_SIZE tags.
        if len(r.json['tags']) < MAX_PAGE_SIZE:
            break

    # Normalize the autofocus fields by adding a prefix of "aftag:".
    normalized = []
    for elm in all_tags:
        d = {}
        for k, v in elm.items():
            d['aftag:{0}'.format(k)] = v
        normalized.append(d)

    return normalized


@timer('clear_kvstore')
def delete_from_kvstore(all_tags, skey, stats):
    if not all_tags:
        logger.info('No tags retrieved, skipping kvstore clear')
        return

    logger.info('Deleting tag metadata from kvstore')
    requests.delete(_uri(), headers=_headers(skey), verify=False)


@timer('save_to_kvstore')
def save_to_kvstore(all_tags, skey, stats):
    logger.info('Saving metadata to kvstore')
    for i in range(0, len(all_tags), 500):
        requests.post(
            _uri() + '/batch_save',
            data=json.dumps(all_tags[i:i+500]),
            headers=_headers(skey),
            verify=False)


def _uri():
    """Returns the URL of the kvstore."""
    return '/'.join((
        splunk.rest.makeSplunkdUri().rstrip('/'),
        'servicesNS',
        'nobody',
        'Splunk_TA_paloalto',
        'storage',
        'collections',
        'data',
        'autofocus_tags'))


def _headers(skey):
    """Returns the auth header for Splunk."""
    return {
        'Authorization': 'Splunk {0}'.format(skey),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


if __name__ == '__main__':
    main()
