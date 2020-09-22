$(document).ready(function () {
  'use strict';

  // Function to remove Firewall Api Key
  function removeFirewallAPIKey() {
    $.ajax({
      url: '/en-US/splunkd/__raw/servicesNS/-/Splunk_TA_paloalto/storage/passwords/%3Afirewall_api_key%3A',
      type: 'DELETE',
      statusCode: {
      404: function() {
        console.log( "API key not found." );
      }
  }
    }).success(function () {
      console.log('Firewall API Key Deleted.');
    }).error(function () {
      console.log('Error deleting Firewall API key.');
    }).done(function () {
      console.log('Finished removeFirewallAPIKey')
    });
  }
  console.log('Lets delete something')

  removeFirewallAPIKey();
});

