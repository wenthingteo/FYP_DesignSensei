import React from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/RegisterPage';
import ChatbotPage from './pages/ChatbotPage';
import FeedbackPage from './pages/FeedbackPage';

function AppNav() {
    return (
        <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/signup" element={<SignUpPage />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
        </Routes>
    );
}

export default AppNav;