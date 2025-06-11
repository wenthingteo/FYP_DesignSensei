import { createContext, useState, useEffect } from "react";
import axios from "axios";

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [chatData, setChatData] = useState({
    conversations: [],
    current_conversation: null,
    messages: []
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch conversations on mount
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/chat/", {
          withCredentials: true,
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
          }
        });

        setChatData((prev) => ({
          ...prev,
          conversations: response.data.conversations || response.data  // depending on your backend format
        }));
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchChats();
  }, []);

  return (
    <ChatContext.Provider value={{ chatData, setChatData, loading, error }}>
      {children}
    </ChatContext.Provider>
  );
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


//   const [chatData, setChatData] = useState({
//     conversations: [
//       { id: 1, title: "Frontend Help", created_at: "2025-06-10T10:00:00Z" },
//       { id: 2, title: "Backend Debugging", created_at: "2025-06-10T11:00:00Z" }
//     ],
//     currentConversation: 1,
//     messages: [
//       // Messages for conversation 1
//         { 
//             id: 1, 
//             conversation: 1, 
//             sender: "user", 
//             content: "What is the difference between high cohesion and low coupling?", 
//             created_at: "2025-06-10T10:01:00Z" 
//         },
//         { 
//             id: 2, 
//             conversation: 1, 
//             sender: "bot", 
//             content: "High cohesion and low coupling are two core principles in software design that significantly impact code maintainability and flexibility. High cohesion means that the responsibilities of a module (like a class or function) are strongly related and focused on a specific task. For example, a class that only manages user authentication—handling login, logout, and token generation—exhibits high cohesion. This makes the code easier to understand, reuse, and modify because everything inside the class is closely related. Low coupling means that a module has minimal dependencies on other modules. This is important because when modules are loosely coupled, changes in one module are less likely to affect others. For example, if your authentication module communicates with the database through an interface or repository layer, you can swap out the database implementation without rewriting the logic. In essence, high cohesion makes modules strong individually, and low coupling makes them collaborate well together. Striking the right balance between both leads to scalable, maintainable, and testable systems.", 
//             created_at: "2025-06-10T10:01:30Z" 
//         },
//         { 
//             id: 3, 
//             conversation: 1, 
//             sender: "user", 
//             content: "Which one is better?", 
//             created_at: "2025-06-10T10:02:00Z" 
//         },
//         { 
//             id: 4, 
//             conversation: 1, 
//             sender: "bot", 
//             // content: "Tailwind is more utility-based; styled-components offer scoped styles.", 
//             content: "Certainly! The SOLID principles are a set of five design guidelines intended to make object-oriented software easier to manage, extend, and maintain: \n "+
//                 "S : Single Responsibility Principle (SRP)"+
//                 "A class should have only one reason to change. That means it should have one job or responsibility. For instance, separating business logic from UI logic ensures that each part of your application evolves independently."+

//                 "O – Open/Closed Principle (OCP)"+
//                 "Software entities (classes, modules, functions) should be open for extension but closed for modification. This means you can add new features via inheritance or composition without changing existing code. It's especially useful when dealing with plugin-based architectures."+

//                 "L – Liskov Substitution Principle (LSP)"+
//                 "Objects of a superclass should be replaceable with objects of a subclass without affecting the correctness of the program. Violating this principle often results in unexpected behavior when using polymorphism."+

//                 "I – Interface Segregation Principle (ISP)"+
//                 "Clients should not be forced to depend on interfaces they do not use. Instead of having one large interface, split it into smaller, more specific ones."+

//                 "D – Dependency Inversion Principle (DIP)"+
//                 "High-level modules should not depend on low-level modules. Both should depend on abstractions. This promotes the use of interfaces or abstract classes to decouple code layers."+

//                 "Following SOLID leads to systems that are easier to refactor, test, and scale.", 
//             created_at: "2025-06-10T10:02:30Z" 
//         },
//         { 
//             id: 5, 
//             conversation: 1, 
//             sender: "user", 
//             content: "Thanks!", 
//             created_at: "2025-06-10T10:03:00Z" 
//         },

//         // Messages for conversation 2
//         { 
//             id: 6, 
//             conversation: 2, 
//             sender: "user", 
//             content: "Can you explain the SOLID principles in software design?", 
//             created_at: "2025-06-10T11:01:00Z" 
//         },
//         { 
//             id: 7, 
//             conversation: 2, 
//             sender: "bot", 
//             content: "Certainly! The SOLID principles are a set of five design guidelines intended to make object-oriented software easier to manage, extend, and maintain: \n "+
//                 "S : Single Responsibility Principle (SRP)"+
//                 "A class should have only one reason to change. That means it should have one job or responsibility. For instance, separating business logic from UI logic ensures that each part of your application evolves independently."+

//                 "O – Open/Closed Principle (OCP)"+
//                 "Software entities (classes, modules, functions) should be open for extension but closed for modification. This means you can add new features via inheritance or composition without changing existing code. It's especially useful when dealing with plugin-based architectures."+

//                 "L – Liskov Substitution Principle (LSP)"+
//                 "Objects of a superclass should be replaceable with objects of a subclass without affecting the correctness of the program. Violating this principle often results in unexpected behavior when using polymorphism."+

//                 "I – Interface Segregation Principle (ISP)"+
//                 "Clients should not be forced to depend on interfaces they do not use. Instead of having one large interface, split it into smaller, more specific ones."+

//                 "D – Dependency Inversion Principle (DIP)"+
//                 "High-level modules should not depend on low-level modules. Both should depend on abstractions. This promotes the use of interfaces or abstract classes to decouple code layers."+

//                 "Following SOLID leads to systems that are easier to refactor, test, and scale.", 
//             created_at: "2025-06-10T11:01:30Z" 
//         },
//         { 
//             id: 8, 
//             conversation: 2, 
//             sender: "user", 
//             content: "Oh, I forgot `withCredentials: true` in axios.", 
//             created_at: "2025-06-10T11:02:00Z" 
//         },
//         { 
//             id: 9, 
//             conversation: 2, 
//             sender: "bot", 
//             content: "Yep, that would cause the issue!", 
//             created_at: "2025-06-10T11:02:30Z" 
//         },
//         { 
//             id: 10, 
//             conversation: 2, 
//             sender: "user", 
//             content: "Fixed it now. Thanks!", 
//             created_at: "2025-06-10T11:03:00Z" 
//         }
//         ]
//     });