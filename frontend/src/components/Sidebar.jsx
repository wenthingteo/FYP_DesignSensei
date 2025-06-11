import React from "react";
import '../colors.css';
import usagi from '../assets/usagi.png';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faCommentDots, faSearch } from '@fortawesome/free-solid-svg-icons';
import ConversationHistory from "./ConversationHistory";
import { useNavigate } from 'react-router-dom';

const Sidebar = () => {
  const navigate = useNavigate();

  const handleFeedbackClick = () => {
    navigate('/feedback');
  };

  return (
    <div className="d-flex flex-column min-vh-100 p-3 bg-grey-1" style={{ width: '350px' }}>
      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center gap-2">
          <div style={{ fontSize: '20px', fontWeight: '600', color: '#333' }}>Software Design Sensei</div>
          <div
            className="rounded-circle overflow-hidden justify-content-between"
            style={{
              width: '40px',
              height: '40px',
              flexShrink: 0,
              border: '2px solid #ccc',
              backgroundColor: '#f8f9fa',
            }}
          >
            <img
              src={usagi}
              alt="profile avatar"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: 'block',
              }}
              onError={(e) => {
                e.currentTarget.src = "https://via.placeholder.com/40";
              }}
            />
          </div>
        </div>
      </div>

      {/* New Chat & Search */}
      <div className="d-flex align-items-center justify-content-between mb-3 gap-3">
        <div
          className="d-flex align-items-center rounded-5 px-3 py-2 bg-blue-dark text-white"
          style={{
            gap: '8px',
            fontSize: '20px',
            cursor: 'pointer',
            flexGrow: 1,
            transition: 'background-color 0.2s ease-in-out',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#003366')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#004080')}
        >
          <FontAwesomeIcon icon={faPlus} size="sm" />
          <span>New Chat</span>
        </div>
        <div
          className="d-flex align-items-center justify-content-center p-3 bg-grey-3"
          style={{
            borderRadius: '100px',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease-in-out',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#e0e0e0')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#f5f5f5')}
        >
          <FontAwesomeIcon icon={faSearch} />
        </div>
      </div>

      {/* Conversation History */}
      <ConversationHistory />

      {/* Feedback Button */}
      <div className="mt-auto pt-3" style={{ borderTop: '1px solid #eee' }}>
        <div
          className="d-flex align-items-center p-2 rounded-5 gap-2"
          style={{ cursor: 'pointer', transition: 'background-color 0.2s ease-in-out' }}
          onClick={handleFeedbackClick}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8f9fa')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <FontAwesomeIcon icon={faCommentDots} style={{ color: '#666', fontSize: '18px' }} />
          <span className="d-flex align-items-center" style={{ fontSize: '18px', color: '#333' }}>
            Feedback
          </span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
