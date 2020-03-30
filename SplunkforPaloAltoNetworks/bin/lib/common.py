#!/usr/bin/env python

# Copyright (c) 2015, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Brian Torres-Gil <btorres-gil@paloaltonetworks.com>

"""Common functions used by all custom searchbar commands"""

import os
import sys
import traceback
import json

from environment import run_by_splunk

'''Import different logging library depending if
script was run by Splunk or on cli'''
if run_by_splunk():
    import splunk.Intersplunk
    import splunk.mining.dcutils as logging
    import splunk.entity as entity  # for splunk config info
    from splunk import ResourceNotFound
    logger = logging.getLogger()
else:
    import logging
    # python 2.6 doesn't have a null handler, so create it
    if not hasattr(logging, 'NullHandler'):
        class NullHandler(logging.Handler):
            def emit(self, record):
                pass
        logging.NullHandler = NullHandler

    # set logging to nullhandler to prevent exceptions if logging not enabled
    logging.getLogger().addHandler(logging.NullHandler())
    logger = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    logger.addHandler(ch)
    formatter = logging.Formatter('%(asctime)s - %(name)s \
                                  - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)


libpath = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(libpath)]
sys.path[:0] = [os.path.join(libpath, 'pan-python', 'lib')]
sys.path[:0] = [os.path.join(libpath, 'pandevice')]
try:
    import pandevice.base
except Exception as e:
    logger.error(str(e))
    sys.exit(4)


'''This is the folder name for the app and not
the app's common name (ie. "Splunk_TA_paloalto")'''
APPNAME = 'Splunk_TA_paloalto'


class NoCredentialsFound(Exception):
    pass


def get_firewall_credentials(session_key):
    """Given a splunk session_key returns a clear text user name
    and password from a splunk password container"""
    try:
        # Get all credentials
        logger.debug("Getting firewall credentials from Splunk")
        entities = entity.getEntities(['admin', 'passwords'],
                                      namespace=APPNAME, owner='nobody',
                                      sessionKey=session_key)

        accounts = entity.getEntities(['admin', 'Splunk_TA_paloalto_account'],
                                      namespace=APPNAME, owner='nobody',
                                      sessionKey=session_key)
    except Exception as e:
        exit_with_error("Could not get %s credentials from splunk. \
                         Error: %s" % (APPNAME, str(e)))
    # Check for username and passwords
    for i, c in accounts.items():
        if i.lower() == 'firewall' or i.lower() == 'panorama':
            username = accounts[i]['username']

    for i, c in entities.items():
        if c['username'] == 'Firewall``splunk_cred_sep``1':
            logger.debug('Match found for firewall credentials')
            clear_password = json.loads(c['clear_password'])
            password = clear_password['password']

    if username and password:
        logger.debug('Credentials have been found')
        return username, password
    else:
        raise NoCredentialsFound("No credentials have been found")


def get_wildfire_apikey(session_key):
    """Given a splunk session_key returns a clear
    text API Key from a splunk password container"""
    try:
        logger.debug("Getting wildfire apikey from Splunk")
        entities = entity.getEntities(['admin', 'passwords'],
                                      namespace=APPNAME, owner='nobody',
                                      sessionKey=session_key)
    except Exception as e:
        entities = {}
        exit_with_error("Could not get %s credentials from splunk."
                        "Error: %s" % (APPNAME, str(e)))
    try:
        clear_password = json.loads(entities['__REST_CREDENTIAL__#Splunk_TA_paloalto#configs/conf-splunk_ta_paloalto_settings:additional_parameters``splunk_cred_sep``1:']['clear_password'])
        api_key = clear_password['wildfire_api_key']
        logger.debug('WildFire API key exists')
        return api_key
    except KeyError:
        logger.info(
            "There are Palo Alto Networks WildFire malware events, "
            "but no WildFire API Key found, please set the API key "
            "in the Splunk_TA_paloalto Add-on Configuration dashboard.")
        exit_with_error("No WildFire API key is set, "
                        "set apikey in Add-on configuration.",
                        log_error=False,
                        log_traceback=False)
    except (ValueError, TypeError):
        exit_with_error("Problem getting WildFire API Key from JSON returned by Splunk password API")


def get_firewall_apikey(session_key):
    """Given a splunk session_key returns a clear
    text API Key from a splunk password container"""
    try:
        entities = entity.getEntities(['admin', 'passwords'],
                                      namespace=APPNAME, owner='nobody',
                                      sessionKey=session_key)

    except Exception as e:
        exit_with_error("Could not get %s credentials from splunk. "
                        "Error: %s" % (APPNAME, str(e)))

    for i, c in entities.items():
        if c['username'] == 'firewall_api_key':
            return c['clear_password']
    raise NoCredentialsFound


def set_firewall_apikey(session_key, apikey):
    """Given a splunk session_key sets the firewall API
    key in the Splunk password store"""
    try:
        '''The password cannot be modified, so it
        must be deleted before it can be added back.'''
        delete_firewall_apikey(session_key)
        apikey = {'name': 'firewall_api_key', 'password': apikey}
        apikey_entity = entity.Entity(['admin', 'passwords'],
                                      "firewall_api_key", namespace=APPNAME,
                                      owner='nobody', contents=apikey)
        entity.setEntity(apikey_entity, sessionKey=session_key,
                         strictCreate=False)
    except Exception as e:
        stack = traceback.format_exc()
        logger.warn(stack)
        logger.warn("entity exception")
        exit_with_error("Could not set %s firewall apikey"
                        "from splunk. Error: %s" % (APPNAME, str(e)))


def delete_firewall_apikey(session_key):
    """Given a splunk session_key delete the
    firewall API key in the Splunk password store"""
    try:
        entity.deleteEntity(['admin', 'passwords'], ":firewall_api_key:",
                            namespace=APPNAME, owner='nobody',
                            sessionKey=session_key)
    except ResourceNotFound:
        pass
    except Exception as e:
        exit_with_error("Could not delete %s firewall apikey "
                        "from splunk. Error: %s" % (APPNAME, str(e)))


def apikey(sessionKey, hostname, debug=False):
    """Login to a Palo Alto Networks device (firewall or Panorama)
    Returns:
        The API key for the firewall or Panorama
    """
    try:
        # Get the API Key for the device or Panorama if Splunk knows it
        apikey = get_firewall_apikey(sessionKey)
        log(debug, "API Key found in Splunk credential store")
        return apikey
    except NoCredentialsFound:
        try:
            log(debug, "API Key was not in Splunk credential store")
            # If Splunk doesn't know the API Key,
            # get the username and password instead
            log(debug, "Getting credentials from Splunk credential store")
            fw_username, fw_password = get_firewall_credentials(sessionKey)
            # Use the username and password to determine the API key
            log(debug, "Getting API Key from firewall/Panorama")
            device = pandevice.base.PanDevice(hostname, fw_username,
                                              fw_password)
            apikey = device.api_key
            # Save the API key to the Splunk credential store inside the App
            log(debug, "Adding API Key to Splunk credential store")
            set_firewall_apikey(sessionKey, apikey)
            return apikey
        except NoCredentialsFound as e:
            exit_with_error("No Firewall/Panorama credentials for searchbar "
                            "command. Please set the username and password in "
                            "the App set up page.")
        except Exception as e:
            exit_with_error("Unable to get apikey from firewall: %s" % str(e))


def check_debug(arguments):
    # Enable debugging by passing 'debug=yes' as an argument of
    # the command on the Splunk searchbar.
    if 'debug' in arguments:
        if arguments['debug'] != "no" and arguments['debug'] != "false":
            logger.info("Debugging enabled")
            logger.setLevel(10)
            return True
    return False


def exit_with_error(e, errorcode=2, log_error=True, log_traceback=True):
    if log_traceback:
        logger.error(''.join(traceback.format_stack()))
    if log_error:
        logger.error(str(e))
    if run_by_splunk():
        splunk.Intersplunk.generateErrorResults(str(e))
    sys.exit(errorcode)


def add_firewall_cli_args(parser):
    # Palo Alto Networks related arguments
    fw_group = parser.add_argument_group('Palo Alto Networks')
    fw_group.add_argument('hostname', help="Hostname of firewall or Panorama")
    fw_group.add_argument('-s', '--fw-vsys', default="vsys1",
                          help="vsys on Firewall or Panorama")
    fw_group.add_argument('-u', '--username',
                          help="Username of firewall or Splunk")
    fw_group.add_argument('-p', '--password',
                          help="Password of firewall or Splunk")
    fw_group.add_argument('-c', '--splunk-creds', action='store_true',
                          help="Use firewall credentials stored in Splunk app")
    return parser


def log(debug, message):
    if debug:
        logger.info(message)
