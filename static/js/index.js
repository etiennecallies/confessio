/*
 * Open popup on map.
 *
 * Does not require JQuery.
 */
function popupChurch(markerName){
    document.getElementById("map-iframe").contentWindow[markerName].openPopup();
}

/*
 * Handles place auto-completion.
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
    let autocompleteUrl = $('#search-input').attr('data-autocomplete-url');

    let cache = {};
    $( "#search-input" ).autocomplete({
      minLength: 3,
      source: function( request, response ) {
        let term = request.term;
        if (term in cache) {
          response(cache[term]);
          return;
        }

        $.getJSON( autocompleteUrl, {
          query: request.term,
        }, function( data, status, xhr ) {
          let optionList = [];
          data.forEach(obj => {
            optionList.push(obj);
          });
          cache[term] = optionList;
          response(optionList);
        });
      },
      select: function( event, ui ) {
        $("#latitude-input").val(ui.item.latitude);
        $("#longitude-input").val(ui.item.longitude);
        $("#search-input").val(ui.item.name);
        $("#parish-uuid-input").val(ui.item.parish_uuid);

        $("#search-form").submit();
      }
    }).autocomplete( "instance" )._renderItem = function( ul, item ) {
      let badge =
          item.type === 'municipality' ? '<span class="badge badge-primary">Ville</span>' :
              (item.type === 'parish' ? '<span class="badge badge-success">Paroisse</span>' : '');
      return $( "<li>" )
        .append( "<div class='row'><div class='col-md autocomplete-name'>" + item.name + " " + badge + "</div>" +
            "<div class='col-md text-end' style='font-style: italic'>" + item.context + "</div></div>" )
        .appendTo( ul );
    };
});

/*
 * Watch map movement.
 *
 * Requires JQuery (to wait for the iframe to be loaded).
 */
$(document).ready(function () {
  $('#map-iframe').load(function() {
    let mapObjectName = $('#map-iframe').attr('data-map-name');
    let map = document.getElementById("map-iframe").contentWindow[mapObjectName];

    map.on('moveend', function(evt){
      let bounds = map.getBounds();
      $("#min-lat-input").val(bounds._southWest.lat);
      $("#min-lng-input").val(bounds._southWest.lng);
      $("#max-lat-input").val(bounds._northEast.lat);
      $("#max-lng-input").val(bounds._northEast.lng);
      $("#search-in-this-area-btn").css('visibility', 'visible');
    });
  });
});
