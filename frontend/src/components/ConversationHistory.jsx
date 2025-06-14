import React, { useState, useRef, useEffect } from "react";
import useGetChats from "../hooks/useGetChats";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEllipsisVertical, faPen, faTrash, faCheck, faTimes } from "@fortawesome/free-solid-svg-icons";
import axios from "axios";

function ConversationHistory() {
  const { chatData, setChatData } = useGetChats();
  const conversations = chatData?.conversations ?? [];
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

  const handleConversationClick = async (conv) => {
    if (editingId) return;

    // Skip API call if clicking on a "new" conversation state
    if (conv.id === "new") {
      setChatData((prev) => ({
        ...prev,
        currentConversation: "new",
        messages: [],
      }));
      return;
    }

    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/conversations/${conv.id}/messages/`, {
        withCredentials: true,
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
      // Use PATCH instead of PUT for partial updates
      const response = await axios.patch(
        `http://127.0.0.1:8000/api/conversations/${convId}/`,
        { title: editingTitle.trim() },
        { 
          withCredentials: true, 
          headers: { 
            'X-CSRFToken': getCookie('csrftoken'), 
            'Content-Type': 'application/json' 
          } 
        }
      );

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
      
      // Try alternative approach with PUT if PATCH fails
      try {
        // Get the current conversation data first
        const currentConv = conversations.find(c => c.id === convId);
        const response = await axios.put(
          `http://127.0.0.1:8000/api/conversations/${convId}/`,
          { 
            title: editingTitle.trim(),
            // Include other required fields if needed
            created_at: currentConv?.created_at || new Date().toISOString(),
          },
          { 
            withCredentials: true, 
            headers: { 
              'X-CSRFToken': getCookie('csrftoken'), 
              'Content-Type': 'application/json' 
            } 
          }
        );

        if (response.status === 200) {
          setChatData((prev) => ({
            ...prev,
            conversations: prev.conversations.map((conv) =>
              conv.id === convId ? { ...conv, title: editingTitle.trim() } : conv
            ),
          }));
          setEditingId(null);
          setEditingTitle("");
          console.log("Conversation renamed successfully with PUT");
        }
      } catch (putErr) {
        console.error("Both PATCH and PUT failed:", putErr);
        alert("Failed to rename conversation. Please try again.");
        cancelRename();
      }
    }
  };

  const handleKeyPress = (e, convId) => {
    if (e.key === 'Enter') {
      saveRename(convId);
    } else if (e.key === 'Escape') {
      cancelRename();
    }
  };

  const deleteConversation = async (convId) => {
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;
    
    try {
      const response = await axios.delete(
        `http://127.0.0.1:8000/api/conversations/${convId}/`,
        { 
          withCredentials: true, 
          headers: { 
            'X-CSRFToken': getCookie('csrftoken'), 
            'Content-Type': 'application/json' 
          } 
        }
      );
      
      if (response.status === 204 || response.status === 200) {
        setChatData((prev) => {
          const updatedConversations = prev.conversations.filter(
            (conv) => conv.id !== convId
          );
          let newCurrentConversation = prev.currentConversation;
          if (newCurrentConversation === convId) {
            newCurrentConversation = updatedConversations.length > 0 ? updatedConversations[0].id : null;
          }
          return {
            ...prev,
            conversations: updatedConversations,
            currentConversation: newCurrentConversation,
            messages: newCurrentConversation === null ? [] : 
                     newCurrentConversation === prev.currentConversation ? [] : prev.messages
          };
        });
        setActiveMenuId(null);
        console.log("Conversation deleted successfully");
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
      alert("Failed to delete conversation. Please try again.");
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
        .filter(conv => conv.id !== "new") // Filter out the "new" state from display
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
                    style={{ fontSize: "16px" }}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="d-flex gap-1">
                    <FontAwesomeIcon 
                      icon={faCheck} 
                      style={{ color: "#28a745", fontSize: "12px", cursor: 'pointer' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        saveRename(conv.id);
                      }}
                    />
                    <FontAwesomeIcon 
                      icon={faTimes} 
                      style={{ color: "#dc3545", fontSize: "12px", cursor: 'pointer' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelRename();
                      }}
                    />
                  </div>
                </div>
              ) : (
                <>
                  <span style={{ fontSize: "18px", color: "#333" }}>{conv.title}</span>
                  <div onClick={(e) => {
                    e.stopPropagation();
                    toggleMenu(conv.id);
                  }}>
                    <FontAwesomeIcon icon={faEllipsisVertical} style={{ color: "#999", fontSize: "14px", cursor: 'pointer' }} />
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
                  padding: '6px 10px',
                  fontSize: '14px',
                  minWidth: '120px'
                }}
              >
                <div
                  className="d-flex align-items-center gap-2"
                  style={{ padding: '4px 0', cursor: 'pointer', color: '#333' }}
                  onClick={() => startRename(conv)}
                >
                  <FontAwesomeIcon icon={faPen} />
                  <span>Rename</span>
                </div>
                <div
                  className="d-flex align-items-center gap-2"
                  style={{ padding: '4px 0', cursor: 'pointer', color: 'red' }}
                  onClick={() => deleteConversation(conv.id)}
                >
                  <FontAwesomeIcon icon={faTrash} />
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