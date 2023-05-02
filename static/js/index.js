function popupChurch(markerName){
    document.getElementById('map-iframe').contentWindow[markerName].openPopup();
}