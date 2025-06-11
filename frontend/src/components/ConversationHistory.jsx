import React, { useState, useRef, useEffect } from "react";
import useGetChats from "../hooks/useGetChats";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEllipsisVertical, faPen, faTrash } from "@fortawesome/free-solid-svg-icons";
import axios from "axios";

function ConversationHistory() {
  const { chatData, setChatData } = useGetChats();
  const conversations = chatData?.conversations ?? [];
  const currentId = chatData?.currentConversation;
  const menuRef = useRef(null);

  const [activeMenuId, setActiveMenuId] = useState(null);

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

  const handleConversationClick = async (conv) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/chat/${conv.id}/messages/`);
      setChatData((prev) => ({
        ...prev,
        current_conversation: conv,
        messages: res.data
      }));
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const toggleMenu = (id) => {
    setActiveMenuId(prev => (prev === id ? null : id));
  };

  const renameConversation = async (id) => {
    const newTitle = prompt("Enter new conversation title:");
    if (!newTitle) return;

    try {
      const response = await fetch('/api/chatbot/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cid: id,
          title: newTitle,
        }),
      });

      if (!response.ok) throw new Error("Failed to rename conversation");

      const data = await response.json();

      // Update local state
      setChatData((prevData) => ({
        ...prevData,
        conversations: prevData.conversations.map((conv) =>
          conv.id === id ? { ...conv, title: data.title } : conv
        ),
      }));

      setActiveMenuId(null);
    } catch (err) {
      alert("Error renaming conversation");
      console.error(err);
    }
  };

  const deleteConversation = async (id) => {
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;

    try {
      const response = await fetch(`/api/chatbot/?cid=${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error("Failed to delete conversation");

      setChatData((prevData) => {
        const updatedConvs = prevData.conversations.filter(conv => conv.id !== id);
        const newCurrent = prevData.currentConversation === id
          ? (updatedConvs[0]?.id || null)
          : prevData.currentConversation;

        return {
          conversations: updatedConvs,
          currentConversation: newCurrent,
        };
      });

      setActiveMenuId(null);
    } catch (err) {
      alert("Error deleting conversation");
      console.error(err);
    }
  };

  return (
    <div>
      {conversations.map((conv) => {
        const isActive = conv.id === currentId;

        return (
          <div key={conv.id} className="position-relative">
            <div
              className={`conversation-item d-flex align-items-center justify-content-between p-2 mb-1 ${isActive ? 'bg-grey-2' : ''}`}
              style={{ borderRadius: "6px", cursor: "pointer" }}
              onClick={() => handleConversationClick(conv.id)}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.classList.add("bg-grey-2");
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.classList.remove("bg-grey-2");
              }}
            >
              <span style={{ fontSize: "18px", color: "#333" }}>{conv.title}</span>
              <div onClick={(e) => {
                e.stopPropagation();
                toggleMenu(conv.id);
              }}>
                <FontAwesomeIcon icon={faEllipsisVertical} style={{ color: "#999", fontSize: "14px", cursor: 'pointer' }} />
              </div>
            </div>

            {activeMenuId === conv.id && (
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
                  onClick={() => renameConversation(conv.id)}
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
