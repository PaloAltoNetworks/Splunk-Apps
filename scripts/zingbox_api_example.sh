
# Types are vulnerability, alert, device,
# URL="https://$CUSTOMERID.iot.paloaltonetworks.com/pub/v4.0/$TYPE/list?customerid=$CUSTOMERID&key_id=$KEYID&access_key=$ACCESSKEY&filter_monitored=yes&pagelength=1000&offset=3000&detail=true"
URL="https://$CUSTOMERID.iot.paloaltonetworks.com/pub/v4.0/$TYPE/list?customerid=$CUSTOMERID&key_id=$KEYID&access_key=$ACCESSKEY&type=policy_alert&resolved=no&stime=2020-04-29T21:28Z&etime=now&pagelength=1000&sortdirection=desc&sortfield=date"
# 
curl --location --request GET $URL