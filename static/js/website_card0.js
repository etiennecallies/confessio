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

  // Listen for Bootstrap collapse events instead of clicks
  $('.collapse').on('shown.bs.collapse hidden.bs.collapse', function() {
    // Find the associated header and toggle the symbol
    $(this).prev('.collapsable-header').find('.toggle-symbol')
      .toggleClass('collapsed-symbol expanded-symbol');
  });
});

/**
 * Activate tooltips.
 */
$(window).on("load", function () {
  $('[data-toggle="tooltip"]').each(function() {
      // use data-html="true" to enable html in tooltips
      $(this).tooltip({html: $(this).data('html') || false});
  });
});

/**
 * Navigate to the church element.
 */
function goToChurch(websiteUuid, churchUuid, isChurchExplicitlyOther) {
  // Uncollapse the churches section.
  $('#churches-'+websiteUuid).collapse('show').on('shown.bs.collapse', function () {
      let $churchEl = churchUuid ? $('#church-' + churchUuid) : $('#nochurch-' + websiteUuid + '-' + isChurchExplicitlyOther);
      // Navigate to the church element
      if ($churchEl.length > 0) {
          $churchEl[0].scrollIntoView();
          animateElement($churchEl.first());
      } else {
          console.error('No church found for websiteUuid=' + websiteUuid + ' and churchUuid=' + churchUuid);
      }
  });
}

/**
 * Navigate to the parsing element.
 */
function goToParsing(websiteUuid, parsingUuid) {
    // Uncollapse the parsing section.
    $('#sources-'+websiteUuid).collapse('show').on('shown.bs.collapse', function () {
        let $parsingEl = $('#parsing-' + websiteUuid + '-' + parsingUuid);
        // Navigate to the parsing element
        if ($parsingEl.length > 0) {
            $parsingEl[0].scrollIntoView();
            animateElement($parsingEl.first());
        } else {
            console.error('No parsing found for websiteUuid=' + websiteUuid + ' and parsingUuid=' + parsingUuid);
        }
    });
}

function animateElement($element) {
    $element.css("background-color", "#f1f9fd");

    setTimeout(() => {
      $element.css("background-color", "");
    }, 1000); // Reset after 1000ms
}