import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet.polyline.snakeanim';
import Data from './Data/ev_dataset.json'
import France_CS from './Data/ev_dataset(FR).json'
import { useState, useEffect, useRef } from 'react';
import './Map.css'
import sunIcon from './assets/sun.svg';
import moonIcon from './assets/moon.png';
import goal_marker from './assets/goal_marker.svg';
import trafic_electiric_charge_station from './assets/charging-station.png';
import { Icon, DivIcon } from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import Search_Box from './UI/Search_Box';
import Battery_Graph from './UI/Battery_Graph';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagic } from '@fortawesome/free-solid-svg-icons';
//Soundes
import searchSound from './assets/Audio/serach_sound.mp3'
import successSound from './assets/Audio/success.mp3'
import AddressAutocomplete from './UI/autocomplete';
import LoadingScreen from './UI/Loading_screen/Loading_screen';
// Component to handle map zoom when path changes
function MapUpdater({ path }) {
  const map = useMap();

  useEffect(() => {
    if (path && path.length > 0) {
      // Zoom to the first coordinate and set a higher zoom level
      map.flyTo(path[0], 7, { duration: 1 });
    }
  }, [path, map]);

  return null;
}
//Calculate distance between two coordinates (haversine formula)
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

//Calculate total distance of path
const getPathDistance = (positions) => {
  if (!positions || positions.length < 2) return 0;
  let totalDistance = 0;
  for (let i = 0; i < positions.length - 1; i++) {
    totalDistance += calculateDistance(positions[i][0], positions[i][1], positions[i + 1][0], positions[i + 1][1]);
  }
  return totalDistance;
};

//Snake line component to animate the path drawing
const SnakeLine = ({ positions, opacity, color = "#4a90e2", weight = 6, speed = 300, delay = 0, onAnimationComplete, zIndex = 1 }) => {
  const map = useMap();

  useEffect(() => {
    if (!positions || positions.length === 0) return;

    let line = null;
    const timer = setTimeout(() => {
      line = L.polyline(positions, { opacity: opacity, color: color, weight: weight, snakingSpeed: speed });
      line.addTo(map).snakeIn();

      // Set z-index on the SVG element
      if (line && line._path) {
        line._path.style.zIndex = zIndex;
      }
      // Calculate animation duration and call onAnimationComplete when done
      if (onAnimationComplete) {
        const pathLength = getPathDistance(positions);
        const animationDuration = (pathLength * 100) / speed;
        const completeTimer = setTimeout(() => {
          onAnimationComplete();
        }, animationDuration);

        return () => clearTimeout(completeTimer);
      }
    }, delay);

    return () => {
      clearTimeout(timer);
      if (line && map.hasLayer(line)) {
        map.removeLayer(line);
      }
    };
  }, [map, positions, color, weight, speed, opacity, delay, onAnimationComplete, zIndex]);

  return null;
};

// Component to handle marker click zoom
function ZoomableMarker({ position, icon, popupContent, label }) {
  const map = useMap();

  const handleMarkerClick = () => {
    map.flyTo(position, 18, { duration: 1 });
  };

  return (
    <Marker
      position={position}
      icon={icon}
      eventHandlers={{
        click: handleMarkerClick
      }}
    >
      <Popup>
        {popupContent}
      </Popup>
    </Marker>
  );
}



export default function Map() {


  const tunisiaCord = [36.8065, 10.1815];
  const lyonCord = [45.76, 4.8357];
  // Loading Screen:
  const [loading_screen, setLoadingScreen] = useState(false);

  //Battery Graph:
  const [batteryData, setBatteryData] = useState([]);

  // State variables
  const [loading, setLoading] = useState(false);
  const [mapCenter, setMapCenter] = useState(tunisiaCord)
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [path, setPath] = useState(null); // State to hold the path data from the backend
  const [exploredPaths, setExploredPaths] = useState([]); // State to hold explored paths
  const [showFinalPath, setShowFinalPath] = useState(false); // State to show final path after explored paths are done
  const [strategy, setStrategy] = useState(null); // State to hold the selected strategy
  const [allAnimationsComplete, setAllAnimationsComplete] = useState(false); // Track when all animations complete
  const [pathDistance, setPathDistance] = useState(0); // Distance of the current path in km
  const lightTiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const darkTiles = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png";
  // delay Function
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const STAGGER_DELAY = 2; // 50ms delay between each explored path animation
  // Audio refs
  const searchAudioRef = useRef(new Audio(searchSound));
  const successAudioRef = useRef(new Audio(successSound));
  const animationCompletionCountRef = useRef(0);

  // Cluster Group Hadling:
  const [showClusters, setShowClusters] = useState(true);


  useEffect(() => {

    // Simulate loading delay when path changes
    if (path && path.length > 0) {
      setLoading(true);
      setShowFinalPath(false); // Reset final path flag for new search
      // Calculate the distance of the main path
      const dist = getPathDistance(path);
      setPathDistance(dist);
      setShowClusters(false); // Hide clusters when a path is displayed
      delay(1500).then(() => setLoading(false)); // Simulate a 1.5-second loading time
    }

  }, [path]);

  // Show final path after all explored paths finish animating
  useEffect(() => {
    if (exploredPaths.length > 0) {
      setShowFinalPath(false);
      // Calculate total animation time: last path delay + animation time
      const totalAnimationTime = (exploredPaths.length - 1) * (strategy == "BFS" ? STAGGER_DELAY / 10 : STAGGER_DELAY) + 1500; //  stagger delay + 1.5s for animation
      const timer = setTimeout(() => {
        setShowFinalPath(true);
      }, totalAnimationTime);
      return () => clearTimeout(timer);
    } else {
      setShowFinalPath(true); // Show immediately if no explored paths
    }
  }, [exploredPaths]);

  // Play search sound while explored paths are active
  useEffect(() => {
    const searchAudio = searchAudioRef.current;

    if (exploredPaths.length > 0 && !showFinalPath && !loading) {
      // Start playing search sound on loop
      searchAudio.currentTime = 0;
      searchAudio.loop = true;
      searchAudio.play().catch(() => { }); // Catch if autoplay is blocked
    } else {
      // Stop search sound when explored paths finish
      searchAudio.pause();
      searchAudio.currentTime = 0;
    }

    return () => {
      searchAudio.pause();
      searchAudio.currentTime = 0;
    };
  }, [exploredPaths, showFinalPath, loading]);

  // Play success sound when final path is shown
  useEffect(() => {
    const successAudio = successAudioRef.current;

    if (showFinalPath && path && path.length > 0) {
      // Stop search sound if it's still playing
      searchAudioRef.current.pause();
      searchAudioRef.current.currentTime = 0;

      // Play success sound once
      successAudio.currentTime = 0;
      successAudio.loop = false;
      successAudio.play().catch(() => { }); // Catch if autoplay is blocked
    }

    return () => {
      successAudio.pause();
      successAudio.currentTime = 0;
    };
  }, [showFinalPath, path]);







  const customIcon = new Icon({
    iconUrl: trafic_electiric_charge_station,
    iconSize: [38, 38]
  })

  // Create a glowing blue dot for the start point
  const startPointIcon = new DivIcon({
    html: `<div style="
      width: 20px;
      height: 20px;
      background-color: #4a90e2;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 0 10px #4a90e2, 0 0 20px #4a90e2, 0 0 30px #4a90e2;
      position: relative;
    "></div>`,
    iconSize: [20, 20],
    popupAnchor: [0, -10]
  })

  // Create a red FontAwesome marker for the goal
  const goalPointIcon = new Icon({
    iconUrl: goal_marker,
    iconSize: [70, 70],
    iconAnchor: [26, 50],
    popupAnchor: [0, -15]
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
      <LoadingScreen isLoading={loading_screen} />
      <Search_Box mapCenter={mapCenter} setMapCenter={setMapCenter} setPath={setPath} setExploredPaths={setExploredPaths} setStrategy={setStrategy} setLoadingScreen={setLoadingScreen} setBattery_data={setBatteryData}/>
      <Battery_Graph data={batteryData}/>
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}

      >
        {isDarkMode ? <div className='LightMod'><img src={sunIcon} alt="moon" /> Light</div> : <div className='DarkMod'><img src={moonIcon} alt="moon" /> Dark</div>}
      </button>

      <MapContainer
        center={mapCenter}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
      >
        <MapUpdater path={path} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isDarkMode ? darkTiles : lightTiles}
        />

        {showClusters && (          <MarkerClusterGroup
            style={{ position: 'relative', borderRadius: '50%', backgroundColor: 'transparent' }}
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
        )}
        {!showClusters && (
            markers.map((marker, index) => (
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
            ))
        )}


        {path && path.length > 0 && (
          <>
            setShowClusters(false); // Hide clusters when a path is displayed
            {/* Start point marker */}
            <ZoomableMarker
              position={path[0]}
              icon={startPointIcon}
              style={{ zIndex: 999 }}
              popupContent={
                <>
                  <h4>Start Point</h4>
                  <p>Lat: {path[0][0]?.toFixed(4)}</p>
                  <p>Lng: {path[0][1]?.toFixed(4)}</p>
                </>
              }
              label="Start"
            />

            {/* Goal point marker */}
            <ZoomableMarker
              position={path[path.length - 1]}
              icon={goalPointIcon}
              style={{ zIndex: 999 }}
              popupContent={
                <>
                  <h4>Destination</h4>
                  <p>Lat: {path[path.length - 1][0]?.toFixed(4)}</p>
                  <p>Lng: {path[path.length - 1][1]?.toFixed(4)}</p>
                </>
              }
              label="Goal"
            />
          </>
        )}

        {path && !loading && showFinalPath && ( // Only render the path after explored paths finish
          <>
            {/* <Polyline pathOptions={{ color: 'darkblue', weight: 8, opacity: 0.5, lineJoin: 'round' }} positions={path} /> */}

            <SnakeLine positions={path} color="#1022caa2" weight={8} speed={200 + pathDistance} opacity={0.5} zIndex={100} /> {/* Add a second line with different style for the explored path */}
            <SnakeLine positions={path} color='#4a90e2' weight={5} speed={200 + pathDistance} zIndex={100} />

            {/* <Polyline pathOptions={{ color: '#4a90e2', weight: 8, opacity: 1, lineJoin: 'round', className: 'animated-polyline' }} positions={path} /> */}
          </>
        )}

        {exploredPaths && exploredPaths.length > 0 && !loading && (
          <>
            {exploredPaths.map((exploredPath, index) => {
              // Filter out invalid paths
              if (!exploredPath || !Array.isArray(exploredPath) || exploredPath.length === 0) {
                return null;
              }

              const delayTime = index * (strategy == "BFS" ? STAGGER_DELAY / 10 : STAGGER_DELAY); // Stagger animations by 300ms each
              return (
                <SnakeLine
                  key={`explored-${index}`}
                  positions={exploredPath}
                  color={"#d61717"}
                  weight={3}
                  speed={400 + pathDistance}
                  opacity={0.6}
                  zIndex={10}
                  delay={delayTime}
                />
              );
            })}
          </>
        )}
      </MapContainer>
    </div>
  )
}