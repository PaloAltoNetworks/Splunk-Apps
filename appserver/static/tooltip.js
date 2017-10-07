require([
  'splunkjs/mvc',
  'underscore',
  'jquery',
], function (
  mvc,
  _,
  $) {
  $('.tooltip_icon').appendTo('.dashboard-title');
  $('.tooltip_icon').show();
  $('.tooltip_icon').click(function() {
    var message = $('#tooltip_txt').text();
    deployModal('Dashboard Information', message);
  });
});
