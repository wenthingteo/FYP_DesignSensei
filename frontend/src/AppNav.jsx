import React from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import Chatbot from './pages/ChatbotPage';
import Feedback from './pages/FeedbackPage';
import Login from '..pages/LoginPage';
import SignUp from './pages/RegisterPage';

function AppNav() {
    return (
        <>
            <Router>
                <Routes>
                    <Route
                        path='/'
                        element={<Login />}
                    />
                    <Route
                        path='/signup'
                        element={<SignUp />}
                    />
                    <Route
                        path='/chat'
                        element={<Chatbot />}
                    />
                    <Route
                        path='/feedback'
                        element={<Feedback />}
                    />
                </Routes>
            </Router>
        </>
    );
}