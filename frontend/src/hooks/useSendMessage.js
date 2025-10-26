import axios from "axios";

const useSendMessage = (
  chatData, 
  setChatData, 
  setTypingMessageContent, 
  setIsTyping,
  fullAiResponseRef,
  typingIntervalRef,
  currentIndexRef
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

    // Add a placeholder for the AI's typing message
    setIsTyping(true);
    setTypingMessageContent(""); // Clear previous typing content

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/chat/", {
        content: content,
        conversation: chatData.currentConversation,
      }, {
        withCredentials: true,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        },
      });

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
          setTypingMessageContent(fullAiResponseContent.substring(0, currentIndexRef.current + 20));
          currentIndexRef.current += 20;
        } else {
          clearInterval(typingIntervalRef.current);
          typingIntervalRef.current = null;
          setIsTyping(false);
          setTypingMessageContent(""); // Clear typing content after full message is displayed

          // Now, add the complete AI message to the chat data
          setChatData((prev) => {
            const filteredMessages = prev.messages.filter((msg) =>
              msg && msg.id !== userTempMessage.id // Remove temp user message
            );

            const messagesToAdd = [];
            if (user_message && typeof user_message === 'object') {
              messagesToAdd.push(user_message);
            }
            if (ai_response && typeof ai_response === 'object') {
              messagesToAdd.push({ ...ai_response, content: fullAiResponseContent }); // Ensure full content is saved
            }

            return {
              ...prev,
              messages: filteredMessages.concat(messagesToAdd),
            };
          });

          // Clear refs after completion
          fullAiResponseRef.current = "";
          currentIndexRef.current = 0;
        }
      }, 0.5); // Adjust typing speed to match ChatbotPage (0.5ms)

    } catch (err) {
      console.error("Failed to send message or get bot response", err);
      setIsTyping(false); // Stop typing on error
      setTypingMessageContent(""); // Clear typing content on error
      
      // Clear refs on error
      fullAiResponseRef.current = "";
      currentIndexRef.current = 0;
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
      
      setChatData((prev) => ({
        ...prev,
        messages: prev.messages.filter((msg) =>
          msg && msg.id !== userTempMessage.id
        ),
      }));
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