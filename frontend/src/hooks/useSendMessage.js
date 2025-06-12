// src/hooks/useSendMessage.js
import axios from "axios";

const useSendMessage = (chatData, setChatData) => {
  return async (content) => {
    const newMessage = {
      id: `temp-${Date.now()}`, // Unique ID for optimistic update
      content,
      conversation: chatData.currentConversation,
      sender: "user", // Optimistic sender is always "user"
      created_at: new Date().toISOString(), // Add created_at for consistency
    };

    console.log("useSendMessage: Optimistically adding user message:", newMessage);

    setChatData((prev) => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    try {
      // **CRITICAL CHANGE: Align payload keys with ChatbotAPIView's POST method**
      const payload = {
        user_query: content, // ChatbotAPIView expects 'user_query'
        conversation_id: chatData.currentConversation, // ChatbotAPIView expects 'conversation_id'
        // You might also need to send user_expertise and response_length if your ChatbotAPIView's POST method uses them from the request data
        // For now, let's assume default values in the backend if not provided.
      };

      console.log("useSendMessage: Sending POST request to:", `/api/chat/`);
      console.log("useSendMessage: Payload:", payload);

      // Use the correct endpoint for the chatbot logic
      const res = await axios.post("/api/chat/", payload);

      console.log("useSendMessage: Backend response status:", res.status);
      console.log("useSendMessage: Backend response data:", res.data); // *** THIS IS THE CRUCIAL LOG ***

      // Backend (ChatbotAPIView) is expected to return both the user's message and the bot's message.
      // The structure was often like { 'user_message': {..}, 'bot_message': {..} }
      // Or it could be an array like [{user_msg}, {bot_msg}]
      const { user_message, bot_message } = res.data; // Destructure if backend returns objects

      let newMessagesFromBackend = [];
      if (user_message && bot_message) {
          // If backend returns as two separate objects
          newMessagesFromBackend = [user_message, bot_message];
      } else if (Array.isArray(res.data) && res.data.length === 2) {
          // If backend returns as an array of two messages
          newMessagesFromBackend = res.data;
      } else {
          console.warn("useSendMessage: Unexpected backend response structure:", res.data);
          // Fallback if structure is unexpected, try to use whatever is there if it looks like messages
          newMessagesFromBackend = Array.isArray(res.data) ? res.data : [res.data];
      }


      setChatData((prev) => {
        // Filter out the optimistic message using its temporary ID
        const messagesWithoutOptimistic = prev.messages.filter(
          (m) => m.id !== newMessage.id
        );

        // Map over the messages from the backend to ensure correct sender values
        // and add a unique key if needed (though IDs from DB should be unique)
        const processedBackendMessages = newMessagesFromBackend.map(msg => ({
            ...msg,
            // Ensure sender is "user" or "AI Chatbot"
            sender: msg.sender === 'user' ? 'user' : 'AI Chatbot',
            // Ensure conversation ID is a number
            conversation: Number(msg.conversation)
        }));

        return {
          ...prev,
          messages: [...messagesWithoutOptimistic, ...processedBackendMessages],
        };
      });
    } catch (err) {
      console.error("useSendMessage: Failed to send message", err);
      // If the API call fails, remove the optimistic message to reflect the failure
      setChatData((prev) => ({
        ...prev,
        messages: prev.messages.filter((m) => m.id !== newMessage.id),
      }));
    }
  };
};

export default useSendMessage;