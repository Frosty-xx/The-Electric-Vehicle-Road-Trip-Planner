import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'
import './TunisiaNotificationPortal.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleExclamation } from '@fortawesome/free-solid-svg-icons'

function TunisiaNotificationPortal() {
  const [isOpen, setIsOpen] = useState(true)

  useEffect(() => {
    // Portal opens automatically on page load
    setIsOpen(true)
  }, [])

  if (!isOpen) return null

  return ReactDOM.createPortal(
    <div className="notification-overlay">
      <div className="notification-modal">
        <button
          className="notification-close-btn"
          onClick={() => setIsOpen(false)}
          aria-label="Close notification"
        >
          ×
        </button>
        
        <div className="notification-header">
          <h2>Important Notice</h2>
        </div>
        
        <div className="notification-content">
          <p className="notification-text">
            The current search functionality is <strong>only available in <span style={{color:"tomato"}}>Tunisia</span></strong>.
          </p>
          <p className="notification-subtext">
            We're working on expanding to other regions soon. Thank you for your patience!
          </p>
        </div>
        
        <button
          className="notification-action-btn"
          onClick={() => setIsOpen(false)}
        >
          Got it
        </button>
      </div>
    </div>,
    document.body
  )
}

export default TunisiaNotificationPortal
