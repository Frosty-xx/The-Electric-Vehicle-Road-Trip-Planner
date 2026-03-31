import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';
import Data from './Data/ev_dataset.json'
import { useState } from 'react';
import './Map.css'
import sunIcon from './assets/sun.svg';
import moonIcon from './assets/moon.png';
import trafic_electiric_charge_station from './assets/charging-station.png';
import { Icon, DivIcon } from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';

export default function Map() {
  const algiersCord = [48.8566, 2.3522];
  const [isDarkMode, setIsDarkMode] = useState(false);
  const lightTiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const darkTiles = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png";

  const customIcon = new Icon({
    iconUrl: trafic_electiric_charge_station,
    iconSize: [38, 38]
  })

  const customClusterIcon = (cluster) => {
    return new DivIcon({
      html: `<div class="cluster-icon">${cluster.getChildCount()}</div>`,
      iconSize: [40, 40]
    })
  }

  const markers = Data.charging_stations.map((station) => {
    return {
      name: station.name,
      charging_speed: station.power_kw,
      position: {
        lat: station.latitude,
        long: station.longitude
      }
    }
  })

  return (
    <div className='Container'>
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}

      >
        {isDarkMode ? <div className='LightMod'><img src={sunIcon} alt="moon" /> Light</div> : <div className='DarkMod'><img src={moonIcon} alt="moon" /> Dark</div>}
      </button>

      <MapContainer
        center={algiersCord}
        zoom={8}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isDarkMode ? darkTiles : lightTiles}
        />


        <MarkerClusterGroup
          style={{ position:'relative' ,borderRadius:'50%' , backgroundColor: 'transparent'}}
          chunkedLoading
          iconCreateFunction={customClusterIcon}
        >
          {markers.map((marker, index) => (
            <Marker
              key={index}
              position={[marker.position.lat, marker.position.long]}
              icon={customIcon}
            >
              <Popup>
                <h3>{marker.name}</h3>
                <p>Charging Speed: {marker.charging_speed} kW</p>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>


      </MapContainer>
    </div>
  )
}