from __future__ import print_function
import sys
import gzip
import csv
import json
import logging
import logging.handlers
import traceback

# CORE SPLUNK IMPORTS (not needed)
# import splunk
# import splunk.search as splunkSearch
# from splunk.rest import simpleRequest
# import splunk.version as ver
# import splunk.clilib.cli_common
# import splunk.auth, splunk.search
# import splunk.Intersplunk as si

try:
    from splunk.clilib.bundle_paths import make_splunkhome_path
except ImportError:
    from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path

sys.path.append(make_splunkhome_path(["etc", "apps", "Splunk_SA_CIM", "lib"]))
sys.path.append(make_splunkhome_path(["etc", "apps", "SA-Utils", "lib"]))
sys.path.append(make_splunkhome_path(["etc", "apps", "Splunk_TA_paloalto", "bin", "lib"]))
sys.path.append(make_splunkhome_path(["etc", "apps", "Splunk_TA_paloalto", "bin", "lib", "pan-python", "lib"]))
sys.path.append(make_splunkhome_path(["etc", "apps", "Splunk_TA_paloalto", "bin", "lib", "pandevice"]))

from cim_actions import ModularAction
import common
from pandevice.firewall import Firewall

# set the maximum allowable CSV field size
#
# The default of the csv module is 128KB; upping to 10MB. See SPL-12117 for
# the background on issues surrounding field sizes.
# (this method is new in python 2.5)
csv.field_size_limit(10485760)

# Default fields that contain IP addresses and should be tagged if they exist
IP_FIELDS = ['src_ip', 'dest_ip', 'ip']
USER_FIELDS= ['src_user', 'dest_user', 'user']

##
## Debugging : index=_internal (source=*_modalert.log* OR source=*_modworkflow.log*)

## ModularAction wrapper
class PantagModularAction(ModularAction):

    def __init__(self, settings, logger, action_name=None):
        super(PantagModularAction, self).__init__(settings, logger, action_name)

        self.connector = common.SplunkConnector(self.session_key, self.logger)

        self.verbose = self.configuration.get('verbose', 'false') in ["True", "true", "yes", "on"]
        self.device = self.configuration.get('device', '')
        self.action = self.configuration.get('action', 'addip')
        self.tag = self.configuration.get('tag', '')
        self.resultcount = 0

        self.logger.debug("verbose = %s", self.verbose)
        self.logger.debug("action = %s", self.action)
        self.logger.debug("device = %s", self.device)
        self.logger.debug("tag = %s", self.tag)

        # Parse the tags into a list
        self.tags = [x.strip() for x in self.tag.split(',')]

        # Place holder for firewall instance
        self.firewall = None

    def start(self):
        # Get/Generate the firewall API key from the credentials stored in Splunk
        if self.firewall is None:
            apikey = self.connector.apikey(self.device)
            # Perform the tagging operation on the firewall
            self.firewall = Firewall(self.device, api_key=apikey)
            self.firewall.userid.batch_start()

    def end(self):
        if self.firewall is None:
            return
        self.firewall.userid.batch_end()
        # Track the final state
        action = "Register" if self.action in ("add", "adduser", "addip") else "Unregister"
        modaction.message("%s PANTag on %s - Results: %s - Tags: %s"
                          % (action, self.device, str(self.resultcount), self.tags),
                          status='success',
                          rids=self.rids
                          )

    def apply(self, result):

        # Extract the User/IP that needs to be tagged
        if self.action in ("adduser", "removeuser"):
            FIELDS = USER_FIELDS
        else:
            FIELDS = IP_FIELDS
        extracted_field = None

        for field in FIELDS:
            if field in result:
                extracted_field = result[field]
                break

        # Couldn't find a extracted field with username/ip
        if extracted_field is None:
            modaction.message('Unable to find field to tag', status='failure', rids=self.rids, level=logging.ERROR)
            return

        if self.action in ("add", "addip"):
            self.logger.debug("Registering tags on firewall %s: %s - %s" % (self.device, extracted_field, self.tags))
            self.firewall.userid.register(extracted_field, self.tags)
        elif self.action in ("remove", "removeip"):
            self.logger.debug("Unregistering tags on firewall %s: %s - %s" % (self.device, extracted_field, self.tags))
            self.firewall.userid.unregister(extracted_field, self.tags)
        elif self.action == "adduser":
            self.logger.debug("Registering tags on firewall %s: %s - %s" % (self.device, extracted_field, self.tags))
            self.firewall.userid.tag_user(extracted_field, self.tags)
        elif self.action == "removeuser":
            self.logger.debug("Unregistering tags on firewall %s: %s - %s" % (self.device, extracted_field, self.tags))
            self.firewall.userid.untag_user(extracted_field, self.tags)
        else:
            self.logger.error("Unknown action. Please use addip|removeip|adduser|removeuser")

        self.resultcount += 1



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--execute":
        print("FATAL Unsupported execution mode (expected --execute flag)", file=sys.stderr)
        sys.exit(1)

    logger = ModularAction.setup_logger('pantag_modalert')
    try:
        modaction = PantagModularAction(sys.stdin.read(), logger, 'pantag')
        session_key = modaction.session_key
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('%s', json.dumps(modaction.settings, sort_keys=True,
                indent=4, separators=(',', ': ')))

        ## process results
        with gzip.open(modaction.results_file, 'rt') as fh:
            for num, result in enumerate(csv.DictReader(fh)):
                modaction.start()
                ## set rid to row # (0->n) if unset
                result.setdefault('rid', str(num))
                modaction.update(result)
                modaction.invoke()
                modaction.apply(result)
        modaction.end()

    except Exception as e:
        ## adding additional logging since adhoc search invocations do not write to stderr
        try:
            logger.critical(traceback.format_exc())
            logger.critical(modaction.message(e, 'failure'))
        except:
            logger.critical(e)
            traceback.print_exc(file=sys.stderr)
        print("ERROR Unexpected error: %s" % e, file=sys.stderr)
        sys.exit(3)
