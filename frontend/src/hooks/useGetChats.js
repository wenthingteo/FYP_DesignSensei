import { useContext } from "react";
import { ChatContext } from "../context/ChatContext";

const useGetChats = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useGetChats must be used inside ChatProvider");
  return context;
};

export default useGetChats;


// import { useEffect, useState } from "react";
// import axios from "axios";

// function useGetChats() {
//     const [chatData, setChatData] = useState({
//         conversations: [],
//         current_conversation: null,
//         messages: []
//     });
//     const [error, setError] = useState(null);
//     const [loading, setLoading] = useState(true);

//     useEffect(() => {
//         const fetchChats = async () => {
//         try {

//             const response = await axios.get("http://127.0.0.1:8000/api/chat/", {
//                 withCredentials: true,
//                 headers: {
//                     'X-CSRFToken': getCookie('csrftoken'),  
//                     'Content-Type': 'application/json'
//                 },  
//             });

//             setChatData(response.data);
//             console.log(response.data)
//         } catch (err) {
//             setError(err);
//             console.log(err);
//         } finally {
//             setLoading(false);
//         }
//         };

//         fetchChats();
//     }, []);

//     return { chatData, error, loading };
// }

// function getCookie(name) {
//   let cookieValue = null;
//   if (document.cookie && document.cookie !== '') {
//     const cookies = document.cookie.split(';');
//     for (let i = 0; i < cookies.length; i++) {
//       const cookie = cookies[i].trim();
//       // Does this cookie string begin with the name we want?
//       if (cookie.substring(0, name.length + 1) === (name + '=')) {
//         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//         break;
//       }
//     }
//   }
//   console.log(cookieValue);
//   return cookieValue;
// }

// export default useGetChats;
