import React, { useContext, useState, useRef, useEffect } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";
import Sidebar from "../components/Sidebar";
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
  // Destructure properties from chatData, ensuring currentConversation is an ID
  const { messages, currentConversation, conversations } = chatData;
  const sendMessage = useSendMessage(chatData, setChatData);

  // Find the current conversation object by ID for header title
  const currentConv = conversations.find(c => c.id === currentConversation);

  // Filter messages for the current conversation
  const currentMessages = messages.filter(m => {
    // Added extensive logging for debugging filter
    console.log(`Filtering message ID: ${m.id}, conversation: ${m.conversation}, sender: ${m.sender}`);
    console.log(`  Current active conversation ID: ${currentConversation}`);
    console.log(`  Match? ${m.conversation === currentConversation} (Type of m.conversation: ${typeof m.conversation}, Type of currentConversation: ${typeof currentConversation})`);
    return m.conversation === currentConversation;
  });


  // Scroll to bottom when new messages come in (dependency should be on messages changing)
  useEffect(() => {
    console.log("ChatbotPage: currentMessages updated, attempting scroll.");
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages]); // Keep currentMessages as dependency for specific re-render context

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
    if (!currentConversation) {
      // Use a custom modal or toast instead of alert()
      console.warn("Please select or create a conversation first.");
      // Example of a simple alert replacement (for dev, use a proper UI component in prod)
      alert("Please select or create a conversation first."); // Temporarily keep for user visibility, but replace!
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

  // --- Crucial logs for debugging rendering ---
  console.log("ChatbotPage Render - chatData:", chatData);
  console.log("ChatbotPage Render - currentConversation ID:", currentConversation);
  console.log("ChatbotPage Render - All messages in state:", messages);
  console.log("ChatbotPage Render - Filtered currentMessages for display:", currentMessages);
  console.log("ChatbotPage Render - Number of currentMessages:", currentMessages.length);
  // --- END Crucial logs ---


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