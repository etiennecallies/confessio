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
