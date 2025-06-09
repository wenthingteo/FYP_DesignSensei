import React from "react";
import './Sidebar.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faCircleQuestion, faGear, faHistory, faMessage, faPlus } from '@fortawesome/free-solid-svg-icons';


const Sidebar = () => {
    return (
        <div class="d-inline-flex flex-column justify-content-between min-vh-100 p-3" 
            style={{backgroundColor: '#f8f8f8'}}>
            <div class="d-inline-flex flex-column align-items-start">
                <FontAwesomeIcon style={{cursor: 'pointer'}} icon={faBars}/>
                <div className="d-inline-flex align-items-center mt-2 px-3 py-2" 
                    style={{
                        gap: '10px',
                        backgroundColor: '#e6eaf1',
                        borderRadius: '50px',
                        fontSize: '14px',
                        cursor: 'pointer'
                    }}>
                    <FontAwesomeIcon icon={faPlus}/>
                    <p>New Chat</p>
                </div>
                <div className="recent">
                    <p className="recent-title">Recent</p>
                    <div className="recent-entry">
                        <FontAwesomeIcon icon={faMessage}/>
                        <p>What is react...</p>
                    </div>
                </div>
            </div>
            <div className="bottom">
                <div className="bottom-item recent-entry">
                    <FontAwesomeIcon icon={faCircleQuestion}/>
                    <p>Help</p>
                </div>
                <div className="bottom-item recent-entry">
                    <FontAwesomeIcon icon={faHistory}/>
                    <p>Activity</p>
                </div>
                <div className="bottom-item recent-entry">
                    <FontAwesomeIcon icon={faGear}/>
                    <p>Settings</p>
                </div>
            </div>
        </div>
    )
}

export default Sidebar;