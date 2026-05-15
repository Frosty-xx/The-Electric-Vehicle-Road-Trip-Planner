import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartLine, faX, faRoute, faMapPin, faBolt, faZap, faClock } from '@fortawesome/free-solid-svg-icons';
import Battery_Graph from './Battery_Graph';
import './Statistics.css';
import Bolt from '../assets/bolt-circle.svg'

export default function Statistics({
    batteryData,
    batteryDistanceData,
    pathDistance,
    totalBatteryConsumed,
    strategy,
    isOpen,
}) {
    // Battery constants
    const BATTERY_CAPACITY_KWH = 77.4;
    
    // Calculate statistics
    const startBattery = batteryData.length > 0 ? batteryData[0].battery_level : 0;
    const endBattery = batteryData.length > 0 ? batteryData[batteryData.length - 1].battery_level : 0;
    const efficiency = pathDistance > 0 && totalBatteryConsumed > 0 
        ? (pathDistance / totalBatteryConsumed).toFixed(2) 
        : 0; // km per kWh
    const timeSpentMinutes = batteryData.length > 0 ? batteryData[batteryData.length - 1].time : 0;
    const timeSpentHours = (timeSpentMinutes / 60).toFixed(2);
    const avgSpeedMetric = pathDistance > 0 && batteryData.length > 0
        ? (pathDistance / (batteryData.length * 5 / 60)).toFixed(2)
        : 0; // Rough estimate

    // Calculate estimated range
    const estimatedRangePerPercent = batteryData.length > 0 && totalBatteryConsumed > 0
        ? (pathDistance / totalBatteryConsumed).toFixed(2)
        : 0;



    return (

        <div className="statistics-container" style={!isOpen ? { display: "none" } : {}}>
            <div className='statistics-box'>
                {/* Header */}
                <div className='statistics-header'>
                    <h2 className='statistics-title'>
                        <FontAwesomeIcon icon={faChartLine} color='#4a90e2' /> Route Statistics
                    </h2>
                </div>

                <hr style={{ border: '1px solid #ccc' }} />

                {/* Battery Graph */}
                <div className='statistics-section'>
                    <h3 className='section-title'>
                        <FontAwesomeIcon icon={faBolt} /> Battery Depletion Over Time
                    </h3>
                    {batteryData && batteryData.length > 0 ? (
                        <Battery_Graph data={batteryData} color='#d63b3b'/>
                    ) : (
                        <div className='no-data-message'>
                            <p>No battery data available. Search a route first.</p>
                        </div>
                    )}
                </div>

                <hr style={{ border: '1px solid #ccc' }} />

                {/* Battery Distance Graph */}
                <div className='statistics-section'>
                    <h3 className='section-title'>
                        <FontAwesomeIcon icon={faBolt} /> Battery Depletion Over Distance
                    </h3>
                    {batteryDistanceData && batteryDistanceData.length > 0 ? (
                        <Battery_Graph data={batteryDistanceData} graphType="distance" color='#2b7fee'/>
                    ) : (
                        <div className='no-data-message'>
                            <p>No distance data available. Search a route first.</p>
                        </div>
                    )}
                </div>

                <hr style={{ border: '1px solid #ccc' }} />

                {/* Legend */}
                <div className='statistics-section'>
                    <h3 className='section-title'>
                        <FontAwesomeIcon icon={faRoute} /> Route Legend
                    </h3>
                    <div className='legend-container'>
                        <div className='legend-item'>
                            <div className='legend-line failed'></div>
                            <span>Failed Explored Path</span>
                        </div>
                        <div className='legend-item'>
                            <div className='legend-line success'></div>
                            <span>Successful Route</span>
                        </div>
                        <div className='legend-item'>
                            <img src={Bolt} width={30}></img>
                            <span>Charging Station</span>
                        </div>
                    </div>
                </div>

                <hr style={{ border: '1px solid #ccc' }} />

                {/* Key Statistics */}
                <div className='statistics-section'>
                    <h3 className='section-title'>
                        <FontAwesomeIcon icon={faMapPin} /> Route Summary
                    </h3>
                    <div className='stats-grid'>
                        <div className='stat-card'>
                            <div className='stat-icon'>
                                <FontAwesomeIcon icon={faRoute} color='#4a90e2' />
                            </div>
                            <div className='stat-content'>
                                <p className='stat-label'>Total Distance</p>
                                <p className='stat-value'>{pathDistance > 0 ? pathDistance.toFixed(2) : '0.00'} km</p>
                            </div>
                        </div>

                        <div className='stat-card'>
                            <div className='stat-icon'>
                                <FontAwesomeIcon icon={faBolt} color='#ff9800' />
                            </div>
                            <div className='stat-content'>
                                <p className='stat-label'>Battery Used</p>
                                <p className='stat-value'>{totalBatteryConsumed.toFixed(2)} kWh</p>
                            </div>
                        </div>

                        <div className='stat-card'>
                            <div className='stat-icon'>
                                <FontAwesomeIcon icon={faZap} color='#4caf50' />
                            </div>
                            <div className='stat-content'>
                                <p className='stat-label'>Efficiency</p>
                                <p className='stat-value'>{efficiency} km/kWh</p>
                            </div>
                        </div>

                        <div className='stat-card'>
                            <div className='stat-icon'>
                                <FontAwesomeIcon icon={faClock} color='#9c27b0' />
                            </div>
                            <div className='stat-content'>
                                <p className='stat-label'>Time Spent</p>
                                <p className='stat-value'>{timeSpentHours} hrs</p>
                            </div>
                        </div>
                    </div>
                </div>

                <hr style={{ border: '1px solid #ccc' }} />

                {/* Advanced Statistics */}
                <div className='statistics-section'>
                    <h3 className='section-title'>
                        <FontAwesomeIcon icon={faChartLine} /> Advanced Metrics
                    </h3>
                    <div className='stats-list'>
                        <div className='stat-item'>
                            <span className='stat-item-label'>Search Strategy Used:</span>
                            <span className='stat-item-value'>{strategy || 'N/A'}</span>
                        </div>
                        <div className='stat-item'>
                            <span className='stat-item-label'>Range per 1% Battery:</span>
                            <span className='stat-item-value'>{estimatedRangePerPercent} km</span>
                        </div>
                        <div className='stat-item'>
                            <span className='stat-item-label'>Initial Battery Level:</span>
                            <span className='stat-item-value'>{startBattery.toFixed(2)}%</span>
                        </div>
                        <div className='stat-item'>
                            <span className='stat-item-label'>Final Battery Level:</span>
                            <span className='stat-item-value'>{endBattery.toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
