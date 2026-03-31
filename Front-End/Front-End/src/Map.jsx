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

  const [path, setPath] = useState([
    [36.7115, 2.8425],
    [36.7189, 2.8525],
    [36.7215, 2.8625],
    [36.7315, 2.8725],
    [36.7415, 2.8825],
    [36.7535, 2.8912],
  ]);

  return (
    <div className='Container'>
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}

      >
        {isDarkMode ? <div className='LightMod'><img src={sunIcon} alt="moon" /> Light</div> : <div className='DarkMod'><img src={moonIcon} alt="moon" /> Dark</div>}
      </button>

      <MapContainer
        center={algiersCord}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isDarkMode ? darkTiles : lightTiles}
        />

        <Marker
          position={[36.7115, 2.8425]}
        >
          <Popup>Start Node</Popup>
        </Marker>
        <Marker
          position={[36.7535, 2.8912]}
        >
          <Popup>End Node</Popup>
        </Marker>

        <Polyline positions={path} color="blue" weight={5} opacity={0.7} />
      </MapContainer>
    </div>
  )
}