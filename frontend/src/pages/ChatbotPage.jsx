import React, { useContext, useState, useRef, useEffect, useCallback } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";
import Sidebar from "../components/Sidebar";
import WelcomePage from "../components/WelcomePage";
import { ChatContext } from "../context/ChatContext";
import useSendMessage from "../hooks/useSendMessage";
import './ChatbotPage.css'; // Import the new CSS file
import DeleteConfirmationModal from "../components/DeleteConfirmationModal"; // Import the new modal component

const ChatbotPage = () => {
  const [inputValue, setInputValue] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarRef = useRef(null);
  const toggleButtonRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { chatData, setChatData } = useContext(ChatContext);
  const { messages, currentConversation, conversations } = chatData;

  // New states for typing effect
  const [typingMessageContent, setTypingMessageContent] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  // New states for welcome page transition
  const [showWelcomePage, setShowWelcomePage] = useState(
    currentConversation === "new" || (!currentConversation && messages.length === 0)
  );
  const [transitioning, setTransitioning] = useState(false);

  // New states for confirmation modal
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [conversationToDeleteId, setConversationToDeleteId] = useState(null);

  // Pass setTypingMessageContent and setIsTyping to useSendMessage
  const sendMessage = useSendMessage(chatData, setChatData, setTypingMessageContent, setIsTyping);

  // Find the current conversation object by ID for header title
  const currentConv = conversations.find(c => c.id === currentConversation);

  // Filter messages for the current conversation (excluding the one being typed placeholder)
  const currentMessages = messages.filter(m =>
    m && m.conversation === currentConversation && m.id !== 'typing-ai-message'
  );

  // Effect to scroll to the latest message or typing message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages, typingMessageContent]);

  // Close sidebar on outside click
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

  // Auto focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, [currentConversation, showWelcomePage]);

  // Helper function to get CSRF token
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

  const handleSend = async (messageContentToSend = inputValue.trim()) => {
    if (!messageContentToSend) return;

    // If we're in "new" conversation state, create conversation with first message
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

        if (!response.ok) {
          throw new Error("Failed to create conversation");
        }

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
        
        const fullAiResponseContent = ai_response.content;
        let i = 0;
        const typingInterval = setInterval(() => {
          if (i < fullAiResponseContent.length) {
            setTypingMessageContent(fullAiResponseContent.substring(0, i + 1));
            i++;
          } else {
            clearInterval(typingInterval);
            setIsTyping(false);
            setTypingMessageContent("");

            setChatData((prev) => ({
              ...prev,
              messages: prev.messages.concat([{ ...ai_response, content: fullAiResponseContent }]),
            }));
          }
        }, 20);

        setInputValue("");
        return;
      } catch (error) {
        console.error("Error creating conversation:", error);
        setIsTyping(false);
        setTypingMessageContent("");
        return;
      }
    }

    await sendMessage(messageContentToSend);
    setInputValue("");
  };

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

  // Effect to manage showWelcomePage state based on currentConversation and messages
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


  // --- Confirmation Modal Functions ---
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
      
      if (!response.ok) {
        throw new Error("Failed to delete conversation");
      }

      setChatData((prev) => {
        const updatedConversations = prev.conversations.filter(
          (conv) => conv.id !== conversationToDeleteId
        );
        // After deleting, ensure currentConversation is set to "new"
        return {
          ...prev,
          conversations: updatedConversations,
          currentConversation: "new", // Go back to welcome page
          messages: [], // Clear messages
        };
      });
      // Immediately show welcome page, even before the useEffect catches up
      setShowWelcomePage(true); 
      closeConfirmModal(); // Close modal after successful deletion
      console.log("Conversation deleted successfully and returned to welcome page.");
    } catch (err) {
      console.error("Error deleting conversation:", err);
      // In a real app, show an error message to the user here (e.g., a toast notification)
      closeConfirmModal(); // Close modal even on error
    }
  }, [conversationToDeleteId, setChatData, closeConfirmModal]);


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
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              setSidebarOpen(false);
            }
          }}
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
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              setSidebarOpen(!sidebarOpen);
            }
          }}
        />
        <h1 className="fs-3 text-center flex-grow-1 m-0">
          {currentConv?.title || "Design Sensei"}
        </h1>
        <div style={{ width: "24px" }} />
      </div>

      {/* Main Content */}
      <div className="d-flex flex-grow-1" style={{ height: "100%", overflow: "hidden" }}>
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
                    msg.sender === "AI Chatbot"
                      ? "bg-white align-self-start"
                      : "bg-blue-light text-black align-self-end"
                  }`}
                  style={{ maxWidth: msg.sender === "AI Chatbot" ? "100%" : "80%" }}
                >
                  <p className="mb-0">{msg.content}</p>
                </div>
              ))}
              {isTyping && typingMessageContent && (
                <div
                  className="px-3 py-2 rounded fs-5 bg-white align-self-start message-fade-in"
                  style={{ maxWidth: "100%" }}
                >
                  <p className="mb-0">{typingMessageContent}<span className="typing-cursor">|</span></p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal - Rendered outside the main content flow */}
      <DeleteConfirmationModal
        show={showConfirmModal}
        onConfirm={handleDeleteConversationConfirmed}
        onCancel={closeConfirmModal}
      />

      {/* Chat Input */}
      <div className="p-5 d-flex align-items-center">
        <input
          ref={inputRef}
          type="text"
          className="form-control me-2"
          placeholder="Have a question on software design? Just ask!"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyPress}
        />
        <button
          className="btn bg-blue-dark text-white"
          onClick={handleSend}
          disabled={!inputValue.trim()}
        >
          <FontAwesomeIcon icon={faPaperPlane} />
        </button>
      </div>
    </div>
  );
};

export default ChatbotPage;