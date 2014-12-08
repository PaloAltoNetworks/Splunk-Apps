###########################################
# Version 0.1 
# author: Brian Torres-Gil, based on monzy merza's PAN app scripts
# About this script:
#   Triggered when a WildFire syslog indicates a file has been analyzed by WildFire.
#   This script retrieves the WildFire data relating to that syslog from the WildFire
#   cloud service API.
#   Script's actions and warning messages are logged in $SPLUNK_HOME/var/log/splunk/python.log
############################################
############################################
# How to Use this script
# The script must be provided 2 things to retrieve an WildFire log from the cloud:
#   1.  An API Key. This is found at https://wildfire.paloaltonetworks.com
#       under 'My Account'.
#   2.  The file digest (MD5, SHA-1, or SHA256) of the file that produced the alert. This is in the syslog.
###########################################
###########################################
# These are the default values.  You can modify these on the CLI using arguments.
# (except for the HTTP_PROXY)
# Your API Key. Found at https://wildfire.paloaltonetworks.com under 'My Account'
APIKEY = ''
# File Digest of the file in MD5, SHA-1, or SHA256
HASH = ''
# if you DO want to go through a proxy, e.g., HTTP_PROXY={squid:'2.2.2.2'}
HTTP_PROXY = {}
#########################################################
# Do NOT modify anything below this line unless you are 
# certain of the ramifications of the changes
#########################################################
#import splunk.Intersplunk # so you can interact with Splunk
#import splunk.entity as entity # for splunk config info
#import splunk.mining.dcutils as dcu
import urllib # for urllib.urlencode()
import urllib2 # make http requests to PAN firewall
import sys # for system params and sys.exit()
import re # regular expressions checks in PAN messages
import xml.etree.ElementTree as ET # for xml parsing
import traceback
import optparse # for option parsing TODO: may not be needed in final script?

def createOpener():
  '''Create a generic opener for http
  This is particularly helpful when there is a proxy server in line'''
  # Thanks to: http://www.decalage.info/en/python/urllib2noproxy
  proxy_handler = urllib2.ProxyHandler(HTTP_PROXY)
  opener = urllib2.build_opener(proxy_handler)
  urllib2.install_opener(opener)  
  return opener

def retrieveWildFireData(apikey, hash):
  # Create a urllib2 opener
  opener = createOpener()
  # URL for WildFire cloud API
  # https://www.paloaltonetworks.com/documentation/61/wildfire/wf_admin/section_6/chapter_4.html
  wfUrl = 'https://wildfire.paloaltonetworks.com/publicapi/get/report'
  # Prepare the variables as POST data
  post_data = urllib.urlencode({
    'apikey' : apikey,
    'hash' : hash,
  })
  # Create a request object
  wfReq = urllib2.Request(wfUrl)
  # Make the request to the WildFire cloud
  try:
    result = opener.open(wfReq, post_data)
  except:
    stack = traceback.format_exc()
    print "Error retrieving WildFire report"
    print stack
    sys.exit(-1)
  return result

def main(argv = sys.argv):
  '''Received parameters from the command line'''
  # setup the option parser
  parser = optparse.OptionParser()
  parser.add_option('-K', '--apikey', dest="APIKEY", default=APIKEY, help="API Key from https://wildfire.paloaltonetworks.com")
  parser.add_option('-H', '--hash', dest="HASH", default=HASH, help="File Digest of the file in MD5, SHA-1, or SHA256")

  options, remainder = parser.parse_args()

  # Grab WildFire data
  data = retrieveWildFireData(options.APIKEY, options.HASH)

  # Parse XML for fields
  print data.read()

  return 0


if __name__ == "__main__":
    main()
