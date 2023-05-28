/*
 * Open popup on map.
 */
function popupChurch(markerName){
    $('#map-iframe').contentWindow[markerName].openPopup();
}

/*
 * Handles place auto-completion
 * https://www.csimouton.fr/auto-completion-dadresse-avec-la-base-api-adresse-data-gouv-fr-bootstrap-jquery/
 */
var currentFocus = -1;
var fetchTrigger = 0;

// Fonction pour mettre en forme visuellement un résultat sélectionné
function setActive() {
  var nbVal = $("div.address-feedback a").length;
  if (!nbVal)
    return false; // Si on n'a aucun résultat listé, on s'arrête là.
  // On commence par nettoyer une éventuelle sélection précédente
  $('div.address-feedback a').removeClass("active");

  // Bidouille mathématique pour contraindre le focus dans la plage du nombre de résultats
  currentFocus = ((currentFocus + nbVal - 1) % nbVal) + 1;

  $('div.address-feedback a:nth-child(' + currentFocus + ')').addClass("active");
}

// Au clic sur une adresse suggérée, on ventile l'adresse dans les champs appropriés. On espionne mousedown plutôt que click pour l'attraper avant la perte de focus du champ adresse.
$('div.address-feedback').on("mousedown", "a", function(event) {
  // Stop la propagation par défaut
  event.preventDefault();
  event.stopPropagation();

  $("#adresse").val($(this).attr("data-name"));
  $("#cp").val($(this).attr("data-postcode"));
  $("#ville").val($(this).attr("data-city"));

  $('.address-feedback').empty();
});

// On espionne le clavier dans le champ adresse pour déclencher les actions qui vont bien
$("#search-input").keyup(function(event) {
  // Stop la propagation par défaut
  event.preventDefault();
  event.stopPropagation();

  if (event.keyCode === 38) { // Flèche HAUT
    currentFocus--;
    setActive();
    return false;
  } else if (event.keyCode === 40) { // Flèche BAS
    currentFocus++;
    setActive();
    return false;
  } else if (event.keyCode === 13) { // Touche ENTREE
    if (currentFocus > 0) {
      // On simule un clic sur l'élément actif
      $("div.address-feedback a:nth-child(" + currentFocus + ")").mousedown();
    }
    return false;
  }

  // Si on arrive ici c'est que l'user a avancé dans la saisie : on réinitialise le curseur de sélection.
  $('div.address-feedback a').removeClass("active");
  currentFocus = 0;

  // On annule une éventuelle précédente requête en attente
  clearTimeout(fetchTrigger);

  // Si le champ adresse est vide, on nettoie la liste des suggestions et on ne lance pas de requête.
  let rue = $("#search-input").val();
  if (rue.length === 0) {
    $('.address-feedback').empty();
    return false;
  }

  // On lance une minuterie pour une requête vers l'API.
  fetchTrigger = setTimeout(function() {
    // On lance la requête sur l'API
    $.get('https://api-adresse.data.gouv.fr/search/', {
      q: rue,
      limit: 15,
      autocomplete: 1
    }, function(data, status, xhr) {
      let liste = "";
      $.each(data.features, function(i, obj) {
        // données phase 1 (obj.properties.label) & phase 2 : name, postcode, city
        // J'ajoute chaque élément dans une liste
        let cooladdress = obj.properties.name + " " + obj.properties.postcode + " <strong>" + obj.properties.city + "</strong>";
        liste += '<a class="list-group-item list-group-item-action py-1" href="#" name="' + obj.properties.label + '" data-name="' + obj.properties.name + '" data-postcode="' + obj.properties.postcode + '" data-city="' + obj.properties.city + '">' + cooladdress + '</a>';
      });
      $('.address-feedback').html(liste);
    }, 'json');
  }, 500);
});

// On cache la liste si le champ adresse perd le focus
$("#search-input").focusout(function() {
  $('.address-feedback').empty();
});

// On annule le comportement par défaut des touches entrée et flèches si une liste de suggestion d'adresses est affichée
$("#search-input").keydown(function(e) {
  if ($("div.address-feedback a").length > 0 && (e.keyCode === 38 || e.keyCode === 40 || e.keyCode === 13)) {
    e.preventDefault();
  }
});