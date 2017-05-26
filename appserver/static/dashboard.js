require.config({
  baseUrl: "{{SPLUNKWEB_URL_PREFIX}}/static/js",
  // waitSeconds: 0 // Disable require.js load timeout
});

  var splunk_libraries = [
    "jquery"
  ]
  var splunk_function = function (
    $
    ){ 
      console.log("in dashboard.js");
      // sessionKey = settings.get("sessionKey", None);
      var ignore_TA = localStorage.ignore_ta
      console.log(ignore_TA);

      if(!ignore_TA) {
        console.log("They didn't want to ignore me so lets check if they seen the modal this session.");
        var check_TA = sessionStorage.checked_ta
      } else {
        console.log("looks like they want to ignore me");
        var check_TA = 1;
      }
      console.log(check_TA);

      if (!check_TA) {
        console.log("inside ta_check");
        var xhttp = new XMLHttpRequest();
        xhttp.open("GET", "https://localhost:8089/services/apps/local/Splunk_TA_paloalto", true);
        xhttp.send();
        console.log(xhttp.responseText);

        // $.ajax({
        //   url: 'http://localhost:8089/services/apps/local',
        //   data: 'output_mode=json',
        //   dataType: 'json',
        //   success: function(data){
        //     console.log('success',data);
        //   }
        // });
        // sessionStorage.checked_ta = 1;

        var htmlData = '<div class="modal fade" role="dialog" tabindex="-1" id="pan_message"> \
        <div class="modal-dialog" role="document"> \
          <div class="modal-content"> \
            <div class="modal-header"> \
              <h4 class="modal-title">  <span class="glyphicon glyphicon-star" aria-hidden="true"></span> Missing Add-on. </h4> \
            </div> \
            <div class="modal-body"> \
              <p>Please install the <a href="https://splunkbase.splunk.com/app/2757/" target="_blank">Palo Alto Networks Add-on</a>.</p> \
              <!-- <input type="checkbox" id="ignore_ta_check" /> I understand the TA is not installed. Don\'t show me this again. --> \
            </div> \
            <div class="modal-footer"> \
              <button type="button" class="btn btn-default" data-dismiss="modal" id="ta_check_close">Close</button> \
            </div> \
          </div> \
        </div>';
        
        $( "body" ).append(htmlData);
        $( "#pan_message" ).modal('show');
      }

      $( "#ta_check_close" ).click(function() {
        ignore_ta_check = $('#ignore_ta_check').is(":checked");
        if(ignore_ta_check === true) {
          console.log("yes its checked");
          localStorage.ignore_ta = 1;
        } 
      });

      console.log("done dashboard.js");
    }; //end splunk function
//return our renderer
require(splunk_libraries, splunk_function);