/**
 * Handle expand/collapse of truncated html.
 */
$(document).ready(function () {
  // Listen for Bootstrap collapse events instead of clicks
  $('.collapse').on('shown.bs.collapse hidden.bs.collapse', function() {
    let $collapsableBody = $(this).find('.collapsable-body');
    if ($collapsableBody.data('lazy-load-url')) {
        lazyLoadElement($collapsableBody, null);
    }

    // Find the associated header and toggle the symbol
    $(this).prev('.collapsable-header').find('.toggle-symbol')
      .toggleClass('collapsed-symbol expanded-symbol');
  });
});

function lazyLoadElement($element, callback) {
    let url = $element.data("lazy-load-url");
    if (!url) {
        if (callback) callback();
        return;
    }

    // Add a loading spinner
    let loader = $('<div class="spinner-border text-info d-block mx-auto" role="status"><span class="sr-only">Loading...</span></div>');
    $element.html(loader);

    $.get(url, function(data) {
        $element.html(data);
        $element.data("lazy-load-url", '');
        if (callback) callback();
        setTimeout(function() {
            activateExpandable($element);
            activateToggleExplicitlyOther($element);
            activateCopyToClipboard($element);
            activateSeeChurchOnMap($element);
            activateNextButton($element);
            activatePreviousButton($element);
        }, 0)
    }).fail(function() {
        $element.html("<p>Une erreur est survenue...</p>");
    });
}

function activateExpandable($element) {
    $element.find('.expandable').on('click', function () {
        $(this).children('.expandable-item').toggle();
    });
}

function activateToggleExplicitlyOther($element) {
    // Handle mute/display explicitly other church
    $element.find('.hide-explicitly-other-btn').on('click', function() {
      let $this = $(this);
      $this.closest('.website-card').toggleClass('hide-explicitly-other');

      // Toggle text "afficher" / "masquer"
      $this.text($this.text() === 'Afficher' ? 'Masquer' : 'Afficher');
    });
}

function activateCopyToClipboard($element) {
    $element.find('.copy-to-clipboard').each(function () {
        $(this).click(function () {
            let content = $(this).prev().text();
            navigator.clipboard.writeText(content);
            $('<span> Copié!</span>').insertAfter(this).delay(2000).fadeOut();
        });
    });
}

function activateSeeChurchOnMap($element) {
    $element.find('.church-container').each(function () {
        let churchMarkerNames = $(this).closest('.churches-container').data('church-marker-names-json');
        let churchUuid = $(this).data('church-uuid');
        if (churchUuid in churchMarkerNames) {
            let churchMarkerName = churchMarkerNames[churchUuid];
            let $span = $(this).find('.church-name');
            let $newAnchor = $('<a href="#map" class="link-info" onclick="return popupChurch(\''+ churchMarkerName +'\');"></a>');
            $span.replaceWith($newAnchor.append($span.clone()));
        }
    });
}

function activateNextButton($element) {
    let $nextButton = $element.find('.next-button');
    if ($nextButton.length) {
        $nextButton.on('click', addEventOnNextButton);
    }
}

function activatePreviousButton($element) {
    let $previousButton = $element.find('.previous-button');
    if ($previousButton.length) {
        $previousButton.on('click', addEventOnPreviousButton);
    }
}

function addEventOnNextButton() {
    // Find the parent table-container
    const container = $(this).closest('.calendar-table-container');

    // Hide range-1 table and show range-2 table in this container
    container.find('.calendar-table.range-1').addClass('d-none');
    container.find('.calendar-table.range-2').removeClass('d-none');

    // Hide "Next" button and show "Previous" button in this container
    $(this).addClass('d-none');
    container.find('.previous-button').removeClass('d-none');
  }

function addEventOnPreviousButton() {
    // Find the parent table-container
    const container = $(this).closest('.calendar-table-container');

    // Hide range-2 table and show range-1 table in this container
    container.find('.calendar-table.range-2').addClass('d-none');
    container.find('.calendar-table.range-1').removeClass('d-none');

    // Hide "Previous" button and show "Next" button in this container
    $(this).addClass('d-none');
    container.find('.next-button').removeClass('d-none');
}

function loadMoreEvents($element) {
    let $eventContainer = $element.closest('.website-event-container');
    lazyLoadElement($($eventContainer), null);
}

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
    let $websiteChurches = $('#churches-'+websiteUuid);
    let $collapsableBody = $websiteChurches.find('.collapsable-body');
    let elementId = churchUuid ? ('church-' + churchUuid) : ('nochurch-' + websiteUuid + '-' + isChurchExplicitlyOther);
    lazyLoadElement($collapsableBody, function () {
        uncollapseAndNavigateToElement($websiteChurches, elementId);
    });
}

/**
 * Navigate to the parsing element.
 */
function goToParsing(websiteUuid, parsingUuid) {
    let $websiteSource = $('#sources-'+websiteUuid);
    let $collapsableBody = $websiteSource.find('.collapsable-body');
    let elementId = 'parsing-' + websiteUuid + '-' + parsingUuid;
    lazyLoadElement($collapsableBody, function () {
        uncollapseAndNavigateToElement($websiteSource, elementId);
    });
}

/**
 * Navigate to the OClocher element.
 */
function goToOclocher(websiteUuid) {
    let $websiteSource = $('#sources-'+websiteUuid);
    let $collapsableBody = $websiteSource.find('.collapsable-body');
    let elementId = 'oclocher-' + websiteUuid;
    lazyLoadElement($collapsableBody, function () {
        uncollapseAndNavigateToElement($websiteSource, elementId);
    });
}

function uncollapseAndNavigateToElement($collapseElement, elementId) {
    if ($collapseElement.length && !$collapseElement.hasClass('show')) {
        $collapseElement.collapse('show').one('shown.bs.collapse', function () {
            navigateToElement(elementId);
        });
    } else {
        navigateToElement(elementId);
    }
}

function navigateToElement(elementId) {
    let $element = $('#' + elementId);
    if ($element.length > 0) {
        $element[0].scrollIntoView();
        animateElement($element.first());
    } else {
        console.error('No element found with id=' + elementId);
    }
}

function animateElement($element) {
    $element.css("background-color", "#f1f9fd");

    setTimeout(() => {
      $element.css("background-color", "");
    }, 1000); // Reset after 1000ms
}

/**
 * Handle date range selection.
 */
$(document).ready(function() {
  // Handle "Next" button click
  $(".next-button").click(addEventOnNextButton);

  // Handle "Previous" button click
  $(".previous-button").click(addEventOnPreviousButton);
});