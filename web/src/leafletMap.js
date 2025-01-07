// © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/* eslint-disable no-undef */

var $ = window.$;
var L = window.L;

if (!$) {
  var jQueryMessage = 'Error: jquery could not be loaded.\n' +
  'Please ensure that is it present by running "npm install" within directory "web".';
  window.alert(jQueryMessage);
  throw new Error(jQueryMessage);
}

if (!L) {
  var leafletMessage = 'Error: leaflet could not be loaded.\n' +
  'Please ensure that is it present by running "npm install" within directory "web".';
  window.alert(leafletMessage);
  throw new Error(leafletMessage);
}

 
const MapModule = function (view, zoom, mapWidth, mapHeight) {
  // Create the map tag:
  var style = "width:" + mapWidth + "px; height:" + mapHeight + "px;border:1px dotted";
  var mapTag = "<div style='"+ style +"' id='mapid'></div>";

  // Append it to body:
  var div = $(mapTag)[0];
  $('#elements').append(div);

  // Create Leaflet map and Agent layers
  var leafletMap = window.L.map('mapid').setView(view, zoom);
  var agentLayer = window.L.geoJSON().addTo(leafletMap);

  // Create the OSM tile layer with correct attribution
  var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
  var osm = new L.TileLayer(osmUrl, { minZoom: 0, maxZoom: 18, attribution: osmAttrib });
  leafletMap.addLayer(osm);

  this.render = function (data) {
    agentLayer.remove();
    agentLayer = L.geoJSON(data, {
      onEachFeature: _popUpProperties,
      style: function (feature) {
        return { color: feature.properties.color };
      },
      pointToLayer: function (feature, latLong) {
        return L.circleMarker(latLong, { radius: feature.properties.radius, color: feature.properties.color });
      }
    }).addTo(leafletMap);
  };

  this.reset = function () {
    agentLayer.remove();
  };
};



function _popUpProperties(feature, layer) {
  var popupContent = '<table>';
  if (feature.properties) {
    for (var p in feature.properties) {
      popupContent += '<tr><td>' + p + '</td><td>' + feature.properties[p] + '</td></tr>';
    }
  }
  popupContent += '</table>';
  layer.bindPopup(popupContent);
}

 /* istanbul ignore next */
if (typeof module !== 'undefined' && module){
  module.exports = {
    'MapModule': MapModule,
    '_popUpProperties': _popUpProperties
  };
}
