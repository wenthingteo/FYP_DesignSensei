import React, { useContext, useState, useRef, useEffect } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";
import Sidebar from "../components/Sidebar";
import WelcomePage from "../components/WelcomePage";
import { ChatContext } from "../context/ChatContext";
import useSendMessage from "../hooks/useSendMessage";

const ChatbotPage = () => {
  const [inputValue, setInputValue] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarRef = useRef(null);
  const toggleButtonRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { chatData, setChatData } = useContext(ChatContext);
  const { messages, currentConversation, conversations } = chatData;
  const sendMessage = useSendMessage(chatData, setChatData);

  // Find the current conversation object by ID for header title
  const currentConv = conversations.find(c => c.id === currentConversation);

  // Filter messages for the current conversation
  const currentMessages = messages.filter(m => {
    // Defensive check: ensure 'm' is a valid object before accessing properties
    if (!m) {
      console.warn("Found an undefined or null message in the messages array. Skipping.");
      return false; // Exclude invalid messages
    }
    return m.conversation === currentConversation;
  });

  // Check if we should show welcome page (new conversation state or no messages)
  const showWelcomePage = currentConversation === "new" || (!currentConversation || currentMessages.length === 0);

  // Effect to scroll to the latest message
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);
  
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
  }, [currentConversation]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    // If we're in "new" conversation state, create conversation with first message
    if (currentConversation === "new") {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/chat/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "include",
          body: JSON.stringify({
            content: inputValue.trim(),
            conversation: null, // null means create new conversation
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to create conversation");
        }

        const data = await response.json();
        const { conversation_id, user_message, ai_response } = data;

        // Create conversation object
        const newConversation = {
          id: conversation_id,
          title: inputValue.trim().substring(0, 50) || "New Conversation",
          created_at: new Date().toISOString(),
        };

        // Update chat data with new conversation and messages
        setChatData((prev) => ({
          ...prev,
          conversations: [newConversation, ...prev.conversations],
          currentConversation: conversation_id,
          messages: [user_message, ai_response],
        }));

        setInputValue("");
        console.log("New conversation created with first message:", conversation_id);
        return;
      } catch (error) {
        console.error("Error creating conversation:", error);
        alert("Failed to create conversation. Please try again.");
        return;
      }
    }

    // Normal message sending for existing conversations
    if (!currentConversation) {
      console.warn("Please select or create a conversation first.");
      alert("Please select or create a conversation first.");
      return;
    }

    await sendMessage(inputValue.trim());
    setInputValue(""); // Clear input after sending
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

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
        <Sidebar />
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
          /* Welcome Page */
          <div className="w-100">
            <WelcomePage userName="WT" />
          </div>
        ) : (
          <>
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
                  className={`px-3 py-2 rounded fs-5 ${
                    msg.sender === "AI Chatbot"
                      ? "bg-white align-self-start"
                      : "bg-blue-light text-black align-self-end"
                  }`}
                  style={{ maxWidth: msg.sender === "AI Chatbot" ? "100%" : "80%" }}
                >
                  <p className="mb-0">{msg.content}</p>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </>
        )}
      </div>

      {/* Chat Input */}
      <div className="p-3 d-flex align-items-center">
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