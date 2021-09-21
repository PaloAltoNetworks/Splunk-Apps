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
], function (_, $, mvc) {
  var tooltipIcon = $('<i class="icon-info-circle tooltip_icon"></i>');
  tooltipIcon.appendTo('.dashboard-title');
  tooltipIcon.show();
  tooltipIcon.click(function() {
    var message = $('#tooltip_txt').html();
    var title = $('#tooltip_title');
    if (title.length) {
        title = title.text()
    } else {
        title = 'Dashboard Information';
    }
    deployModal(title, message);
  });
});
