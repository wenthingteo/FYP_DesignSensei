import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [chatData, setChatData] = useState({
    conversations: [],
    currentConversation: null, // Changed from current_conversation to currentConversation
    messages: []
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch conversations on mount
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/chat/", {
          withCredentials: true,
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
          }
        });

        setChatData((prev) => ({
          ...prev,
          conversations: response.data.conversations || [],
          currentConversation: response.data.current_conversation ? response.data.current_conversation.id : null, // Set currentConversation from backend response
          messages: response.data.messages || [] // Populate messages from initial fetch
        }));
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchChats();
  }, []);

  // Helper function to get CSRF token
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
    <ChatContext.Provider value={{ chatData, setChatData, loading, error }}>
      {children}
    </ChatContext.Provider>
  );
};