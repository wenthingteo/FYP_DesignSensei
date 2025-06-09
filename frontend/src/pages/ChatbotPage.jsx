import React from "react";
import Sidebar from "../components/Sidebar";

const ChatbotPage = () => {
  return (
    <>
      <Sidebar/>
    </>
  )
}

export default ChatbotPage

// import React, { useEffect, useState, useRef } from 'react';
// import axios from 'axios';
// import API_BASE from '../config'; // adjust this to your config file

// const ChatbotPage = () => {
//   const [conversations, setConversations] = useState([]);
//   const [currentConversationId, setCurrentConversationId] = useState(null);
//   const [messages, setMessages] = useState([]);
//   const [message, setMessage] = useState('');
//   const messagesEndRef = useRef(null);

//   useEffect(() => {
//     axios.get(`${API_BASE}/api/conversations/`, { withCredentials: true })
//       .then(res => setConversations(res.data));
//   }, []);

//   useEffect(() => {
//     if (currentConversationId) {
//       axios.get(`${API_BASE}/api/conversations/${currentConversationId}/messages/`, { withCredentials: true })
//         .then(res => setMessages(res.data));
//     }
//   }, [currentConversationId]);

//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [messages]);

//   const handleNewConversation = () => {
//     axios.post(`${API_BASE}/api/conversations/`, {}, { withCredentials: true })
//       .then(res => {
//         setCurrentConversationId(res.data.id);
//         setConversations(prev => [res.data, ...prev]);
//       });
//   };

//   const handleSend = (e) => {
//     e.preventDefault();
//     if (!message.trim()) return;

//     setMessages(prev => [...prev, { content: message, sender: 'You' }]);

//     axios.post(`${API_BASE}/api/conversations/${currentConversationId}/messages/`, {
//       message
//     }, { withCredentials: true })
//       .then(res => {
//         setMessages(prev => [...prev, { content: res.data.response, sender: 'AI Chatbot' }]);
//       });

//     setMessage('');
//   };

//   return (
//     <div className="flex h-screen overflow-hidden">
//       {/* Sidebar */}
//       <div className="w-64 bg-gray-100 border-r p-4 overflow-y-auto">
//         <h2 className="text-xl font-semibold mb-4">Conversations</h2>
//         <button
//           className="w-full bg-green-500 text-white py-2 rounded mb-4 hover:bg-green-600"
//           onClick={handleNewConversation}
//         >
//           + New Conversation
//         </button>

//         <div className="space-y-2">
//           {conversations.map((convo) => (
//             <button
//               key={convo.id}
//               onClick={() => setCurrentConversationId(convo.id)}
//               className={`w-full text-left px-3 py-2 rounded ${convo.id === currentConversationId ? 'bg-blue-200' : 'bg-gray-200'} hover:bg-gray-300`}
//             >
//               {convo.title || 'New Conversation'}
//             </button>
//           ))}
//         </div>

//         <a href="/feedback" className="block mt-6 text-blue-500 hover:underline">
//           Send Feedback
//         </a>
//       </div>

//       {/* Chat Area */}
//       <div className="flex flex-col flex-1">
//         <div className="bg-blue-600 text-white p-4 text-lg font-semibold">
//           Chat - {conversations.find(c => c.id === currentConversationId)?.title || 'New Conversation'}
//         </div>

//         <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4">
//           {messages.map((msg, index) => (
//             <div
//               key={index}
//               className={`flex ${msg.sender === 'You' ? 'justify-end' : 'justify-start'}`}
//             >
//               <div
//                 className={`rounded px-4 py-2 max-w-xs break-words ${
//                   msg.sender === 'You' ? 'bg-green-200' : 'bg-gray-200'
//                 }`}
//               >
//                 <div className="text-sm font-bold">{msg.sender}</div>
//                 <div>{msg.content}</div>
//               </div>
//             </div>
//           ))}
//           <div ref={messagesEndRef} />
//         </div>

//         {/* Message Input */}
//         <form onSubmit={handleSend} className="p-4 bg-white border-t flex items-center gap-2">
//           <input
//             type="text"
//             className="flex-1 border rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
//             placeholder="Type your message..."
//             value={message}
//             onChange={(e) => setMessage(e.target.value)}
//           />
//           <button
//             type="submit"
//             className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
//           >
//             Send
//           </button>
//         </form>
//       </div>
//     </div>
//   );
// };

// export default ChatbotPage;
