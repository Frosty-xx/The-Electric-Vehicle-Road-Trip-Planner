import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet.polyline.snakeanim';
import DZ_Charging_Stations from './Data/Algeria_charging_stations.json'
import { useState, useEffect, useRef } from 'react';
import './Map.css'
import goal_marker from './assets/goal_marker.svg';
import trafic_electiric_charge_station from './assets/charging.png';
import { Icon, DivIcon } from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import Search_Box from './UI/Search_Box';
import Statistics from './UI/Statistics';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faL, faMagic, faMoon, faSatellite, faSun } from '@fortawesome/free-solid-svg-icons';
//Soundes
import searchSound from './assets/Audio/serach_sound.mp3'
import successSound from './assets/Audio/success.mp3'
//-----------------
import AddressAutocomplete from './UI/autocomplete';
import LoadingScreen from './UI/Loading_screen/Loading_screen';
import Battery_warning from './UI/Battery_warning/battery_warning';

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
//Snake line component to animate the path drawing
const SnakeLine = ({ positions, opacity, color = "#4a90e2", weight = 6, speed = 300, dashArray, zIndex = 9999 }) => {
  const map = useMap();

  useEffect(() => {
    if (!positions || positions.length === 0) return;

    let line = null;
    const timer = setTimeout(() => {
      line = L.polyline(positions, { opacity: opacity, color: color, weight: weight, snakingSpeed: speed, dashArray: dashArray });
      line.addTo(map).snakeIn();

      // Set z-index on the SVG element
      if (line && line._path) {
        line._path.style.zIndex = zIndex;
      }
    });

    return () => {
      clearTimeout(timer);
      if (line && map.hasLayer(line)) {
        map.removeLayer(line);
      }
    };
  }, [map, positions, color, weight, speed, opacity, zIndex]);

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
// Component to handle map events (e.g., zoom)
function MapEvents({ onZoom }) {
  const map = useMapEvents({
    zoomend: () => onZoom(map.getZoom())
  });
  return null;
}

export default function Map() {


  const algeriaCord = [30, 1.6596];
  // Loading Screen============================================================================================================
  const [loading_screen, setLoadingScreen] = useState(false);
  //Battery Graph============================================================================================================
  const [batteryData, setBatteryData] = useState([]);
  const [batteryDistanceData, setBatteryDistanceData] = useState([]);
  // State variables============================================================================================================
  const [mapCenter, setMapCenter] = useState(algeriaCord)
  const [totalBatteryConsumed, setTotalBatteryConsumed] = useState(0); // State to hold total battery consumed
  const [strategy, setStrategy] = useState(null); // State to hold the selected strategy
  // Map tile URLs===================================================================================================
  const lightTiles = "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}";
  const darkTiles = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png";
  const satteliteTiles = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

  // delay Function============================================================================================================
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  // Calculate distance between coordinates for animation timing
  const getPathDistance = (positions) => {
    if (!positions || positions.length < 2) return 0;
    let distance = 0;
    for (let i = 0; i < positions.length - 1; i++) {
      const [lat1, lng1] = positions[i];
      const [lat2, lng2] = positions[i + 1];
      const R = 6371; // Earth's radius in km
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLng = (lng2 - lng1) * Math.PI / 180;
      const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      distance += R * c;
    }
    return distance;
  };

  // Audio refs=======================================================================================================================================
  const searchAudioRef = useRef(new Audio(searchSound));
  const successAudioRef = useRef(new Audio(successSound));
  const animationCompletionCountRef = useRef(0);

  // Control States:=======================================================================================================================================
  const [tileLayerUrl, setTileLayerUrl] = useState(lightTiles);
  const [loading, setLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isBatteryWarningOpen, setIsBatteryWarningOpen] = useState(false);
  const [isStatisticsOpen, setIsStatisticsOpen] = useState(false);
  const [zoom, setZoom] = useState(5);
  const [chargingStationsInPath, setChargingStationsInPath] = useState([]);

  // Scratch animtion:
  const [showFinalPath, setShowFinalPath] = useState(false); // State to show final path after explored paths are done
  const [startExploring, setStartExploring] = useState(false)
  const [allAnimationsComplete, setAllAnimationsComplete] = useState(false); // Track when all animations complete
  const [exploredPaths, setExploredPaths] = useState([]); // State to hold explored paths
  const [count, setCount] = useState(0);// Count the explored paths displayed
  const [path, setPath] = useState(null); // State to hold the path data from the backend
  const [pathDistance, setPathDistance] = useState(0); // Distance of the current path in km

  // TIMING CONFIGURATION
  const EXPLORED_PATH_DISPLAY_TIME = 30;
  const EXPLORED_PATH_ANIMATION_SPEED = 300; // Slower speed so animation is visible (lower = slower drawing)


  // Handle explored paths animation timing
  useEffect(() => {
    if (count < exploredPaths.length && !loading && !showFinalPath) {
      const timer = setTimeout(() => setCount(count + 1), EXPLORED_PATH_DISPLAY_TIME);
      return () => clearTimeout(timer);
    } else if (count >= exploredPaths.length && exploredPaths.length > 0) {
      // All explored paths shown, now show final path
      setShowFinalPath(true);

    }
  }, [count, exploredPaths.length, loading]);

  // Handle loading state
  useEffect(() => {
    // Simulate loading delay when path changes
    if (path && path.length > 0) {
      setLoading(true);
      setCount(0)
      setShowFinalPath(false)
      delay(1500).then(() => setLoading(false));
    }
  }, [path]);

  // Play search sound while explored paths are active
  useEffect(() => {
    const searchAudio = searchAudioRef.current;

    if (count < exploredPaths.length && exploredPaths.length > 0 && !loading && !showFinalPath) {
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
  }, [exploredPaths, count, showFinalPath, loading]);

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

  // ====================================== UI ICONS =======================================================
  // Custom icon for charging stations with dynamic size based on zoom level
  const customIcon = (size) => new Icon({
    iconUrl: trafic_electiric_charge_station,
    iconSize: [size, size]
  })
  const getIconSize = (zoom) => Math.max(30, zoom * 3);
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
  // ======================================================================================================

  const markers = DZ_Charging_Stations.charging_stations.map((station) => {
    return {
      name: station.name,
      charging_speed: station.power_kw,
      position: {
        lat: station.latitude,
        long: station.longitude
      }
    }
  })

  // Custom cluster icon styling
  const createClusterCustomIcon = (cluster) => {
    const count = cluster.getChildCount();
    let size = 'large';
    let color = '#4a90e2';

    if (count < 10) {
      size = 'small';
      color = '#4a90e2';
    } else if (count < 50) {
      size = 'medium';
      color = '#ff9800';
    } else {
      size = 'large';
      color = '#e74c3c';
    }

    return new DivIcon({
      html: `
        <div class="custom-cluster-icon ${size}" style="background: ${color}; border-color: ${color};">
          <span>${count}</span>
        </div>
      `,
      className: 'custom-cluster',
      iconSize: size === 'small' ? [40, 40] : size === 'medium' ? [50, 50] : [60, 60],
      iconAnchor: size === 'small' ? [20, 20] : size === 'medium' ? [25, 25] : [30, 30]
    });
  };
  const worldBounds = [
    [-90, -180], // South Pole / International Date Line West
    [90, 180]    // North Pole / International Date Line East
  ];
  return (

    <div className='Container'>
      <Battery_warning isOpen={isBatteryWarningOpen} setIsOpen={setIsBatteryWarningOpen} />
      <LoadingScreen isLoading={loading_screen} />
      <Search_Box
        mapCenter={mapCenter}
        setBattery_warning_open={setIsBatteryWarningOpen}
        setMapCenter={setMapCenter}
        setPath={setPath}
        setExploredPaths={setExploredPaths}
        setStrategy={setStrategy}
        setLoadingScreen={setLoadingScreen}
        setBattery_data={setBatteryData}
        setBatteryDistanceData={setBatteryDistanceData}
        setIsStatisticsOpen={setIsStatisticsOpen}
        isStatisticsOpen={isStatisticsOpen}
        setChargingStationsInPath={setChargingStationsInPath}
        setTotalBatteryConsumed={setTotalBatteryConsumed}
        setPathDistance={setPathDistance}
        setCount={setCount}
      />
      <Statistics
        batteryData={batteryData}
        batteryDistanceData={batteryDistanceData}
        pathDistance={pathDistance}
        strategy={strategy}
        totalBatteryConsumed={totalBatteryConsumed}
        isOpen={isStatisticsOpen}
      />
      <div className='views_container'>
        <button
          onClick={() => {
            setIsDarkMode(!isDarkMode)
            setTileLayerUrl(isDarkMode ? lightTiles : darkTiles)
          }}
          className={`ThemeButton ${isDarkMode ? 'LightMode' : 'DarkMode'}`}
        >
          {isDarkMode ? <FontAwesomeIcon icon={faSun} /> : <FontAwesomeIcon icon={faMoon} />}
        </button>
        <button className='SatteliteButton'
          onClick={() => setTileLayerUrl(tileLayerUrl == satteliteTiles && isDarkMode ? darkTiles : tileLayerUrl == satteliteTiles && !isDarkMode ? lightTiles : satteliteTiles)}
          style={tileLayerUrl == satteliteTiles ? { backgroundColor: '#000000b3', color: "white" } : {}}>
          <FontAwesomeIcon icon={faSatellite}></FontAwesomeIcon>
        </button>

      </div>
      <MapContainer
        center={mapCenter}
        zoom={zoom}
        maxZoom={8}
        maxBounds={worldBounds}
        maxBoundsViscosity={1.0}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <MapUpdater path={path} />
        <MapEvents onZoom={setZoom} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={tileLayerUrl === satteliteTiles ? satteliteTiles : (isDarkMode ? darkTiles : lightTiles)}
          noWrap={true}
          maxZoom={8}
        />
        {!path && (
          <MarkerClusterGroup
            iconCreateFunction={createClusterCustomIcon}
            maxClusterRadius={80}
            disableClusteringAtZoom={15}
          >
            {markers.map((marker, index) => (
              <Marker
                key={index}
                position={[marker.position.lat, marker.position.long]}
                icon={customIcon(getIconSize(zoom))}
              >
                <Popup>
                  <h3>{marker.name}</h3>
                  <p>Charging Speed: {marker.charging_speed} kW</p>
                </Popup>
              </Marker>
            ))}
          </MarkerClusterGroup>)}

        {path && path.length > 0 && (
          <>
            {/* Start point marker */}
            <ZoomableMarker
              position={path[0]}
              icon={startPointIcon}
              style={{ zIndex: 999999999999 }}
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
            {chargingStationsInPath.map((station, index) => (
              <Marker
                key={`station-${index}`}
                position={[station.lat, station.lon]}
                icon={customIcon(getIconSize(zoom))}>
                <Popup>
                  <p>Charging Speed: {station.power_kw} kW</p>
                </Popup>
              </Marker>))}
          </>
        )}

        {path && showFinalPath && ( // Only render the path after explored paths finish
          <>
            <SnakeLine positions={path} color='#285ed3' weight={5} speed={500} zIndex={9999999999999} />
          </>
        )}

        {exploredPaths && exploredPaths.length > 0 && !loading && (
          <>
            {exploredPaths.slice(0, count).map((exploredPath, index) => {
              return (
                <SnakeLine
                  key={`explored-${index}`}
                  positions={exploredPath}
                  color={"#d61717"}
                  weight={3}
                  speed={EXPLORED_PATH_ANIMATION_SPEED}
                  opacity={0.5}
                  zIndex={1}
                />
              );
            })}
          </>
        )}
      </MapContainer>
    </div>
  )
}