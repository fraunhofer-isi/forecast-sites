// © 2024-2026 Fraunhofer-Gesellschaft e.V., München
//
// SPDX-License-Identifier: AGPL-3.0-or-later

global.window = {};

describe('Library checks', () =>{

 it('jQuery', () => {
    window.alert = jest.fn();
    function loadLeafletMap(){
      require('../src/leafletMap');
    }
    expect(loadLeafletMap).toThrow('Error: jquery could not be loaded.' );
 });

 it('leaflet', () => {
    window.$ = 'mocked_jquery';
    window.alert = jest.fn();
    function loadLeafletMap(){
      require('../src/leafletMap');
    }
    expect(loadLeafletMap).toThrow('Error: leaflet could not be loaded.' );
 });
});


describe('Public API', () => {
  let sut;
  beforeAll(() => {

    var mockedJQuery={
      append: jest.fn(),
    };
    global.window.$ = jest.fn().mockReturnValue(mockedJQuery);


    var mockedGeoJson = function(data, options){

      if(options){
         var mockedFeature = {
          properties: {
            color: 'mocked_color',
            radius: 'mocked_radius',
          }
        };
        options.style(mockedFeature);

        options.pointToLayer(mockedFeature, 'mockedLatLong');
      }

      var mockedMap = {
        remove: jest.fn(),
      };
      mockedMap.addTo = jest.fn().mockReturnValue(mockedMap);

      return mockedMap;
    };

    var mockedLeaflet = {
      map: jest.fn().mockReturnValue({
        setView: jest.fn().mockReturnValue({
          addLayer: jest.fn(),
        }),
      }),
      geoJSON: mockedGeoJson,
      circleMarker: jest.fn().mockReturnValue(),
      TileLayer: jest.fn().mockReturnValue(),
    };
    global.window.L = mockedLeaflet;

    var leafletMap = require('../src/leafletMap');
    var MapModule = leafletMap['MapModule'];

    sut = new MapModule('mocked_view', 'mocked_zoom', 'mocked_map_width', 'mocked_map_height');
  });

  it('construction', () => {
    expect(sut).toBeDefined();
  });

  it('render', () => {
    sut.render('mocked_data');
  });

  it('reset', () => {
    sut.reset();
  });
});

describe('Private API', () => {

  describe('_popUpProperties', ()=>{

     it('with properties', () => {
      var leafletMap = require('../src/leafletMap');
      var _popUpProperties = leafletMap['_popUpProperties'];

      var mockedFeature = {
        properties: {
          mockedProperty: 'mockedValue'
        }
      };

      var mockedLayer = {
        bindPopup: jest.fn(),
      };

      _popUpProperties(mockedFeature, mockedLayer);


    });

    it('without properties', () => {
      var leafletMap = require('../src/leafletMap');
      var _popUpProperties = leafletMap['_popUpProperties'];

      var mockedFeature = {
      };

      var mockedLayer = {
        bindPopup: jest.fn(),
      };

      _popUpProperties(mockedFeature, mockedLayer);
    });

  });





});