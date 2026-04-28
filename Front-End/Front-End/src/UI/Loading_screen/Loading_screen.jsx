import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import loading_animation from '../../assets/animated_charging_station.gif'

function LoadingOverlay() {
  const [dots, setDots] = useState(1);

  useEffect(() => {
    const id = setInterval(() => {
      setDots((d) => (d % 3) + 1);
    }, 600);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(0, 0, 0, 0.2)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 99999,
    }}>
      <div style={{
        background: "#ffffff", borderRadius: 16,
        padding: "2.5rem 3rem", textAlign: "center",
        border: "2px solid #4a90e2", boxShadow: "0 4px 15px rgba(0, 0, 0, 0.3)"
      }}>
        <img src={loading_animation} alt="Loading..." style={{ width: 160, marginBottom: 10 }} />
        <p style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
          Finding you the Best Route {".".repeat(dots)}
        </p>
        <small style={{color:"gray"}}>Hang tight, this won't take long</small>
      </div>
    </div>
  );
}

export default function LoadingScreen({ isLoading }) {
  if (!isLoading) return null;
  return createPortal(<LoadingOverlay />, document.body);
}