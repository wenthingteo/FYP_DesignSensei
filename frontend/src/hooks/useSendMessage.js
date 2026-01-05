import axios from "axios";
import API_BASE from "../config";

const useSendMessage = (
  chatData, 
  setChatData, 
  setTypingMessageContent, 
  setIsTyping,
  fullAiResponseRef,
  typingIntervalRef,
  currentIndexRef,
  timeoutTimerRef,
  setErrorState,
  setErrorMessage,
  setLastUserMessage,
  abortControllerRef // Add abort controller
) => {
  return async (content) => {
    const userTempMessage = {
      id: `temp-user-${Date.now()}`,
      content,
      conversation: chatData.currentConversation,
      sender: "user",
    };

    setChatData((prev) => ({
      ...prev,
      messages: [...prev.messages, userTempMessage],
    }));

    // Store last user message for regeneration
    if (setLastUserMessage) {
      setLastUserMessage(content);
    }

    // Add a placeholder for the AI's typing message
    setIsTyping(true);
    setTypingMessageContent(""); // Clear previous typing content

    // --- Reset error state ---
    setErrorState(null);
    setErrorMessage("");
    
    const clearAllTimers = () => {
      if (timeoutTimerRef.current) {
        clearTimeout(timeoutTimerRef.current);
        timeoutTimerRef.current = null;
      }
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
    };

    // Clear any existing abort controller
    if (abortControllerRef && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (abortControllerRef) {
      abortControllerRef.current = new AbortController();
    }

    // Frontend timeout: 60 seconds (backend timeout is 50s + extra buffer for longer responses)
    timeoutTimerRef.current = setTimeout(() => {
      setErrorState('timeout');
      setErrorMessage("Response generation is taking longer than expected. This might be due to high server load or complex processing.");
      setIsTyping(false);
      setTypingMessageContent("");
      fullAiResponseRef.current = "";
      currentIndexRef.current = 0;
      if (abortControllerRef && abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearAllTimers();
    }, 60000); // 60 seconds timeout

    try {
      const res = await axios.post(`${API_BASE}/api/chat/`, {
        content: content,
        conversation: chatData.currentConversation,
      }, {
        withCredentials: true,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        },
        signal: abortControllerRef ? abortControllerRef.current.signal : undefined,
      });

      // Clear timeout since we got a response
      clearTimeout(timeoutTimerRef.current);
      timeoutTimerRef.current = null;

      // Check if backend returned timeout error (408)
      if (res.status === 408 || res.data.error === 'timeout') {
        setErrorState('timeout');
        setErrorMessage(res.data.message || "The server took too long to process your request.");
        setIsTyping(false);
        setTypingMessageContent("");
        fullAiResponseRef.current = "";
        currentIndexRef.current = 0;
        clearAllTimers();
        
        // Replace temp with real user_message from backend
        if (res.data.user_message) {
          setChatData((prev) => ({
            ...prev,
            messages: prev.messages.map(msg => 
              msg.id === userTempMessage.id ? res.data.user_message : msg
            ),
          }));
        }
        
        return;
      }

      const { user_message, ai_response } = res.data;

      // Simulate typing effect for AI response
      const fullAiResponseContent = ai_response.content;
      
      // Store full response in ref for tab switching recovery
      fullAiResponseRef.current = fullAiResponseContent;
      currentIndexRef.current = 0;

      // Clear any existing interval
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
      }

      typingIntervalRef.current = setInterval(() => {
        if (currentIndexRef.current < fullAiResponseContent.length) {
          setTypingMessageContent(fullAiResponseContent.substring(0, currentIndexRef.current + 150));
          currentIndexRef.current += 150;
        } else {
          clearAllTimers();
          setIsTyping(false);
          setTypingMessageContent("");

          // Replace temp message with real messages from backend
          setChatData((prev) => {
            const filteredMessages = prev.messages.filter((msg) =>
              msg && msg.id !== userTempMessage.id
            );

            const messagesToAdd = [];
            if (user_message && typeof user_message === 'object') {
              messagesToAdd.push(user_message);
            }
            if (ai_response && typeof ai_response === 'object') {
              messagesToAdd.push({ ...ai_response, content: fullAiResponseContent });
            }

            return {
              ...prev,
              messages: filteredMessages.concat(messagesToAdd),
            };
          });

          fullAiResponseRef.current = "";
          currentIndexRef.current = 0;
          
          if (setLastUserMessage) {
            setLastUserMessage(null);
          }
        }
      }, 10); // Adjust typing speed to match ChatbotPage (0.5ms)

    } catch (err) {
      console.error("Failed to send message or get bot response", err);
      
      // Clear timeout timer
      clearAllTimers();
      
      // Check if request was aborted (network disconnection)
      if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
        setErrorState('network');
        setErrorMessage("Request cancelled. Please check your internet connection.");
        setIsTyping(false);
        setTypingMessageContent("");
        fullAiResponseRef.current = "";
        currentIndexRef.current = 0;
        // Keep temp message displayed
        return;
      }
      
      // Determine error type and set appropriate message
      if (err.response) {
        // Server responded with an error
        if (err.response.status === 408) {
          setErrorState('timeout');
          setErrorMessage(err.response.data?.message || "The server took too long to process your request. Please try regenerating your question.");
        } else if (err.response.status >= 500) {
          setErrorState('server');
          setErrorMessage("The server encountered an error. Please try again in a moment.");
        } else {
          setErrorState('server');
          setErrorMessage(err.response.data?.message || "An error occurred while processing your request.");
        }
      } else if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        // Network timeout
        setErrorState('network');
        setErrorMessage("Request timed out. Please check your internet connection and try again.");
      } else if (err.message.includes('Network Error') || !window.navigator.onLine) {
        // Network error or offline
        setErrorState('network');
        setErrorMessage("Unable to connect to the server. Please check your internet connection.");
      } else {
        // Other errors
        setErrorState('server');
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
      
      setIsTyping(false);
      setTypingMessageContent("");
      
      fullAiResponseRef.current = "";
      currentIndexRef.current = 0;
      
      // Keep temp message displayed so user can regenerate
    }
  };
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

export default useSendMessage;