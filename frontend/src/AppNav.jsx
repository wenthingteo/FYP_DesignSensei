import React from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ChatbotPage from './pages/ChatbotPage';
import FeedbackPage from './pages/FeedbackPage';
import RegisterPage from './pages/RegisterPage';

function AppNav() {
    return (
        <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
        </Routes>
    );
}

export default AppNav;