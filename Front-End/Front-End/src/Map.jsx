import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';
import { useState } from 'react';
import './Map.css'
import sunIcon from './assets/sun.svg'; 
import moonIcon from './assets/moon.png';

export default function Map() {
  const algiersCord = [36.7338, 2.9];
  const [isDarkMode, setIsDarkMode] = useState(false);
  const lightTiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const darkTiles = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png";

  return (
    <div className='Container'>
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}
        
      >
        {isDarkMode ? <div className='LightMod'><img src={sunIcon} alt="moon" /> Light</div> : <div className='DarkMod'><img src={moonIcon} alt="moon" /> Dark</div>}
      </button>

      <MapContainer
        center={algiersCord}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isDarkMode ? darkTiles : lightTiles}
        />
      </MapContainer>
    </div>
  )
}