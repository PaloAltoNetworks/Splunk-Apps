###########################################
# Version 0.2
# author: Brian Torres-Gil, based on monzy merza's PAN app scripts
# About this script:
# Triggered when a WildFire syslog indicates a file has been analyzed by WildFire.
# This script retrieves the WildFire data relating to that syslog from the WildFire
# cloud service API.
# Script's actions and warning messages are logged in $SPLUNK_HOME/var/log/splunk/python.log
############################################
############################################
# How to Use this script
# The script must be provided 3 things to retrieve an WildFire log from the cloud:
# 1.  An API Key. This is found at https://wildfire.paloaltonetworks.com
#   under 'My Account'.
# 2.  The file digest (MD5, SHA-1, or SHA256) of the file that produced the alert. This is in the syslog.
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
import splunk.Intersplunk # so you can interact with Splunk
import splunk.entity as entity # for splunk config info
import splunk.mining.dcutils as dcu
import urllib # for urllib.urlencode()
import urllib2 # make http requests to PAN firewall
import sys # for system params and sys.exit()
#import re # regular expressions checks in PAN messages
#import xml.etree.ElementTree as ET # for xml parsing
import traceback

def createOpener():
  '''Create a generic opener for http
  This is particularly helpful when there is a proxy server in line'''
  # Thanks to: http://www.decalage.info/en/python/urllib2noproxy
  proxy_handler = urllib2.ProxyHandler(HTTP_PROXY)
  opener = urllib2.build_opener(proxy_handler)
  urllib2.install_opener(opener)
  return opener

def getWildFireAPIKey(sessionKey):
  '''Given a splunk sesionKey returns a clear text API Key from a splunk password container'''
  # this is the folder name for the app and not the app's common name
  myapp = 'SplunkforPaloAltoNetworks'
  try:
    entities = entity.getEntities(['admin', 'passwords'], namespace=myapp, owner='nobody', sessionKey=sessionKey)
  except Exception, e:
    stack =  traceback.format_exc()
    logger.warn(stack)
    logger.warn("entity exception")
    raise Exception("Could not get %s credentials from splunk. Error: %s" % (myapp, str(e)))
  # return first set of credentials
  for i, c in entities.items():
    if c['username'] == 'wildfire_api_key':
      return c['clear_password']
  logger.warn("There are Palo Alto Networks WildFire malware events, but no WildFire API Key found, please set the API key in the SplunkforPaloAltoNetworks App set up page")
  raise Exception("No credentials have been found")

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
  result = opener.open(wfReq, post_data)
  return result

# setup the logger. $SPLUNK_HOME/var/log/splunk/python.log
logger = dcu.getLogger()

# an empty dictionary will be used to hold system values
settings = dict()
# results contains the data from the search results and settings contains the sessionKey that we can use to talk to splunk
results,unused1,settings = splunk.Intersplunk.getOrganizedResults()
#logger.info(settings) #For debugging
# get the sessionKey
sessionKey = settings['sessionKey']
# get the Panorama user and password from Splunk using the sessionKey
if len(results) > 0:
  PAN_WF_APIKEY = getWildFireAPIKey(sessionKey)

# get each row of result
for result in results:
  # check to see if the result has in ip field
  if result.has_key('file_digest') and result.has_key('report_id'):
    try:
      # get the report
      wfReportXml = retrieveWildFireData(PAN_WF_APIKEY, result['file_digest']).read().strip()
      # Add the file_digest to the XML for correlation to the original WildFire log from the firewall
      wfReportXml = wfReportXml.replace("</version>", "</version>\n<id>"+result['report_id']+"</id>", 1)
      result['wildfire_report'] = wfReportXml
    except:
      logger.warn("Error retrieving WildFire report for file digest: %s" % result['file_digest'])
      #log the result row in case of an exception
      logger.info(result)
      stack = traceback.format_exc()
      # log the stack information
      logger.warn(stack)
  else:
    logger.info("Required fields missing from command. Expected the following fields: file_digest")
# output the complete results sent back to splunk
splunk.Intersplunk.outputResults(results)
