/*
 * Open popup on map.
 * Does not require JQuery.
 */
function popupChurch(markerName){
    document.getElementById("map-iframe").contentWindow[markerName].openPopup();
}

/*
 * Handles place auto-completion
 * https://www.csimouton.fr/auto-completion-dadresse-avec-la-base-api-adresse-data-gouv-fr-bootstrap-jquery/
 *
 * Requires JQuery UI autocomplete.
 *
 * https://jqueryui.com/autocomplete/#remote-with-cache
 * https://jqueryui.com/autocomplete/#custom-data
 * https://api.jqueryui.com/autocomplete/
 *
 * Adresse API documentation
 * https://adresse.data.gouv.fr/api-doc/adresse
 */
$( function() {
    let cache = {};
    $( "#search-input" ).autocomplete({
      minLength: 3,
      source: function( request, response ) {
        let term = request.term;
        if (term in cache) {
          response(cache[term]);
          return;
        }

        $.getJSON( "https://api-adresse.data.gouv.fr/search/", {
          q: request.term,
          limit: 15,
          autocomplete: 1,
          type: 'municipality'
        }, function( data, status, xhr ) {
          let optionList = [];
          data.features.forEach(obj => {
            optionList.push({
              value: obj.properties.name,
              label: obj.properties.name,
              context: obj.properties.context,
              latitude: obj.geometry.coordinates[1],
              longitude: obj.geometry.coordinates[0]
            });
          });
          cache[term] = optionList;
          response(optionList);
        });
      },
      select: function( event, ui ) {
        $( "#latitude-input" ).val( ui.item.latitude );
        $( "#longitude-input" ).val( ui.item.longitude );
        $( "#search-input" ).val( ui.item.value );

        $("#search-form").submit();
      }
    }).autocomplete( "instance" )._renderItem = function( ul, item ) {
      return $( "<li>" )
        .append( "<div><span style='font-weight: bold'>" + item.label + "</span> " +
            "<span style='font-style: italic; float: right'>" + item.context + "</span></div>" )
        .appendTo( ul );
    };
});
