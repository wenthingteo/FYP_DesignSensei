import React, { useState, useRef, useEffect } from "react";
import useGetChats from "../hooks/useGetChats";
import useSidebarUpdates from '../hooks/useSidebarUpdates';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEllipsisVertical, faPen, faTrash, faCheck, faTimes } from "@fortawesome/free-solid-svg-icons";
import axios from "axios";
import API_BASE from "../config";
import { getAccessToken } from "../utils/auth";

function ConversationHistory({ onDeleteConfirmRequest }) {
  const { chatData, setChatData } = useGetChats();
  const { updateTrigger } = useSidebarUpdates();
  let conversations = chatData?.conversations ?? [];  
  const currentId = chatData?.currentConversation;
  const menuRef = useRef(null);
  const inputRef = useRef(null);

  const [activeMenuId, setActiveMenuId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setActiveMenuId(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  useEffect(() => {
    console.log('useEffect triggered with updateTrigger:', updateTrigger);
    
    if (updateTrigger > 0) {
      console.log('Sidebar update triggered, refreshing conversation list...');
      console.log('Current conversations before sorting:', conversations);
      
      if (conversations.length > 0) {
        // Sort and update the conversations
        const sortedConversations = [...conversations].sort((a, b) => {
          const timeA = new Date(a.updated_at || a.created_at);
          const timeB = new Date(b.updated_at || b.created_at);
          console.log(`Comparing ${a.title} (${timeA}) with ${b.title} (${timeB})`);
          return timeB.getTime() - timeA.getTime();
        });
        
        console.log('Sorted conversations:', sortedConversations);
        
        // Update the chatData with sorted conversations
        setChatData(prev => ({
          ...prev,
          conversations: sortedConversations
        }));
      }
    }
  }, [updateTrigger, setChatData]);

  const handleConversationClick = async (conv) => {
    if (editingId) return;

    if (conv.id === "new") {
      setChatData((prev) => ({
        ...prev,
        currentConversation: "new",
        messages: [],
      }));
      return;
    }

    try {
      const token = getAccessToken();
      const res = await axios.get(`${API_BASE}/api/conversations/${conv.id}/messages/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setChatData((prev) => ({
        ...prev,
        currentConversation: conv.id,
        messages: res.data,
      }));
      console.log(res);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const toggleMenu = (id) => {
    setActiveMenuId(prev => (prev === id ? null : id));
  };

  const startRename = (conv) => {
    setEditingId(conv.id);
    setEditingTitle(conv.title);
    setActiveMenuId(null); // Close menu
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditingTitle("");
  };

  const saveRename = async (convId) => {
    if (!editingTitle.trim()) {
      cancelRename();
      return;
    }

    try {
      console.log(`Attempting to rename conversation ${convId} to "${editingTitle.trim()}"`);
      
      const token = getAccessToken();
      const response = await axios.put(
        `${API_BASE}/api/conversations/${convId}/`,
        { 
          title: editingTitle.trim()
        },
        { 
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json' 
          } 
        }
      );

      console.log("Rename response:", response);

      if (response.status === 200) {
        setChatData((prev) => ({
          ...prev,
          conversations: prev.conversations.map((conv) =>
            conv.id === convId ? { ...conv, title: editingTitle.trim() } : conv
          ),
        }));
        setEditingId(null);
        setEditingTitle("");
        console.log("Conversation renamed successfully");
      }
    } catch (err) {
      console.error("Error renaming conversation:", err);
      console.error("Error details:", err.response?.data);
      
      let errorMessage = "Failed to rename conversation. ";
      if (err.response?.data?.error) {
        errorMessage += err.response.data.error;
      } else if (err.response?.status === 403) {
        errorMessage += "You don't have permission to rename this conversation.";
      } else if (err.response?.status === 404) {
        errorMessage += "Conversation not found.";
      } else {
        errorMessage += "Please try again.";
      }
      
      alert(errorMessage);
      cancelRename();
    }
  };

  const handleKeyPress = (e, convId) => {
    if (e.key === 'Enter') {
      saveRename(convId);
    } else if (e.key === 'Escape') {
      cancelRename();
    }
  };

  const requestDeleteConfirmation = (convId) => {
    if (onDeleteConfirmRequest) {
      onDeleteConfirmRequest(convId);
      setActiveMenuId(null); // Close the menu after clicking delete
    }
  };

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  return (
    <div>
      {conversations
        .filter(conv => conv.id !== "new")
        .map((conv) => {
        const isActive = conv.id === currentId;
        const isEditing = editingId === conv.id;

        return (
          <div key={conv.id} className="position-relative">
            <div
              className={`conversation-item d-flex align-items-center justify-content-between p-2 mb-1 ${isActive ? 'bg-grey-2' : ''}`}
              style={{ borderRadius: "6px", cursor: "pointer" }}
              onClick={() => !isEditing && handleConversationClick(conv)}
              onMouseEnter={(e) => {
                if (!isActive && !isEditing) e.currentTarget.classList.add("bg-grey-2");
              }}
              onMouseLeave={(e) => {
                if (!isActive && !isEditing) e.currentTarget.classList.remove("bg-grey-2");
              }}
            >
              {isEditing ? (
                <div className="d-flex align-items-center flex-grow-1 gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onKeyDown={(e) => handleKeyPress(e, conv.id)}
                    className="form-control form-control-sm"
                    style={{ fontSize: "1rem" }}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="d-flex gap-1">
                    <FontAwesomeIcon 
                      icon={faCheck} 
                      style={{ color: "#28a745", fontSize: "0.85rem", cursor: 'pointer' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        saveRename(conv.id);
                      }}
                    />
                    <FontAwesomeIcon 
                      icon={faTimes} 
                      style={{ color: "#dc3545", fontSize: "0.85rem", cursor: 'pointer' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelRename();
                      }}
                    />
                  </div>
                </div>
              ) : (
                <>
                  <span 
                    style={{ 
                      fontSize: "18px", 
                      color: "#333",
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      marginRight: '8px'
                    }}
                    title={conv.title}
                  >
                    {conv.title}
                  </span>
                  <div onClick={(e) => {
                    e.stopPropagation();
                    toggleMenu(conv.id);
                  }}>
                    <FontAwesomeIcon icon={faEllipsisVertical} style={{ color: "#999", fontSize: "1rem", cursor: 'pointer' }} />
                  </div>
                </>
              )}
            </div>

            {activeMenuId === conv.id && !isEditing && (
              <div
                ref={menuRef}
                className="position-absolute bg-white border rounded shadow-sm"
                style={{
                  top: '100%',
                  right: '10px',
                  zIndex: 999,
                  padding: '6px 0',
                  fontSize: '0.93rem',
                  minWidth: '120px'
                }}
              >
                <div
                  className="menu-item d-flex align-items-center gap-2"
                  style={{ 
                    padding: '8px 12px', 
                    cursor: 'pointer', 
                    color: '#333',
                    transition: 'background-color 0.2s ease'
                  }}
                  onClick={() => startRename(conv)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#EEEEEE';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <FontAwesomeIcon icon={faPen} style={{ fontSize: '1rem' }} />
                  <span>Rename</span>
                </div>
                <div
                  className="menu-item d-flex align-items-center gap-2"
                  style={{ 
                    padding: '8px 12px', 
                    cursor: 'pointer', 
                    color: '#dc3545',
                    transition: 'background-color 0.2s ease'
                  }}
                  onClick={() => requestDeleteConfirmation(conv.id)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#EEEEEE';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <FontAwesomeIcon icon={faTrash} style={{ fontSize: '1rem' }} />
                  <span>Delete</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default ConversationHistory;