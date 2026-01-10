import { useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config';

const TestConnection = () => {
  useEffect(() => {
    axios.get(`${API_BASE}/api/ping/`)
      .then(res => {
        console.log("Backend is connected:", res.data);
      })
      .catch(err => {
        console.error("Failed to connect to backend:", err.message);
      });
  }, []);

  return <div>Testing backend connection...</div>;
};

export default TestConnection;
