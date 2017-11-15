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
