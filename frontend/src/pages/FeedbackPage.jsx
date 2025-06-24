import React, { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faSignOutAlt } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from "react-router-dom";
import axios from "axios";

const FeedbackPage = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    feedback: "",
  });
  const [submissionStatus, setSubmissionStatus] = useState(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmissionStatus(null);

    const csrfToken = getCookie('csrftoken');

    try {
      const response = await axios.post("http://127.0.0.1:8000/api/feedback/", 
        { 
          comment: formData.feedback 
        }, 
        {
          withCredentials: true,
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          },
        }
      );

      if (response.data.success) {
        setSubmissionStatus('success');
        setFormData({ name: "", email: "", feedback: "" });
      } else {
        setSubmissionStatus('error');
        console.error("Feedback submission failed:", response.data.error);
      }
    } catch (error) {
      setSubmissionStatus('error');
      console.error("Error submitting feedback:", error);
      if (error.response && error.response.status === 401) {
        console.error("Authentication required. Please log in.");
      } else if (error.response && error.response.data && error.response.data.error) {
        setSubmissionStatus('error');
        console.error("Backend error:", error.response.data.error);
      } else {
        setSubmissionStatus('error');
        console.error("An unexpected error occurred.");
      }
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/api/logout/", {}, {
        withCredentials: true,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        },
      });
      document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      navigate('/login');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className="d-flex flex-column vh-100">
      {/* Header */}
      <div className="d-flex align-items-center justify-content-between px-4 py-3 bg-white border-bottom shadow-sm">
        {/* Home Button */}
        <button
          className="btn text-dark"
          onClick={() => navigate("/chatbot")} 
          aria-label="Go to Chatbot Home"
        >
          <FontAwesomeIcon icon={faHome} size="lg" />
        </button>

        <h1 className="fs-3 m-0 flex-grow-1 text-center">Design Sensei Feedback</h1> {/* Updated title */}
        
        {/* Logout Button */}
        <button className="btn btn-outline-danger" onClick={handleLogout}>
          <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
          Logout
        </button>
      </div>

      {/* Feedback Form */}
      <div className="flex-grow-1 d-flex justify-content-center align-items-center p-4 bg-blue-light">
        <form onSubmit={handleSubmit} style={{ width: "400px", background: "white", padding: "20px", borderRadius: "10px" }}>
          <h2 className="text-center mb-4">Feedback Form</h2>
          <p className="text-center mb-4">Let us know — your feedback helps us improve!</p>
          
          {/* Submission Status Message */}
          {submissionStatus === 'success' && (
            <div className="alert alert-success text-center mb-3" role="alert">
              Thank you for your feedback!
            </div>
          )}
          {submissionStatus === 'error' && (
            <div className="alert alert-danger text-center mb-3" role="alert">
              Failed to submit feedback. Please try again.
            </div>
          )}

          <div className="mb-3">
            <input
              type="text"
              className="form-control"
              name="name"
              placeholder="Name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="mb-3">
            <input
              type="email"
              className="form-control"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="mb-3">
            <textarea
              className="form-control"
              name="feedback"
              placeholder="Your Feedback"
              value={formData.feedback}
              onChange={handleChange}
              rows="5"
              required
            />
          </div>
          
          <div className="text-center">
            <button type="submit" className="btn bg-blue-dark text-white"
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2C5E97')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3980D0')}
            >Send Feedback</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FeedbackPage;