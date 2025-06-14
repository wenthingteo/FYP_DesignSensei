// src/hooks/useCreateChat.js

const useCreateChat = (setChatData) => {
  return () => {
    // Simply set the state to show welcome page - no API call yet
    setChatData((prev) => ({
      ...prev,
      currentConversation: "new", // Special identifier for new conversation state
      messages: [], // Empty messages to show welcome page
    }));

    console.log("New conversation state set - showing welcome page");
  };
};

export default useCreateChat;