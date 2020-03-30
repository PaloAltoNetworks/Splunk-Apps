# This script takes the following GET params:
#   * pid: A pcap ID
#   * host: The hostname of the device to get the pcap from
#   * stime: The search_time window, formatted as YYYY/MM/DD HH:MM:SS
#   * serial: Optional.  Serial number of the firewall if host is panorama

import os
import sys

libpath = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(libpath, 'lib')]
sys.path[:0] = [os.path.join(libpath, 'lib', 'pan-python', 'lib')]
sys.path[:0] = [os.path.join(libpath, 'lib', 'pandevice')]

import time
import common
import json
import splunk
import splunk.mining.dcutils as dcu

import pandevice.base
import pandevice.panorama
import pandevice.firewall

logger = dcu.getLogger()


class Cfg(object):
    """Config is a separate object for testing purposes."""
    def __init__(self):
        self.skey = None
        self.hostname = None
        self.search_time = ''
        self.serial = None
        self.pcap_id = 0
        self.api_key = None

    def parse(self, skey, req):
        # Initialize all config.
        self.skey = skey

        #sc = common.SplunkConnector(self.skey, logger)
        self.hostname = req['query']['host']
        self.search_time = req['query']['stime']
        self.serial = req['query'].get('serial', None)
        self.pcap_id = req['query']['pid']
        if self.pcap_id <= 0:
            raise ValueError('{0} is not a valid pcap ID'.format(self.pcap_id))

        self.api_key = common.apikey(self.skey, self.hostname)


class MasterP(splunk.rest.BaseRestHandler):
    def handle_GET(self):
        # Get and process query params.
        logger.info('Initiated pcap retrieval, parsing request config')
        cfg = Cfg()
        cfg.parse(self.sessionKey, self.request)

        # Connect to the firewall / panorama.
        logger.info('Creating connection object for given hostname')
        o = pandevice.base.PanDevice.create_from_device(
            cfg.hostname, api_key=cfg.api_key)

        # Set the serial target (if present and this is a panorama).
        if isinstance(o, pandevice.panorama.Panorama):
            if not cfg.serial:
                raise ValueError('Host is panorama, serial number is required')
            logger.info('This is a panorama device, creating sub-object')
            dev = pandevice.firewall.Firewall(serial=cfg.serial)
            o.add(dev)
        else:
            dev = o

        # Retrieve the pcap file.
        logger.info('Retrieving pcap file')
        dev.xapi.export(
            'threat-pcap', search_time=cfg.search_time, pcapid=cfg.pcap_id)
        if not dev.xapi.export_result or not dev.xapi.export_result['content']:
            raise ValueError('File not present or file is empty')

        # Send pcap to the user.
        self.response.setHeader('Content-Type', 'application/vnd.tcpdump.pcap')
        self.response.write(dev.xapi.export_result['content'])
        logger.info('Done')
