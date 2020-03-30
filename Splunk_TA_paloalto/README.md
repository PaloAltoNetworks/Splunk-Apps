
Palo Alto Networks Add-on for Splunk
====================================

* **Add-on Homepage:** https://splunkbase.splunk.com/app/2757
* **Authors:** Brian Torres-Gil, Paul Nguyen, Garfield Freeman - Palo Alto Networks
* **Add-on Version:** 6.2.0

### Description ###
 
The Palo Alto Networks Add-on for Splunk allows a Splunk® Enterprise
or Splunk Cloud administrator to collect data from Palo Alto Networks
Next-Generation Firewall devices and Advanced Endpoint Protection. The
add-on collects traffic, threat, system, configuration, and endpoint logs
from Palo Alto Networks physical or virtual firewall devices over syslog.
After Splunk indexes the events, you can consume the data using the
pre-built dashboard panels included with the add-on, with Splunk Enterprise
Security, or with the Palo Alto Networks App for Splunk. This add-on
provides the inputs and CIM-compatible knowledge to use with other Splunk
Enterprise apps, such as the Splunk App for Enterprise Security and the
Splunk App for PCI Compliance, and integrates with Splunk Adaptive Response.

Documentation for this add-on is located at: http://splunk.paloaltonetworks.com/

### Documentation ###

**Installation and Getting Started:** http://splunk.paloaltonetworks.com/getting_started.html  
**Release Notes:** http://splunk.paloaltonetworks.com/release-notes.html  
**Support:** http://splunk.paloaltonetworks.com/support.html

### Install from Git ###

This app is available on [Splunkbase](http://splunkbase.splunk.com/app/2757)
and [Github](https://github.com/PaloAltoNetworks/Splunk_TA_paloalto).
Optionally, you can clone the github repository to install the app.

From the directory `$SPLUNK_HOME/etc/apps/`, type the following command:

    git clone https://github.com/PaloAltoNetworks/Splunk_TA_paloalto.git Splunk_TA_paloalto
    
### Libraries Included ###

**Pan-Python:** [Github] (https://github.com/kevinsteves/pan-python)  
**PanDevice:** [Github] (https://github.com/PaloAltoNetworks/pandevice)

Copyright (C) 2014-2020 Palo Alto Networks Inc. All Rights Reserved.