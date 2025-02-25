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

  $('.collapsable-header').click(function() {
    $(this).find('.toggle-symbol').toggleClass('collapsed-symbol expanded-symbol');
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

/**
 * Open tab of given id.
 */
function openTab(tabId) {
  // Open the tab
  let $tabAnchor = $('.nav-tabs a[href="#' + tabId + '"]');
  if ($tabAnchor.length === 0) {
    return
  }
  $tabAnchor.trigger('click');
}