import axios from "axios";

const useSendMessage = (chatData, setChatData) => {
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

      setChatData((prev) => {
        const filteredMessages = prev.messages.filter((msg) =>
          msg && msg.id !== userTempMessage.id
        );

        const messagesToAdd = [];
        if (user_message && typeof user_message === 'object') {
          messagesToAdd.push(user_message);
        }
        if (ai_response && typeof ai_response === 'object') {
          messagesToAdd.push(ai_response);
        }

        return {
          ...prev,
          messages: filteredMessages.concat(messagesToAdd),
        };
      });

    } catch (err) {
      console.error("Failed to send message or get bot response", err);
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