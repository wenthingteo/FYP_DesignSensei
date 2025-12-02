import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../config';
import './AdminDashboard.css';

function AdminDashboard() {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFeedbacks();
  }, []);

  const fetchFeedbacks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/feedback/`, {
        withCredentials: true,
      });
      
      if (response.data.success) {
        setFeedbacks(response.data.feedbacks);
        setIsAdmin(true);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching feedbacks:', err);
      
      if (err.response?.status === 403) {
        setError('Access denied. Admin privileges required.');
        setIsAdmin(false);
      } else if (err.response?.status === 401) {
        setError('Not authenticated. Please login.');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError('Failed to load feedback submissions.');
      }
      setLoading(false);
    }
  };

  const handleDelete = async (feedbackId) => {
    if (!window.confirm('Are you sure you want to delete this feedback?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/api/admin/feedback/${feedbackId}/`, {
        withCredentials: true,
      });
      
      // Remove from local state
      setFeedbacks(feedbacks.filter(fb => fb.id !== feedbackId));
    } catch (err) {
      console.error('Error deleting feedback:', err);
      alert('Failed to delete feedback.');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading">Loading feedback submissions...</div>
      </div>
    );
  }

  if (error && !isAdmin) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/chatbot')} className="back-button">
          Go Back to Chatbot
        </button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Admin Dashboard - User Feedback</h1>
        <button onClick={() => navigate('/login')} className="back-button">
          Back to Home
        </button>
      </div>

      <div className="feedback-stats">
        <div className="stat-card">
          <div className="stat-number">{feedbacks.length}</div>
          <div className="stat-label">Total Submissions</div>
        </div>
      </div>

      {feedbacks.length === 0 ? (
        <div className="no-feedback">
          <p>No feedback submissions yet.</p>
        </div>
      ) : (
        <div className="feedback-table-container">
          <table className="feedback-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Email</th>
                <th>Comment</th>
                <th>Submitted At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {feedbacks.map((feedback) => (
                <tr key={feedback.id}>
                  <td>{feedback.id}</td>
                  <td>{feedback.username}</td>
                  <td>{feedback.email}</td>
                  <td className="comment-cell">
                    <div className="comment-content">{feedback.comment}</div>
                  </td>
                  <td className="date-cell">{formatDate(feedback.created_at)}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(feedback.id)}
                      className="delete-button"
                      title="Delete feedback"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
