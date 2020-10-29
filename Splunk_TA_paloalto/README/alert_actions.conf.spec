
[pantag]
python.version = python3
param.verbose = <bool>
    * Set modular alert action logger to verbose mode
    * Defaults to "false"
param._cam = <json> Active response parameters.
param.device = <string> Firewall. It's a required parameter.
param.action = <list> Action. It's a required parameter.
param.tag = <string> Tags. It's a required parameter.

[panwildfiresubmit]

param.verbose = <bool>
    * Set modular alert action logger to verbose mode
    * Defaults to "false"

param._cam = json
    * Prevent splunk startup and btool from erroring
