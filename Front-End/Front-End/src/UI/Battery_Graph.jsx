import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import './Battery_Graph.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBolt } from '@fortawesome/free-solid-svg-icons';

export default function Battery_Graph({ data }) {
    const batteryData = data
    const smoothedData = batteryData.filter((_, index) => index % 5 === 0);
    const FINAL_BATTERY = data.length > 0 ? data[data.length - 1].battery_level.toFixed(2) : 0;

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
                <h3 className="graph-title"> <FontAwesomeIcon icon={faBolt} color='#4a90e2' /> Battery Status</h3>
                <div className="graph-info">
                    <span className="current-battery">{FINAL_BATTERY}%</span>
                </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={smoothedData}>
                    <defs>
                        <linearGradient id="colorBattery" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4a90e2" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#4a90e2" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.19)" />
                    <XAxis
                        dataKey="distance"
                        domain={['dataMin', 'dataMax']} // Starts at 0 and ends at your max distance                       
                        tickFormatter={(value) => `${Math.round(value)}`} // Rounds 58.48... to 58
                        stroke="rgb(252, 252, 252)"
                        label={{ value: 'Distance (km)', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                        dataKey="battery_level"
                        domain={[0, 100]}
                        label={{ value: 'Battery %', angle: -90, position: 'insideLeft' }}
                        stroke="rgb(255, 255, 255)"
                        tickCount={20}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        wrapperStyle={{ paddingTop: '10px' }}
                        textColor="rgba(255, 255, 255, 0.94)"
                    />
                    <Line
                        type="linear"
                        dataKey="battery_level"
                        stroke="#4a90e2"
                        strokeWidth={3}        // Slightly thicker for a premium feel
                        dot={false}            // <-- THIS removes the "chunky" jagged look
                        activeDot={{ r: 6, strokeWidth: 0 }} // Only show dot on hover
                        fill="url(#colorBattery)"
                        isAnimationActive={true}
                        animationDuration={1500} // Slower animation looks smoother
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
