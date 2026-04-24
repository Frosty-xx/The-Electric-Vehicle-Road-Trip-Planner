import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import './Battery_Graph.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBolt } from '@fortawesome/free-solid-svg-icons';

export default function Battery_Graph() {
    // Sample data - replace with real data from backend
    const [batteryData] = useState([
        { distance: 0, battery: 100 },
        { distance: 15, battery: 88 },
        { distance: 30, battery: 76 },
        { distance: 45, battery: 72 },
        { distance: 60, battery: 65 },
        { distance: 75, battery: 80 },
        { distance: 90, battery: 50 },
        { distance: 105, battery: 42 },
        { distance: 120, battery: 35 },
        { distance: 135, battery: 28 },
        { distance: 150, battery: 22 },
        { distance: 165, battery: 18 },
        { distance: 180, battery: 100 }
    ]);
    const CURRENT_BATTERY = 80

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-distance">
                        Distance: <span>{payload[0].payload.distance} km</span>
                    </p>
                    <p className="tooltip-battery">
                        Battery: <span>{payload[0].value}%</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="battery-graph-container">
            <div className="graph-header">
                <h3 className="graph-title"> <FontAwesomeIcon icon={faBolt} color='#4a90e2'/> Battery Status</h3>
                <div className="graph-info">
                    <span className="current-battery">{CURRENT_BATTERY}%</span>
                </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={batteryData}>
                    <defs>
                        <linearGradient id="colorBattery" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4a90e2" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#4a90e2" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                        dataKey="distance" 
                        label={{ value: 'Distance (km)', position: 'insideBottom', offset: -5 }}
                        stroke="rgb(0, 0, 0)"
                    />
                    <YAxis 
                        domain={[0, 100]}
                        label={{ value: 'Battery %', angle: -90, position: 'insideLeft' }}
                        stroke="rgb(0, 0, 0)"
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                        wrapperStyle={{ paddingTop: '10px' }}
                        textColor="rgba(255, 255, 255, 0.94)"
                    />
                    <Line 
                        type="monotone" 
                        dataKey="battery" 
                        stroke="#4a90e2" 
                        strokeWidth={2}
                        dot={{ fill: '#4a90e2', r: 3 }}
                        activeDot={{ r: 6 }}
                        fill="url(#colorBattery)"
                        isAnimationActive={true}
                        animationDuration={800}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
