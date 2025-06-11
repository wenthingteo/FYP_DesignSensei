// src/hooks/useSendMessage.js
import axios from "axios";

const useSendMessage = (chatData, setChatData) => {
  return async (content) => {
    const newMessage = {
      id: `temp-${Date.now()}`,
      content,
      conversation: chatData.currentConversation,
      sender: "user",
    };

    setChatData((prev) => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    try {
      const res = await axios.post("/api/messages/", {
        content,
        conversation: chatData.currentConversation,
        sender: "user",
      });

      setChatData((prev) => ({
        ...prev,
        messages: prev.messages
          .filter((m) => m.id !== newMessage.id)
          .concat(res.data),
      }));
    } catch (err) {
      console.error("Failed to send message", err);
    }
  };
};

export default useSendMessage;
