import React, { useContext } from "react";
import '../colors.css';
import usagi from '../assets/usagi.png';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faCommentDots, faSearch } from '@fortawesome/free-solid-svg-icons';
import ConversationHistory from "./ConversationHistory";
import { useNavigate } from 'react-router-dom';
import useCreateChat from '../hooks/useCreateChat';
import { ChatContext } from "../context/ChatContext";

// Sidebar now accepts onDeleteConfirmRequest prop
const Sidebar = ({ onDeleteConfirmRequest }) => {
  const navigate = useNavigate();
  const { setChatData } = useContext(ChatContext);
  const createNewChat = useCreateChat(setChatData);

  const handleFeedbackClick = () => {
    navigate('/feedback');
  };

  return (
    <div className="d-flex flex-column min-vh-100 p-3 bg-grey-1" style={{ width: '100%', maxWidth: '350px' }}>
      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center gap-2">
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>Software Design Sensei</div>
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
            fontSize: '14px',
            cursor: 'pointer',
            flexGrow: 1,
            transition: 'background-color 0.2s ease-in-out',
          }}
          onClick={createNewChat}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2C5E97')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3980D0')}
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
      <ConversationHistory onDeleteConfirmRequest={onDeleteConfirmRequest} />

      {/* Feedback Button */}
      <div className="mt-auto pt-3" style={{ borderTop: '1px solid #eee' }}>
        <div
          className="d-flex align-items-center p-3 gap-2 rounded"
          style={{ cursor: 'pointer', transition: 'background-color 0.2s ease-in-out' }}
          onClick={handleFeedbackClick}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#e0e0e0')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <FontAwesomeIcon icon={faCommentDots} style={{ color: '#666', fontSize: '14px' }} />
          <span className="d-flex align-items-center" style={{ fontSize: '14px', color: '#333' }}>
            Feedback
          </span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;