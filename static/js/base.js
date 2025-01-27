/**
 * Handle close alert on dismissible alert.
 */
$(document).ready(function () {
  $('.alert-dismissible .close').click(function () {
    $(this).closest('.alert-dismissible').alert('close');
  });
});


