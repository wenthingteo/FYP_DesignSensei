import React from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ChatbotPage from './pages/ChatbotPage';
import FeedbackPage from './pages/FeedbackPage';
import RegisterPage from './pages/RegisterPage';
import AdminDashboard from './pages/AdminDashboard';

function AppNav() {
    return (
        <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/admin/feedback" element={<AdminDashboard />} />
        </Routes>
    );
}

export default AppNav;