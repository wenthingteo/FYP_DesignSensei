import { createContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [chatData, setChatData] = useState({
    conversations: [],
    currentConversation: null,
    messages: []
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Helper function to get CSRF token (keep as is)
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

  const fetchChats = useCallback(async () => { // Wrap fetchChats in useCallback
    setLoading(true); // Set loading to true when fetching starts
    setError(null);    // Clear any previous errors
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
        currentConversation: response.data.current_conversation ? response.data.current_conversation.id : null,
        messages: response.data.messages || []
      }));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []); // No dependencies, so it doesn't change on re-renders

  // Fetch conversations on mount
  useEffect(() => {
    fetchChats();
  }, [fetchChats]); // Add fetchChats as a dependency to useEffect

  return (
    <ChatContext.Provider value={{ chatData, setChatData, loading, error, fetchChats }}> {/* Expose fetchChats */}
      {children}
    </ChatContext.Provider>
  );
};