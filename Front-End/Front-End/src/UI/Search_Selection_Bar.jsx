import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBolt, faNetworkWired, faStar } from '@fortawesome/free-solid-svg-icons';
import './Search_Selection_Bar.css';

export default function Nav_Bar({ activeSearch, setActiveSearch }) {
    const searchMethods = [
        {
            id: 'Greedy',
            label: 'Greedy Search',
            icon: faBolt,
            description: 'Fast greedy approach'
        },
        {
            id: 'BFS',
            label: 'BFS',
            icon: faNetworkWired,
            description: 'Breadth-First Search'
        },
        {
            id: 'A*',
            label: 'A*',
            icon: faStar,
            description: 'A* Algorithm'
        }
    ];

    const handleAlgorithmSelection = (id) => {
        setActiveSearch(id);
        // Only selects the algorithm - search is not initiated here
    };

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {searchMethods.map((method) => (                    <button
                        key={method.id}
                        type="button"
                        className={`nav-item ${activeSearch === method.id ? 'active' : ''}`}
                        onClick={() => handleAlgorithmSelection(method.id)}
                        title={method.description}
                    >
                        <FontAwesomeIcon icon={method.icon} className="nav-icon" />
                        <span className="nav-label">{method.label}</span>
                    </button>
                ))}
            </div>
        </nav>
    );
}
