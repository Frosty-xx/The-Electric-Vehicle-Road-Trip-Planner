import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'
import { faCircleExclamation } from '@fortawesome/free-solid-svg-icons'
import battery_warning from '../../assets/battery_warning.gif'
import './battery_warning.css'

function Battery_warning({isOpen=false, setIsOpen}) {


    if (!isOpen) return null

    return ReactDOM.createPortal(
        <div style={{
            position: "fixed", inset: 0,
            background: "rgba(0, 0, 0, 0.2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 99999,
        }}>
            <div style={{
                background: "#ffffff", borderRadius: 16,
                padding: "2.5rem 3rem", textAlign: "center",
                border: "2px solid red", boxShadow: "0 4px 15px rgba(0, 0, 0, 0.3)",
                position: "relative",
                width: "90%", maxWidth:500,
            }}
            className='fade-in-element'
            >
                <button
                    className="notification-close-btn"
                    onClick={() => setIsOpen(false)}
                    aria-label="Close notification"
                >
                    ×
                </button>
                <img src={battery_warning} alt="Loading..." style={{ width: 160, marginBottom: 10 }} />
                <p style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
                    Insufficient battery level!
                </p>
                <small style={{ color: "gray" }}>Please charge your battery</small>
                <button
                    className="notification-action-btn"
                    onClick={() => setIsOpen(false)}
                    style={{backgroundColor:"red",marginTop: 20}}
                >
                    Got it
                </button>
            </div>
        </div>,
        document.body
    )
}

export default Battery_warning
