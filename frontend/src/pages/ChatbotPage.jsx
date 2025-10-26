import React, { useContext, useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from 'react-router-dom';
import axios from "axios";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faPaperPlane, faSignOutAlt } from '@fortawesome/free-solid-svg-icons';
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";
import Sidebar from "../components/Sidebar";
import WelcomePage from "../components/WelcomePage";
import { ChatContext } from "../context/ChatContext";
import useSendMessage from "../hooks/useSendMessage";
import useSidebarUpdates from '../hooks/useSidebarUpdates';
import './ChatbotPage.css';
import DeleteConfirmationModal from "../components/DeleteConfirmationModal";

const ChatbotPage = () => {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarRef = useRef(null);
  const toggleButtonRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { chatData, setChatData } = useContext(ChatContext);
  const { messages, currentConversation, conversations } = chatData;
  const { triggerSidebarUpdate } = useSidebarUpdates();

  const [typingMessageContent, setTypingMessageContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  // NEW: Store full AI response for tab switching recovery
  const fullAiResponseRef = useRef("");
  const typingIntervalRef = useRef(null);
  const currentIndexRef = useRef(0);

  const [showWelcomePage, setShowWelcomePage] = useState(
    currentConversation === "new" || (!currentConversation && messages.length === 0)
  );
  const [transitioning, setTransitioning] = useState(false);

  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [conversationToDeleteId, setConversationToDeleteId] = useState(null);

  const sendMessage = useSendMessage(
    chatData, 
    setChatData, 
    setTypingMessageContent, 
    setIsTyping,
    fullAiResponseRef,
    typingIntervalRef,
    currentIndexRef
  );
  const currentConv = conversations.find(c => c.id === currentConversation);

  const currentMessages = messages.filter(m =>
    m && m.conversation === currentConversation && m.id !== 'typing-ai-message'
  );

  // --- NEW: Handle tab visibility changes ---
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden" && isTyping && fullAiResponseRef.current) {
        // User switched tabs while typing - show full response immediately
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current);
          typingIntervalRef.current = null;
        }
        
        setIsTyping(false);
        setTypingMessageContent("");
        
        // Add the full AI message to chat - DON'T filter anything, just add the bot message
        setChatData((prev) => {
          // Check if this exact message already exists to avoid duplicates
          const messageExists = prev.messages.some(
            m => m.content === fullAiResponseRef.current && m.sender === 'bot' && m.conversation === prev.currentConversation
          );
          
          if (!messageExists) {
            return {
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id: `ai-${Date.now()}`,
                  sender: 'bot',
                  content: fullAiResponseRef.current,
                  conversation: prev.currentConversation,
                  timestamp: new Date().toISOString(),
                }
              ],
            };
          }
          return prev;
        });
        
        // Clear refs
        fullAiResponseRef.current = "";
        currentIndexRef.current = 0;
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isTyping, setChatData]);

  // --- Scroll to bottom when new messages appear ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages, typingMessageContent]);

  // --- Sidebar toggle logic ---
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target) &&
        toggleButtonRef.current &&
        !toggleButtonRef.current.contains(event.target)
      ) {
        setSidebarOpen(false);
      }
    };

    if (sidebarOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.body.style.overflow = "hidden";
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
      document.body.style.overflow = "auto";
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.body.style.overflow = "auto";
    };
  }, [sidebarOpen]);

  // --- Auto focus input ---
  useEffect(() => {
    inputRef.current?.focus();
  }, [currentConversation, showWelcomePage]);

  const getCookie = (name) => {
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
  };

  // --- Send message (main logic) ---
  const handleSend = async (messageContentToSend = inputValue.trim()) => {
    if (!messageContentToSend) return;
    setInputValue("");

    // For new conversation
    if (chatData.currentConversation === "new" || !chatData.currentConversation) {
      try {
        setTypingMessageContent("");
        setIsTyping(true);

        const response = await fetch("http://127.0.0.1:8000/api/chat/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "include",
          body: JSON.stringify({
            content: messageContentToSend,
            conversation: null,
          }),
        });

        if (!response.ok) throw new Error("Failed to create conversation");

        const data = await response.json();
        const { conversation_id, user_message, ai_response } = data;

        const newConversation = {
          id: conversation_id,
          title: messageContentToSend.substring(0, 50) || "New Conversation",
          created_at: new Date().toISOString(),
        };

        setChatData((prev) => ({
          ...prev,
          conversations: [newConversation, ...prev.conversations],
          currentConversation: conversation_id,
          messages: prev.messages.concat([user_message]),
        }));

        triggerSidebarUpdate();

        const fullAiResponseContent = ai_response.content;
        fullAiResponseRef.current = fullAiResponseContent;
        currentIndexRef.current = 0;
        
        const typingSpeed = 0.5;

        // Clear any existing interval
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current);
        }

        typingIntervalRef.current = setInterval(() => {
          if (currentIndexRef.current < fullAiResponseContent.length) {
            setTypingMessageContent(fullAiResponseContent.substring(0, currentIndexRef.current + 20));
            currentIndexRef.current += 20;
          } else {
            clearInterval(typingIntervalRef.current);
            typingIntervalRef.current = null;
            setIsTyping(false);
            setTypingMessageContent("");
            setChatData((prev) => ({
              ...prev,
              messages: prev.messages.concat([
                { ...ai_response, content: fullAiResponseContent },
              ]),
            }));
            fullAiResponseRef.current = "";
            currentIndexRef.current = 0;
          }
        }, typingSpeed);

        setInputValue("");
        return;
      } catch (error) {
        console.error("Error creating conversation:", error);
        setIsTyping(false);
        setTypingMessageContent("");
        fullAiResponseRef.current = "";
        currentIndexRef.current = 0;
        return;
      }
    }

    // Existing conversation
    await sendMessage(messageContentToSend);
  };

  // --- Cleanup on unmount ---
  useEffect(() => {
    return () => {
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
      }
    };
  }, []);

  // --- Handle Enter to send ---
  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFirstMessageSend = useCallback(async (messageContent) => {
    setTransitioning(true);
    await handleSend(messageContent);

    setTimeout(() => {
      setShowWelcomePage(false);
      setTransitioning(false);
    }, 700);
  }, [chatData, setChatData, sendMessage, handleSend]);

  // --- Welcome page transition logic ---
  useEffect(() => {
    const shouldShow = currentConversation === "new" || (!currentConversation && messages.length === 0);
    if (showWelcomePage !== shouldShow) {
      if (showWelcomePage && !shouldShow) {
        setTransitioning(true);
        setTimeout(() => {
          setShowWelcomePage(shouldShow);
          setTransitioning(false);
        }, 700);
      } else {
        setShowWelcomePage(shouldShow);
      }
    }
  }, [currentConversation, messages, showWelcomePage]);

  // --- Delete conversation modal logic ---
  const openConfirmModal = useCallback((convId) => {
    setConversationToDeleteId(convId);
    setShowConfirmModal(true);
  }, []);

  const closeConfirmModal = useCallback(() => {
    setShowConfirmModal(false);
    setConversationToDeleteId(null);
  }, []);

  const handleDeleteConversationConfirmed = useCallback(async () => {
    if (!conversationToDeleteId) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/conversations/${conversationToDeleteId}/`,
        {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        }
      );

      if (!response.ok) throw new Error("Failed to delete conversation");

      setChatData((prev) => {
        const updatedConversations = prev.conversations.filter(
          (conv) => conv.id !== conversationToDeleteId
        );
        return {
          ...prev,
          conversations: updatedConversations,
          currentConversation: "new",
          messages: [],
        };
      });
      setShowWelcomePage(true);
      closeConfirmModal();
    } catch (err) {
      console.error("Error deleting conversation:", err);
      closeConfirmModal();
    }
  }, [conversationToDeleteId, setChatData, closeConfirmModal]);

  // --- Logout ---
  const handleLogout = async () => {
    try {
      await axios.post('http://127.0.0.1:8000/api/logout/', {}, { withCredentials: true });
      setChatData({
        conversations: [],
        messages: [],
        currentConversation: null,
      });
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      alert('Logout failed. Please try again.');
    }
  };

  return (
    <div className="d-flex flex-column vh-100 bg-white">
      {/* Sidebar */}
      <div
        ref={sidebarRef}
        className="position-fixed h-100 bg-light shadow"
        style={{
          width: "350px",
          left: sidebarOpen ? "0" : "-400px",
          transition: "left 0.3s ease-in-out",
          zIndex: 1000,
        }}
      >
        <Sidebar onDeleteConfirmRequest={openConfirmModal} />
      </div>
      {sidebarOpen && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100"
          style={{ backgroundColor: "rgba(0, 0, 0, 0.5)", zIndex: 999 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between px-4 py-3 border-bottom shadow-sm">
        <FontAwesomeIcon
          role="button"
          tabIndex={0}
          style={{ cursor: "pointer" }}
          icon={faBars}
          size="2xl"
          ref={toggleButtonRef}
          onClick={() => setSidebarOpen(!sidebarOpen)}
        />
        <h1 className="fs-3 text-center flex-grow-1 m-0">
          {currentConv?.title || "Software Design Sensei"}
        </h1>
        <div style={{ width: "24px" }} />
        <button className="btn btn-outline-danger" onClick={handleLogout}>
          <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
          Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="d-flex flex-grow-1 overflow-auto" style={{ height: "100%", overflow: "hidden" }}>
        {showWelcomePage ? (
          <div className={`w-100 ${transitioning ? 'welcome-page-exit' : ''}`}>
            <WelcomePage onStartChat={handleFirstMessageSend} />
          </div>
        ) : (
          <div className={`d-flex flex-grow-1 chat-content ${transitioning ? 'chat-content-enter' : ''}`}>
            {/* Robot */}
            <div className="d-flex justify-content-center align-items-center" style={{ width: "30%", flexShrink: 0 }}>
              <div style={{ width: "100%", height: "auto", maxWidth: "100%", maxHeight: "100%" }}>
                <Lottie animationData={robotAnimation} loop />
              </div>
            </div>

            {/* Messages */}
            <div className="flex-grow-1 overflow-auto d-flex flex-column gap-3 px-5 py-3">
              {currentMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`px-3 py-2 rounded fs-5 message-fade-in ${
                    msg.sender === "bot"
                      ? "bg-white align-self-start"
                      : "bg-blue-light text-black align-self-end"
                  }`}
                  style={{ maxWidth: msg.sender === "bot" ? "100%" : "80%" }}
                >
                  <p className="mb-0">{msg.content}</p>
                </div>
              ))}
              {isTyping && typingMessageContent && (
                <div
                  className="px-3 py-2 rounded fs-5 bg-white align-self-start message-fade-in"
                  style={{ maxWidth: "100%" }}
                >
                  <p className="mb-0">
                    {typingMessageContent}
                    <span className="typing-cursor">|</span>
                  </p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      <DeleteConfirmationModal
        show={showConfirmModal}
        onConfirm={handleDeleteConversationConfirmed}
        onCancel={closeConfirmModal}
      />

      {/* Chat Input */}
      <div style={{ padding: "1.5rem 2rem", backgroundColor: "#ffffff" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            maxWidth: "1200px",
            margin: "0 auto",
          }}
        >
          <div
            style={{
              flex: 1,
              position: "relative",
              backgroundColor: "#f8fafc",
              borderRadius: "1.5rem",
              border: "1px solid rgb(179, 186, 194)",
              transition: "all 0.2s ease",
            }}
          >
            <input
              ref={inputRef}
              type="text"
              placeholder="Have a question on software design? Just ask!"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              style={{
                width: "100%",
                padding: "1.125rem 1.5rem",
                border: "none",
                borderRadius: "1.5rem",
                backgroundColor: "transparent",
                fontSize: "1.125rem",
                outline: "none",
                color: "#334155",
              }}
              onFocus={(e) => {
                e.target.parentElement.style.borderColor = "#000000";
                e.target.parentElement.style.boxShadow = "0 0 0 3px #3b82f6";
              }}
              onBlur={(e) => {
                e.target.parentElement.style.borderColor = "#e2e8f0";
                e.target.parentElement.style.boxShadow = "none";
              }}
            />
          </div>
          <button
            style={{
              width: "3rem",
              height: "3rem",
              borderRadius: "50%",
              border: "none",
              color: "white",
              cursor: inputValue.trim() ? "pointer" : "not-allowed",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              boxShadow: inputValue.trim() ? "0 4px 12px rgba(59, 130, 246, 0.3)" : "none",
            }}
            className={inputValue.trim() ? "bg-blue-dark" : ""}
            onClick={handleSend}
            disabled={!inputValue.trim()}
            onMouseEnter={(e) => {
              if (inputValue.trim()) {
                e.target.style.transform = "scale(1.05)";
              }
            }}
            onMouseLeave={(e) => {
              if (inputValue.trim()) {
                e.target.style.transform = "scale(1)";
              }
            }}
          >
            <FontAwesomeIcon icon={faPaperPlane} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;