// Function to deploy the modal.
function deployModal(title, message) {
  var htmlData = '<div class="modal fade" role="dialog" tabindex="-1" id="pan_message"> \
  <div class="modal-dialog" role="document"> \
  <div class="modal-content"> \
  <div class="modal-header"> \
  <h3 class="modal-title">' + title + '</h3> \
  </div> \
  <div class="modal-body"> \
  ' + message + ' \
  </div> \
  <div class="modal-footer"> \
  <button type="button" class="btn btn-default" data-dismiss="modal" id="ta_check_close">Close</button> \
  </div> \
  </div> \
  </div>';

  $('body').append(htmlData);
  $('#pan_message').modal('show');
}
require([
  'underscore',
  'jquery',
  'splunkjs/mvc',
  'splunkjs/mvc/simplexml/ready!'
], function (
  mvc,
  ignored,
  _,
  $
  ) {
  // Get Required TA version
  var dependencyVersion;
  var checkTA = sessionStorage.checked_ta;
  var service = mvc.createService();
  var i;

  // Only check if the TA is install once per a session.
  if (!checkTA) {
    $.ajax({
      url: '/en-US/splunkd/__raw/servicesNS/admin/SplunkforPaloAltoNetworks/configs/conf-app/install',
      data: {
        output_mode: 'json'
      },
      type: 'GET',
      dataType: 'json'
    }).done(function (response) {
      for (i = 0; i < response.entry.length; i += 1) {
        dependencyVersion = response.entry[i].content.ta_dependency_version;
      }
    });

    service.apps()
    .fetch(function (err, apps) {
      var title;
      var message;
      var paloaltoTA = apps.item('Splunk_TA_paloalto');
      var looseVersion;
      if (err) {
        console.error(err);
        return;
      }

      // Check if the Add-on is installed.
      if (!paloaltoTA) {
        title = 'Missing Add-on';
        message = '<p>Please install the <a href="https://splunkbase.splunk.com/app/2757/" target="_blank">Palo Alto Networks Add-on</a>.</p><p>For more information please view the <a href="http://splunk.paloaltonetworks.com/installation.html" target="_blank">getting started documentation</a>.</p>';
        // TA is not installed.
        deployModal(title, message);
        sessionStorage.checked_ta = 1;
      } else {
        // TA is installed
        // Check the version to see if it matches dependency.
        looseVersion = paloaltoTA._properties.version;
        if (dependencyVersion === undefined || looseVersion === undefined) {
          // Unable to get dependencyVersion for some reason.
          // Adding to session storage to not check the TA anymore.
          console.log('Unable to get dependency/loose version.');
        } else if (looseVersion >= dependencyVersion) {
          // Everything passed. Adding to session storage to not check the TA anymore.
          sessionStorage.checked_ta = 1;
        } else if (looseVersion < dependencyVersion) {
          // Add-on filed to match. Adding to session storage to not check the TA anymore.
          title = 'Add-on Dependency Warning';
          message = '<p>The current verison of the Palo Alto Networks Add-on you have installed does not match the required version needed for this app. </p>\
            <p>Installed version: ' + looseVersion + '</p> \
            <p>The version required is: ' + dependencyVersion + '</p> \
            <p>Please download the required version from <a href="https://splunkbase.splunk.com/app/2757/" target="_blank">Splunk Base</a></p>';
          // Display modal
          deployModal(title, message);
          sessionStorage.checked_ta = 1;
        } else {
          // Catch all if something fails. Check once and don't display modal.
          console.log('Unable to check if add-on matches.');
          sessionStorage.checked_ta = 1;
        }
      }
    });
  }
});
