import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBars, faBattery, faEnvelope, faHamburger, faLocationCrosshairs, faLocationDot, faX, faChartLine, faMagic, faMagnet, faMagnifyingGlass, faEraser } from '@fortawesome/free-solid-svg-icons'
import { useState } from 'react';
import Nav_Bar from './Search_Selection_Bar';
import './Search_Box.css';
import AddressAutocomplete from './autocomplete';
import Car_Selection from './Car_Selection/Car_Selection';


const BatteryIcon = ({ width }) =>
    <div className='battery_icon'>
        <div className='battery_cap'></div>
        <div className='battery_fill'
            style={
                width < 20 && width ? { width: `${width}%`, backgroundColor: 'red' } :
                    width < 50 && width ? { width: `${width}%`, backgroundColor: 'orange' } :
                        width ? { width: `${width}%` } : { width: '0%' }
            }>
        </div>

    </div>



export default function Search_Box({
    mapCenter,
    setMapCenter,
    setPath,
    setExploredPaths,
    setStrategy,
    setLoadingScreen,
    setBattery_data,
    setBatteryDistanceData,
    setBattery_warning_open,
    setIsStatisticsOpen,
    isStatisticsOpen,
    setChargingStationsInPath,
    setTotalBatteryConsumed,
    setPathDistance,
    setCount

}) {

    const [startAddress, setStartAddress] = useState('');
    const [destinationAddress, setDestinationAddress] = useState('');
    const [battery_level, setBattery_level] = useState('');
    const [activeSearch, setActiveSearch] = useState(null);
    const [errors, setErrors] = useState({});

    const [searchmenuOpen, setSearchmenuOpen] = useState(true);


    const validateForm = () => {
        const newErrors = {};

        // Validate start address
        if (!startAddress.trim()) {
            newErrors.startAddress = 'Starting location is required';
        }

        // Validate destination address
        if (!destinationAddress.trim()) {
            newErrors.destinationAddress = 'Destination is required';
        }

        // Validate battery level
        if (!battery_level.trim()) {
            newErrors.battery_level = 'Battery percentage is required';
        } else {
            const batteryValue = parseFloat(battery_level);
            if (isNaN(batteryValue)) {
                newErrors.battery_level = 'Battery must be a number';
            } else if (batteryValue < 0 || batteryValue > 100) {
                newErrors.battery_level = 'Battery must be between 0 and 100';
            }
        }

        // Validate search strategy
        if (!activeSearch) {
            newErrors.activeSearch = 'Please select a search strategy';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleInputChange = (field, value) => {
        if (field === 'battery_level') setBattery_level(value);
        if (field === 'startAddress') setStartAddress(value);
        if (field === 'destinationAddress') setDestinationAddress(value);

        // Clear error for this field when user starts typing
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: ''
            }));
        }
    };
    function resetData() {
        setExploredPaths([]); // Clear old explored paths first
        setPath(null); // Clear old path first
        setTotalBatteryConsumed(0); // Reset total battery consumed
        setPathDistance(0)
        setBattery_data([]); // Clear old battery data
        setChargingStationsInPath([]); // Clear old charging stations data
        setBatteryDistanceData([]); // Clear old battery distance data
        setCount(0);
    }
    function resetForm() {
        setBattery_level(null)
        setStartAddress(' ');
        setDestinationAddress('');
        setActiveSearch(null);
    }

    async function handleSearch(e) {
        e.preventDefault();
        if (!validateForm()) {
            return;
        }
        setLoadingScreen(true);
        const payload = {
            start: startAddress,
            end: destinationAddress,
            battery_level: battery_level,
            search_strategy: activeSearch
        };
        console.log('Searching route:', payload);
        // run App.py before request
        const API_URL = import.meta.env.VITE_API_URL;
        console.log('API URL:', API_URL + '/api/route');
        try {

            resetData(); // Clear old data before fetching new results
            setStrategy(activeSearch);
            const response = await fetch(`${API_URL}/api/route`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            if (!response.ok) {
                setBattery_warning_open(true);
                setLoadingScreen(false);
                return;
            }
            const data = await response.json();
            console.log(data)
            setTimeout(() => {
                // Set new data after a brief delay to ensure cleanup
                setExploredPaths(data.explored_paths || []);
                setMapCenter(data.path[0]);
                setPath(data.path.filter(coord => !isNaN(coord[0]) && !isNaN(coord[1])));
                setBattery_data(data.Battery_Time_Graph || [])
                setBatteryDistanceData(data.Battery_Distance_Graph || [])
                console.log("Charging Stations in Path:", data.Charging_stations || []);
                setChargingStationsInPath(data.Charging_stations || [])
                setTotalBatteryConsumed(data.total_kwh_used || 0);
                setPathDistance(data.total_ditance_km)

            }, 100);
            setLoadingScreen(false);

        } catch (error) {
            setLoadingScreen(false);
            console.error('Network Error:', error);
            alert("Connection Failed: The server is unreachable. Please check your internet or try again later.");
        }

    }

    return (
        <>
            <div className="search-box-container">
                <div style={{ position: "relative" }}>
                    <div className="button-controls">
                        <button
                            type="button"
                            className='stats-button'
                            title='View Statistics'
                            onClick={() => {
                                searchmenuOpen ? setSearchmenuOpen(false) : "";
                                setIsStatisticsOpen(prev => !prev);
                            }}
                        >
                            {isStatisticsOpen ? <FontAwesomeIcon icon={faX} /> : <FontAwesomeIcon icon={faChartLine} />}

                        </button>
                        <button type='"button"' title='Search Menu' className='stats-button' onClick={() => {
                            isStatisticsOpen ? setIsStatisticsOpen(false) : "";
                            setSearchmenuOpen(prev => !prev)
                        }}>
                            {searchmenuOpen ? <FontAwesomeIcon icon={faX} /> : <FontAwesomeIcon icon={faMagnifyingGlass} />}
                        </button>
                        <button type='"button"' title='Reset' className='stats-button' onClick={() => {
                            resetData();
                            resetForm();
                        }}>
                            <FontAwesomeIcon icon={faEraser} />

                        </button>

                    </div>
                    <form onSubmit={handleSearch}>
                        <div className='search-box' style={isStatisticsOpen ? { visibility: "hidden" } : searchmenuOpen ? {} : { padding: '0px', display: 'none' }}>
                            <p className='search_title'>Where To:</p>
                            <div className="input-group">
                                <label htmlFor="start-address" className="input-label">
                                    <FontAwesomeIcon icon={faLocationCrosshairs} color='red' fontSize={18}></FontAwesomeIcon>
                                </label>
                                <div className="input-wrapper">
                                    <AddressAutocomplete
                                        id="startAddress"
                                        onSelect={(place) => setStartAddress(place.display_name)}
                                        onChange={(value) => handleInputChange('startAddress', value)}
                                        countrycodes='DZ'
                                        errors={errors}
                                        setErrors={setErrors}
                                    />
                                    {errors.startAddress && <span className="error-message">{errors.startAddress}</span>}
                                </div>
                            </div>

                            <div className="input-group">
                                <label htmlFor="destination-address" className="input-label">
                                    <FontAwesomeIcon icon={faLocationDot} color='white' fontSize={18}></FontAwesomeIcon>
                                </label>
                                <div className="input-wrapper">
                                    <AddressAutocomplete
                                        id="destinationAddress"
                                        onSelect={(place) => setDestinationAddress(place.display_name)}
                                        onChange={(value) => handleInputChange('destinationAddress', value)}
                                        countrycodes='DZ'
                                        errors={errors}
                                        placeholder='Search for an destination...'
                                        setErrors={setErrors}
                                    />
                                    {errors.destinationAddress && <span className="error-message">{errors.destinationAddress}</span>}
                                </div>
                            </div>
                            <hr style={{ border: '1px solid #ccc', }} />
                            <div>

                                <p className='search_title'>Battery Level:</p>
                                <div className="input-group" style={{ alignItems: "center", padding: "1rem 0" }}>
                                    <label htmlFor="battery_level">
                                        {/* <FontAwesomeIcon icon={faBattery} color='green' fontSize={18}></FontAwesomeIcon> */}
                                        <BatteryIcon width={battery_level} />
                                    </label>
                                    <div className="input-wrapper">
                                        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                                            <input
                                                id="battery_level"
                                                type="range"
                                                min="0"
                                                max="100"
                                                className={` battery_slider ${errors.battery_level ? 'input-error' : ''}`}
                                                value={battery_level ? battery_level : 0}
                                                onChange={(e) => handleInputChange('battery_level', e.target.value)}
                                                style={
                                                    battery_level < 20 ? { accentColor: 'red' } :
                                                        battery_level < 50 ? { accentColor: 'orange' } :
                                                            {}
                                                }
                                            />
                                            <p className='battery_level'>{battery_level ? battery_level : 0}% </p>
                                        </div>
                                        {errors.battery_level && <span className="error-message">{errors.battery_level}</span>}
                                    </div>
                                </div>
                            </div>
                            <hr style={{ border: '1px solid #ccc', }} />

                            <div>
                                <p className='search_title'>Search Algorithm:</p>
                                <br></br>
                                <Nav_Bar activeSearch={activeSearch} setActiveSearch={setActiveSearch} />
                                <br></br>
                                {errors.activeSearch && <span className="error-message" style={{ marginTop: '-0.5rem' }}>{errors.activeSearch}</span>}
                            </div>
                            <hr style={{ border: '1px solid #ccc', }} />

                            <Car_Selection />

                            <button type="submit" className="search-button" onClick={() => {
                                if (validateForm()) {
                                    !isStatisticsOpen ? setIsStatisticsOpen(true) : ""
                                    setSearchmenuOpen(false)
                                }
                            }
                            }>
                                Search Route
                            </button>
                        </div>

                    </form>

                </div>
            </div>
        </>
    );
}
