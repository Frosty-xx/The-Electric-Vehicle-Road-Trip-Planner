import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import './Battery_Graph.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBolt } from '@fortawesome/free-solid-svg-icons';

export default function Battery_Graph({ data, graphType = "time",color = "#50df24" }) {
    const batteryData = data
    // const smoothedData = batteryData.filter((_, index) => index % 5 === 0);
    const FINAL_BATTERY = data.length > 0 ? data[data.length - 1].battery_level.toFixed(2) : 0;
    const xAxisKey = graphType === "distance" ? "distance_km" : "time";
    const xAxisLabel = graphType === "distance" ? "Distance (km)" : "Time (min)";
    
    // Calculate max X value with fallback
    const maxXValue = data.length > 0 
        ? Math.max(...data.map(d => {
            const value = graphType === "distance" ? (d.distance_km || 0) : (d.time || 0);
            return isFinite(value) ? value : 0;
        }), 0)
        : 0;

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const displayLabel = graphType === "distance" 
                ? `Distance: <span>${payload[0].payload.distance_km?.toFixed(2) || 'N/A'} km</span>`
                : `Time: <span>${payload[0].payload.time?.toFixed(2) || 'N/A'} min</span>`;
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-distance" style={{color:"white"}}dangerouslySetInnerHTML={{ __html: displayLabel }}>
                    </p>
                    <p className="tooltip-battery">
                        Battery: <span style={{color:"white"}}>{payload[0].value}%</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="battery-graph-container">
            <div className="graph-header">
                <h3 className="graph-title"> <FontAwesomeIcon icon={faBolt} color={color} /> Battery Status</h3>
                <div className="graph-info">
                    <span className="current-battery" style={{color:color}}>{FINAL_BATTERY}%</span>
                </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data}>
                    <defs>
                        <linearGradient id="colorBattery" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                            <stop offset="95%" stopColor={color} stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.19)" />
                    <XAxis
                        dataKey={xAxisKey}
                        type="number"
                        domain={[0, Math.max(Math.ceil(maxXValue), 1)]}
                        tickCount={10}
                        tickFormatter={(value) => `${value.toFixed(1)}`}
                        stroke="rgb(252, 252, 252)"
                        label={{ value: xAxisLabel, position: 'insideBottom', offset: -5 }}
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
                        stroke={color}
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
