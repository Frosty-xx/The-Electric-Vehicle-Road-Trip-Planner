import { useState, useMemo, useEffect } from 'react'
import ReactDOM from 'react-dom'
import './Cars_menu.css'

const EV_CARS = [
  {
    id: 1,
    label: 'Hyundai Ioniq 5',
    brand: 'Hyundai',
    range: 481,
    battery: 77.4,
    power: 225,
    charge: '800V · 350kW DC',
    year: 2024,
    tag: 'Midsize SUV',
  },
  {
    id: 2,
    label: 'Tesla Model 3',
    brand: 'Tesla',
    range: 576,
    battery: 82.0,
    power: 358,
    charge: '250kW DC',
    year: 2024,
    tag: 'Sedan',
  },
  {
    id: 3,
    label: 'Kia EV6',
    brand: 'Kia',
    range: 528,
    battery: 77.4,
    power: 239,
    charge: '800V · 350kW DC',
    year: 2024,
    tag: 'Crossover',
  },
  {
    id: 4,
    label: 'BMW iX',
    brand: 'BMW',
    range: 630,
    battery: 111.5,
    power: 385,
    charge: '200kW DC',
    year: 2024,
    tag: 'Luxury SUV',
  },
  {
    id: 5,
    label: 'Mercedes EQS',
    brand: 'Mercedes',
    range: 780,
    battery: 107.8,
    power: 245,
    charge: '200kW DC',
    year: 2024,
    tag: 'Luxury Sedan',
  },
  {
    id: 6,
    label: 'Renault Megane E-Tech',
    brand: 'Renault',
    range: 470,
    battery: 60.0,
    power: 160,
    charge: '130kW DC',
    year: 2024,
    tag: 'Compact',
  },
  {
    id: 7,
    label: 'Volkswagen ID.4',
    brand: 'Volkswagen',
    range: 522,
    battery: 82.0,
    power: 210,
    charge: '135kW DC',
    year: 2024,
    tag: 'SUV',
  },
  {
    id: 8,
    label: 'Audi Q4 e-tron',
    brand: 'Audi',
    range: 520,
    battery: 82.0,
    power: 220,
    charge: '135kW DC',
    year: 2024,
    tag: 'SUV',
  },
]

const BRAND_INITIALS = {
  Hyundai: 'HY',
  Tesla: 'TS',
  Kia: 'KI',
  BMW: 'BM',
  Mercedes: 'ME',
  Renault: 'RE',
  Volkswagen: 'VW',
  Audi: 'AU',
}

const BRAND_COLORS = {
  Hyundai: '#00c6ff',
  Tesla: '#e82127',
  Kia: '#05141f',
  BMW: '#1c69d4',
  Mercedes: '#9ea4a9',
  Renault: '#efdf00',
  Volkswagen: '#001e50',
  Audi: '#bb0a30',
}

function Cars_Menu({ isOpen, setIsOpen }) {

  // Fetch car data from backend here and store in state:
  const [evData, setEvData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // We are using ID 45011 (2022 Hyundai Ioniq 5 Long Range RWD)
  const vehicleId = "45011";

  useEffect(() => {
    const fetchAllEVs = async () => {
      try {
        // This CSV contains ALL vehicles, all years — no pagination needed
        const response = await fetch(
          "https://corsproxy.io/?https://www.fueleconomy.gov/feg/epadata/vehicles.csv"
        );
        const csvText = await response.text();

        // Parse CSV manually (or use papaparse if available)
        const lines = csvText.split("\n");
        const headers = lines[0].split(",").map(h => h.trim().replace(/"/g, ""));

        const results = [];

        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(",").map(c => c.trim().replace(/"/g, ""));
          if (cols.length < 2) continue;

          const row = {};
          headers.forEach((h, idx) => row[h] = cols[idx] || "");

          // Filter only EVs: combE > 0 means it has electric consumption data
          const kwhPer100Miles = parseFloat(row["combE"] || 0);
          if (kwhPer100Miles === 0) continue;

          const rangeMiles = parseFloat(row["range"] || 0);
          const rangeKm = Math.round(rangeMiles * 1.60934);
          const consumptionKwhPerKm = Number(((kwhPer100Miles / 100) / 1.60934).toFixed(5));
          const derivedBatteryKwh = Number((rangeMiles * (kwhPer100Miles / 100)).toFixed(1));

          results.push({
            id: row["id"],
            year: row["year"],
            name: `${row["make"]} ${row["model"]}`,
            battery_kwh: derivedBatteryKwh,
            range_km: rangeKm,
            consumption_kwh_per_km: consumptionKwhPerKm,
          });
        }

        setEvData(results);
      } catch (err) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAllEVs();
    console.log("EV Data:", evData);
  }, []);




  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState(null)

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return EV_CARS
    return EV_CARS.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        c.brand.toLowerCase().includes(q) ||
        c.tag.toLowerCase().includes(q)
    )
  }, [query])

  if (!isOpen) return null

  return ReactDOM.createPortal(
    <div className="cm-overlay" onClick={() => setIsOpen(false)}>
      <div className="cm-panel" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="cm-header">
          <div>
            <h2 className="cm-title">Choose you Car</h2>
            <p className="cm-subtitle">{EV_CARS.length} electric vehicles</p>
          </div>
          <button className="cm-close" onClick={() => setIsOpen(false)} aria-label="Close">
            ×
          </button>
        </div>

        {/* Search */}
        <div className="cm-search-wrapper">
          <input
            className="cm-search"
            type="text"
            placeholder="Search by name, brand or type…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          {query && (
            <button className="cm-search-clear" onClick={() => setQuery('')}>
              ×
            </button>
          )}
        </div>

        {/* Count */}
        <div className="cm-count">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''}
          {query && <span className="cm-count-query"> for "{query}"</span>}
        </div>

        {/* List */}
        <div className="cm-list">
          {filtered.length === 0 ? (
            <div className="cm-empty">
              <span className="cm-empty-icon">🔌</span>
              <p>No vehicles match your search.</p>
            </div>
          ) : (
            filtered.map((car) => (
              <div
                key={car.id}
                className={`cm-card ${selectedId === car.id ? 'cm-card--active' : ''}`}
                onClick={() => setSelectedId(selectedId === car.id ? null : car.id)}
              >
                {/* Left: Badge */}
                <div
                  className="cm-badge"
                  style={{ '--badge-color': BRAND_COLORS[car.brand] }}
                >
                  {BRAND_INITIALS[car.brand]}
                </div>

                {/* Center: Name + Tag */}
                <div className="cm-card-main">
                  <span className="cm-car-name">{car.label}</span>
                  <span className="cm-car-tag">{car.tag}</span>
                </div>

                {/* Right: Stats */}
                <div className="cm-stats">
                  <div className="cm-stat">
                    <span className="cm-stat-val">{car.range}</span>
                    <span className="cm-stat-lbl">km</span>
                  </div>
                  <div className="cm-stat">
                    <span className="cm-stat-val">{car.battery}</span>
                    <span className="cm-stat-lbl">kWh</span>
                  </div>
                  <div className="cm-stat">
                    <span className="cm-stat-val">{car.power}</span>
                    <span className="cm-stat-lbl">kW</span>
                  </div>
                </div>

                {/* Expanded detail */}
                {selectedId === car.id && (
                  <div className="cm-detail">
                    <div className="cm-detail-row">
                      <span className="cm-detail-key">Charge Speed</span>
                      <span className="cm-detail-val">{car.charge}</span>
                    </div>
                    <div className="cm-detail-row">
                      <span className="cm-detail-key">Model Year</span>
                      <span className="cm-detail-val">{car.year}</span>
                    </div>
                    <div className="cm-detail-row">
                      <span className="cm-detail-key">WLTP Range</span>
                      <span className="cm-detail-val">{car.range} km</span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}

export default Cars_Menu
