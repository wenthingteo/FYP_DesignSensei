// src/hooks/useCreateConversation.js
import { useCallback } from 'react';

const useCreateChat = (setChatData) => {
  return useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' }),
      });

      if (!response.ok) throw new Error('Failed to create conversation');

      const newConv = await response.json();

      setChatData((prev) => ({
        ...prev,
        conversations: [newConv, ...prev.conversations],
        currentConversation: newConv.id,
      }));
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  }, [setChatData]);
};

export default useCreateChat;
