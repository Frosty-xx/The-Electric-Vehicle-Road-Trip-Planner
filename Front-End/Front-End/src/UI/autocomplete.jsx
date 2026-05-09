import { useState, useRef, useEffect, useCallback } from "react";
import './Search_Box.css';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMap } from "@fortawesome/free-solid-svg-icons";
/**
 * AddressAutocomplete
 *
 * Props:
 *  - onSelect(place)  → called with the full Nominatim result object
 *                       place.lat, place.lon, place.display_name, place.address
 *  - placeholder      → input placeholder text (optional)
 *  - countrycodes     → comma-separated ISO codes to restrict results e.g. "fr,dz" (optional)
 */
export default function AddressAutocomplete({
    id,
    onSelect,
    onChange,
    placeholder = "Search for an address...",
    countrycodes = "",
    errors = {},
    setErrors,
}) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [open, setOpen] = useState(false);
    const [activeIdx, setActiveIdx] = useState(-1);

    const timerRef = useRef(null);
    const inputRef = useRef(null);
    const rootRef = useRef(null);

    const search = useCallback(
        async (q) => {
            if (q.length < 3) {
                setResults([]);
                setOpen(false);
                return;
            }
            setLoading(true);
            try {
                const params = new URLSearchParams({
                    q,
                    format: "json",
                    addressdetails: "1",
                    limit: "6",
                    ...(countrycodes && { countrycodes }),
                });
                const res = await fetch(
                    `https://nominatim.openstreetmap.org/search?${params}`,
                    { headers: { "Accept-Language": "en", "User-Agent": "EVRoutePlanner/1.0" } }
                );
                const data = await res.json();
                setResults(data);
                setOpen(data.length > 0);
                setActiveIdx(-1);
            } catch (err) {
                console.error("Nominatim error:", err);
                setResults([]);
            } finally {
                setLoading(false);
            }
        },
        [countrycodes]
    );

    const handleChange = (e) => {
        const v = e.target.value;
        setQuery(v);
        setErrors?.(prev => ({ ...prev, [id]: null })); // Clear error on typing
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => search(v), 350);
        onChange?.(v);
    };

    const handleSelect = (place) => {
        setQuery(place.display_name);
        setErrors?.(prev => ({ ...prev, [id]: null })); // Clear error on selection
        setOpen(false);
        setResults([]);
        onSelect?.({
            ...place,
            lat: parseFloat(place.lat),
            lon: parseFloat(place.lon),
        });
    };

    const handleKeyDown = (e) => {
        if (!open) return;
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setActiveIdx((i) => Math.min(i + 1, results.length - 1));
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActiveIdx((i) => Math.max(i - 1, 0));
        } else if (e.key === "Enter" && activeIdx >= 0) {
            e.preventDefault();
            handleSelect(results[activeIdx]);
        } else if (e.key === "Escape") {
            setOpen(false);
        }
    };

    const handleClear = () => {
        setQuery("");
        setResults([]);
        setOpen(false);
        onChange?.("");
        inputRef.current?.focus();
    };

    // Close dropdown on outside click
    useEffect(() => {
        const handler = (e) => {
            if (!rootRef.current?.contains(e.target)) setOpen(false);
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    return (
        <div ref={rootRef} style={{ position: "relative", width: "100%" }}>
            {/* Input */}
            <div style={{ display: "flex", position: "relative", alignItems: "center" }} >
                <span
                    style={{
                        position: "absolute",
                        right: query ? 32 : 8,
                        fontSize: 14,
                        color: "#888",
                        pointerEvents: "none",
                        userSelect: "none",

                    }}
                >
                    {loading ? "⟳" : ""}
                </span>
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    onFocus={() => results.length > 0 && setOpen(true)}
                    placeholder={placeholder}
                    aria-autocomplete="list"
                    aria-expanded={open}
                    aria-haspopup="listbox"
                    className={`search-input ${errors[id] ? 'input-error' : ''}`}
                />
                {query && (
                    <button
                        onClick={handleClear}
                        style={{
                            position: "absolute",
                            right: 8,
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            color: "#aaa",
                            fontSize: 13,
                            padding: "2px 4px",
                            lineHeight: 1,
                        }}
                        aria-label="Clear"
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* Dropdown */}
            {open && (
                <ul
                    role="listbox"
                    style={{
                        position: "absolute",
                        top: "calc(100% + 4px)",
                        left: 0,
                        right: 0,
                        zIndex: 1000,
                        margin: 0,
                        padding: 0,
                        listStyle: "none",
                        background: "#fff",
                        border: "1px solid #ddd",
                        borderRadius: 8,
                        overflow: "hidden",
                        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                    }}
                >
                    {results.map((r, i) => {
                        const primary =
                            r.address?.road ||
                            r.address?.amenity ||
                            r.address?.neighbourhood ||
                            r.name ||
                            r.display_name.split(",")[0];
                        const secondary = [
                            r.address?.city || r.address?.town || r.address?.village,
                            r.address?.country,
                        ]
                            .filter(Boolean)
                            .join(", ");

                        return (
                            <li
                                key={r.place_id}
                                role="option"
                                aria-selected={i === activeIdx}
                                onMouseDown={() => handleSelect(r)}
                                onMouseEnter={() => setActiveIdx(i)}
                                style={{
                                    padding: "9px 12px",
                                    cursor: "pointer",
                                    color: i === activeIdx ? "#3085e6" : "#333",
                                    background: i === activeIdx ? "#f5f5f5" : "transparent",
                                    borderBottom: i < results.length - 1 ? "1px solid #f0f0f0" : "none",
                                    display: "flex",
                                    gap: 10,
                                    alignItems: "flex-start",
                                }}
                            >
                                <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
                                    <FontAwesomeIcon icon={faMap} color="#3085e6" />
                                    <div style={{ minWidth: 0 }}>
                                        <div
                                            style={{
                                                fontSize: 13,
                                                fontWeight: 500,
                                                whiteSpace: "nowrap",
                                                overflow: "hidden",
                                                textOverflow: "ellipsis",
                                            }}
                                        >
                                            {primary}
                                        </div>
                                        {secondary && (
                                            <div
                                                style={{
                                                    fontSize: 12,
                                                    color: "#888",
                                                    marginTop: 2,
                                                    whiteSpace: "nowrap",
                                                    overflow: "hidden",
                                                    textOverflow: "ellipsis",
                                                }}
                                            >
                                                {secondary}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </li>
                        );
                    })}
                    <li
                        style={{
                            padding: "5px 12px",
                            fontSize: 11,
                            color: "#bbb",
                            textAlign: "right",
                            borderTop: "1px solid #f0f0f0",
                            listStyle: "none",
                        }}
                    >
                        © OpenStreetMap contributors
                    </li>
                </ul>
            )}
        </div>
    );
}
