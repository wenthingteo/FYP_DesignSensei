// src/hooks/useCreateChat.js

const useCreateChat = (setChatData) => {
  return () => {
    // Clear messages and set to new conversation state
    // This ensures the first message sent will be added to the new conversation
    setChatData((prev) => ({
      ...prev,
      currentConversation: "new", // Special identifier for new conversation state
      messages: [], // Clear all messages to start fresh
    }));

    console.log("New conversation state set - ready for first message");
  };
};

export default useCreateChat;