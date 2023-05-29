/*
 * Open popup on map.
 */
function popupChurch(markerName){
    document.getElementById("map-iframe").contentWindow[markerName].openPopup();
}

/*
 * Handles place auto-completion
 * https://www.csimouton.fr/auto-completion-dadresse-avec-la-base-api-adresse-data-gouv-fr-bootstrap-jquery/
 */
let fetchTrigger = 0;

function onInput() {
  let searchInput = document.getElementById("search-input");
  let val = searchInput.value;
  let opts = document.getElementById('list-autocomplete-search').childNodes;
  let datalist = document.getElementById("list-autocomplete-search");
  for (let i = 0; i < opts.length; i++) {
    if (opts[i].getAttribute('data-string-value') === val) {
      datalist.setAttribute('data-last-search-string', val);
      datalist.setAttribute('data-last-latitude', opts[i].getAttribute('data-latitude'));
      datalist.setAttribute('data-last-longitude', opts[i].getAttribute('data-longitude'));
      return;
    }
  }

  // We cancel precedent timeout trigger if any
  clearTimeout(fetchTrigger);

  // We trigger a new timeout
  fetchTrigger = setTimeout(function() {
    let searchString = searchInput.value;
    let lastSearchString = datalist.getAttribute('data-last-search-string');
    if (searchString.length === 0) {
      return false;
    } else if(searchString === lastSearchString) {
      return false;
    }

    $.get('https://api-adresse.data.gouv.fr/search/', {
      q: searchString,
      limit: 15,
      autocomplete: 1,
      type: 'municipality'
    }, function(data, status, xhr) {
      let optionList = "";
      data.features.forEach(obj => {
        let displayValue = obj.properties.name;
        let contextValue = obj.properties.context;
        let latitude = obj.geometry.coordinates[1];
        let longitude = obj.geometry.coordinates[0];

        optionList += '<option value="' + displayValue + '"' +
            ' data-string-value="' + displayValue + '"' +
            ' data-latitude="' + latitude + '"' +
            ' data-longitude="' + longitude + '"' +
            '>' + contextValue + '</option>';
      });
      datalist.innerHTML = optionList;
    }, 'json');
  }, 500);
}