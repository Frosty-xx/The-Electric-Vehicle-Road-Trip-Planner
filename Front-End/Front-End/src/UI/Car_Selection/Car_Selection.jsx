import './Car_Selection.css';
import { useState } from 'react';
// import coverd_car from '../../assets/coverd_car.png';
import Cars_Menu from './Cars_menu';
import Hyundai from '../../assets/Hyundai-Ioniq-5.png'

export default function Car_Selection({ }) {

    const [isOpen, setIsOpen] = useState(true)

    return (
        <div className="car-selection-container">
            <img src={Hyundai} alt="Car" className="car-image" />
            <div className="car-info">
                <h2>Hyundai Ioniq 5</h2>
                <p>Range: <span>480 km</span></p>
                <p>Battery <span>kwh: 77.4</span> </p>
                <p>Top Speed: <span>185 km/h</span></p>
            </div>
        </div>


    )


}