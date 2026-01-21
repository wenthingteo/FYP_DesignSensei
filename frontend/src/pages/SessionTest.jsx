import React, { useState } from 'react';
import API_BASE from '../config';

const SessionTest = () => {
    const [sessionInfo, setSessionInfo] = useState(null);
    const [authInfo, setAuthInfo] = useState(null);

    const testSession = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/auth/debug/`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            setSessionInfo(data);
        } catch (error) {
            console.error('Session test failed:', error);
            setSessionInfo({ error: error.message });
        }
    };

    const testAuth = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/auth/ping/`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            setAuthInfo(data);
        } catch (error) {
            console.error('Auth test failed:', error);
            setAuthInfo({ error: error.message });
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Session Debug Tool</h2>
            
            <div className="space-y-4">
                <div>
                    <button 
                        onClick={testSession}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mr-2"
                    >
                        Test Session
                    </button>
                    <button 
                        onClick={testAuth}
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    >
                        Test Auth
                    </button>
                </div>

                {sessionInfo && (
                    <div className="border p-4 rounded bg-gray-50">
                        <h3 className="font-bold mb-2">Session Info:</h3>
                        <pre className="text-sm overflow-auto">
                            {JSON.stringify(sessionInfo, null, 2)}
                        </pre>
                    </div>
                )}

                {authInfo && (
                    <div className="border p-4 rounded bg-gray-50">
                        <h3 className="font-bold mb-2">Auth Info:</h3>
                        <pre className="text-sm overflow-auto">
                            {JSON.stringify(authInfo, null, 2)}
                        </pre>
                    </div>
                )}

                <div className="border p-4 rounded bg-yellow-50">
                    <h3 className="font-bold mb-2">Browser Cookies:</h3>
                    <pre className="text-sm">
                        {document.cookie || 'No cookies found'}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default SessionTest;