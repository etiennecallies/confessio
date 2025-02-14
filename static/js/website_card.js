/**
 * Copy to clipboard.
 */
$(document).ready(function () {
    $('.copy-to-clipboard').each(function () {
        $(this).click(function () {
            let content = $(this).prev().text();
            navigator.clipboard.writeText(content);
            $('<span> Copié!</span>').insertAfter(this).delay(2000).fadeOut();
        });
    });
});

/**
 * Handle expand/collapse of truncated html.
 */
$(document).ready(function () {
  $('.expandable').on('click', function () {
    $(this).children('.expandable-item').toggle();
  });
});

/**
 * Activate tooltips.
 */
$(window).on("load", function () {
  $('[data-toggle="tooltip"]').each(function() {
      $(this).tooltip({html: $(this).data('html') || false});
  });
});