import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBattery, faEnvelope, faLocationCrosshairs, faLocationDot } from '@fortawesome/free-solid-svg-icons'
import { useState } from 'react';
import Nav_Bar from './Nav_Bar';
import './Search_Box.css';

export default function Search_Box({mapCenter,setMapCenter,setPath,setExploredPaths, setStrategy, setDistance}) {
    const [startAddress, setStartAddress] = useState('');
    const [destinationAddress, setDestinationAddress] = useState('');
    const [battery_level, setBattery_level] = useState('');
    const [activeSearch, setActiveSearch] = useState(null);
    const [errors, setErrors] = useState({});

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
        if (field === 'startAddress') setStartAddress(value);
        if (field === 'destinationAddress') setDestinationAddress(value);
        if (field === 'battery_level') setBattery_level(value);
        
        // Clear error for this field when user starts typing
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: ''
            }));
        }
    };

    async function handleSearch(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        const payload = {
            start: startAddress,
            end: destinationAddress,
            battery_level: battery_level,
            search_strategy: activeSearch
        };
        console.log('Searching route:', payload);
        // run App.py before request
        const response = await fetch('http://localhost:5000/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        if (!response.ok){
            alert('No route found!')
            return;
        }
        const data = await response.json();
        console.log(data)
        setStrategy(activeSearch);
        setExploredPaths([]); // Clear old explored paths first
        setPath([]); // Clear old path first
        setTimeout(() => {
          // Set new data after a brief delay to ensure cleanup
          setExploredPaths(data.explored_paths);
          setMapCenter(data.path[0]);
          setPath(data.path);
          if (data.distance) {
            setDistance(data.distance);
          }
        }, 100);
    }

    return (
        <div className="search-box-container">
            <form onSubmit={handleSearch}>
                <div className='search-box'>
                    <div className="input-group">
                        <label htmlFor="start-address" className="input-label">
                            <FontAwesomeIcon icon={faLocationCrosshairs} color='red' fontSize={18}></FontAwesomeIcon>
                        </label>
                        <div className="input-wrapper">
                            <input
                                id="start-address"
                                type="text"
                                className={`search-input ${errors.startAddress ? 'input-error' : ''}`}
                                placeholder="Enter starting location..."
                                value={startAddress}
                                onChange={(e) => handleInputChange('startAddress', e.target.value)}
                            />
                            {errors.startAddress && <span className="error-message">{errors.startAddress}</span>}
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="destination-address" className="input-label">
                            <FontAwesomeIcon icon={faLocationDot} color='black' fontSize={18}></FontAwesomeIcon>
                        </label>
                        <div className="input-wrapper">
                            <input
                                id="destination-address"
                                type="text"
                                className={`search-input ${errors.destinationAddress ? 'input-error' : ''}`}
                                placeholder="Enter destination..."
                                value={destinationAddress}
                                onChange={(e) => handleInputChange('destinationAddress', e.target.value)}
                            />
                            {errors.destinationAddress && <span className="error-message">{errors.destinationAddress}</span>}
                        </div>
                    </div>
                    <div className="input-group">
                        <label htmlFor="destination-address" className="input-label">
                            <FontAwesomeIcon icon={faBattery} color='green' fontSize={18}></FontAwesomeIcon>
                        </label>
                        <div className="input-wrapper">
                            <input
                                id="battery_level"
                                type="text"
                                className={`search-input ${errors.battery_level ? 'input-error' : ''}`}
                                placeholder="Enter your current battery %"
                                value={battery_level}
                                onChange={(e) => handleInputChange('battery_level', e.target.value)}
                            />
                            {errors.battery_level && <span className="error-message">{errors.battery_level}</span>}
                        </div>
                    </div>
                    <Nav_Bar activeSearch={activeSearch} setActiveSearch={setActiveSearch} />
                    {errors.activeSearch && <span className="error-message" style={{marginTop: '-0.5rem'}}>{errors.activeSearch}</span>}

                </div>

                <button type="submit" className="search-button">
                    Search Route
                </button>
            </form>
        </div>
    );
}
