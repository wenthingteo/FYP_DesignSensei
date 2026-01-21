import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AppNav from './AppNav'
import { ChatProvider } from './context/ChatContext';

function App() {
  return (
    <BrowserRouter>
      <ChatProvider>
        <AppNav />
      </ChatProvider>
    </BrowserRouter>
  );
}

export default App;
