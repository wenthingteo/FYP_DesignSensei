import React, { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faSignOutAlt, faStar, faBug, faLightbulb, faCommentDots, faCheck } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API_BASE from "../config";

const FeedbackPage = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    feedback: "",
    rating: 0,
    feedbackType: "",
  });
  const [submissionStatus, setSubmissionStatus] = useState(null);
  const [hoveredRating, setHoveredRating] = useState(0);
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
      const response = await axios.post(`${API_BASE}/api/feedback/`, 
        { 
          comment: formData.feedback,
          rating: formData.rating,
          feedbackType: formData.feedbackType || 'general',
          name: formData.name,
          email: formData.email
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
        setFormData({ name: "", email: "", feedback: "", rating: 0, feedbackType: "" });
        
        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          setSubmissionStatus(null);
        }, 3000);
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
      await axios.post(`${API_BASE}/api/logout/`, {}, {
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
    <div className="d-flex flex-column vh-100" style={{ backgroundColor: '#f8f9fa', overflow: 'hidden' }}>
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

        <h1 className="fs-3 m-0 flex-grow-1 text-center" style={{ color: '#3980D0', fontWeight: '600' }}>
          We Value Your Feedback
        </h1>
        
        {/* Logout Button */}
        <button className="btn btn-outline-danger" onClick={handleLogout}>
          <FontAwesomeIcon icon={faSignOutAlt} className="me-2" />
          Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-grow-1 d-flex justify-content-center align-items-center p-4" style={{ overflow: 'hidden' }}>
        <div className="row w-100 g-4" style={{ maxWidth: "1300px", maxHeight: "calc(100vh - 100px)" }}>
          
          {/* Left Side - Info Card */}
          <div className="col-md-4 d-flex align-items-stretch">
            <div 
              className="card border-0 h-100 w-100" 
              style={{ 
                background: 'linear-gradient(135deg, #3980D0 0%, #2C5E97 100%)',
                borderRadius: '16px',
                boxShadow: '0 8px 24px rgba(57, 128, 208, 0.3)',
                padding: '35px 30px',
                color: 'white'
              }}
            >
              <div className="text-center mb-4">
                <div 
                  style={{ 
                    width: '90px', 
                    height: '90px', 
                    background: 'rgba(255, 255, 255, 0.2)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 15px',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <FontAwesomeIcon icon={faCommentDots} size="2x" />
                </div>
                <h2 style={{ fontSize: '1.75rem', fontWeight: '700', marginBottom: '15px' }}>
                  Help Us Improve
                </h2>
                <p style={{ fontSize: '1.05rem', lineHeight: '1.6', opacity: '0.95', marginBottom: '20px' }}>
                  Your feedback shapes the future of Software Design Sensei.
                </p>
              </div>
              
              <div>
                <div className="mb-3 d-flex align-items-center">
                  <div 
                    style={{ 
                      width: '38px', 
                      height: '38px', 
                      background: 'rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '12px',
                      fontSize: '0.9rem'
                    }}
                  >
                    <FontAwesomeIcon icon={faCheck} />
                  </div>
                  <span style={{ fontSize: '1rem' }}>Quick and easy</span>
                </div>
                <div className="mb-3 d-flex align-items-center">
                  <div 
                    style={{ 
                      width: '38px', 
                      height: '38px', 
                      background: 'rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '12px',
                      fontSize: '0.9rem'
                    }}
                  >
                    <FontAwesomeIcon icon={faCheck} />
                  </div>
                  <span style={{ fontSize: '1rem' }}>Anonymous option</span>
                </div>
                <div className="d-flex align-items-center">
                  <div 
                    style={{ 
                      width: '38px', 
                      height: '38px', 
                      background: 'rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '12px',
                      fontSize: '0.9rem'
                    }}
                  >
                    <FontAwesomeIcon icon={faCheck} />
                  </div>
                  <span style={{ fontSize: '1rem' }}>Direct impact</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Feedback Form */}
          <div className="col-md-8" style={{ maxHeight: 'calc(100vh - 100px)', overflowY: 'auto', padding: '5px' }}>
            <div 
              className="card border-0" 
              style={{ 
                background: 'white',
                borderRadius: '16px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
                padding: '35px'
              }}
            >
              {/* Success Message with Animation */}
              {submissionStatus === 'success' && (
                <div 
                  className="alert alert-success text-center mb-3" 
                  style={{ 
                    borderRadius: '10px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: 'white',
                    fontSize: '1rem',
                    fontWeight: '500',
                    padding: '15px',
                    animation: 'slideDown 0.5s ease-out'
                  }}
                >
                  <FontAwesomeIcon icon={faCheck} className="me-2" />
                  Thank you for your feedback!
                </div>
              )}
              
              {submissionStatus === 'error' && (
                <div 
                  className="alert alert-danger text-center mb-3" 
                  style={{ 
                    borderRadius: '10px',
                    border: 'none',
                    fontSize: '0.9rem',
                    padding: '12px'
                  }}
                >
                  Failed to submit. Please try again.
                </div>
              )}

              <form onSubmit={handleSubmit}>
                {/* Feedback Type Selection */}
                <div className="mb-3">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '1rem', color: '#333', marginBottom: '10px' }}>
                    Feedback Type
                  </label>
                  <div className="d-flex gap-2 flex-wrap">
                    {[
                      { value: 'bug', label: 'Bug Report', icon: faBug },
                      { value: 'feature', label: 'Feature Request', icon: faLightbulb },
                      { value: 'general', label: 'General Feedback', icon: faCommentDots }
                    ].map((type) => (
                      <button
                        key={type.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, feedbackType: type.value })}
                        style={{
                          flex: '1',
                          minWidth: '140px',
                          padding: '12px 18px',
                          border: formData.feedbackType === type.value ? '2px solid #3980D0' : '2px solid #e5e7eb',
                          backgroundColor: formData.feedbackType === type.value ? '#EBF4FF' : 'white',
                          color: formData.feedbackType === type.value ? '#3980D0' : '#6b7280',
                          borderRadius: '10px',
                          cursor: 'pointer',
                          fontWeight: '500',
                          fontSize: '0.95rem',
                          transition: 'all 0.2s',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px'
                        }}
                        onMouseEnter={(e) => {
                          if (formData.feedbackType !== type.value) {
                            e.currentTarget.style.borderColor = '#3980D0';
                            e.currentTarget.style.backgroundColor = '#f9fafb';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (formData.feedbackType !== type.value) {
                            e.currentTarget.style.borderColor = '#e5e7eb';
                            e.currentTarget.style.backgroundColor = 'white';
                          }
                        }}
                      >
                        <FontAwesomeIcon icon={type.icon} />
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Rating System */}
                <div className="mb-3">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '0.9rem', color: '#333', marginBottom: '8px' }}>
                    Rate your experience
                  </label>
                  <div className="d-flex gap-2 justify-content-center mb-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <FontAwesomeIcon
                        key={star}
                        icon={faStar}
                        size="2x"
                        style={{
                          color: star <= (hoveredRating || formData.rating) ? '#fbbf24' : '#e5e7eb',
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                        onMouseEnter={() => setHoveredRating(star)}
                        onMouseLeave={() => setHoveredRating(0)}
                        onClick={() => setFormData({ ...formData, rating: star })}
                      />
                    ))}
                  </div>
                  <div className="text-center text-muted" style={{ fontSize: '0.95rem' }}>
                    {formData.rating === 0 ? 'Click to rate' : 
                     formData.rating === 1 ? 'Poor' :
                     formData.rating === 2 ? 'Fair' :
                     formData.rating === 3 ? 'Good' :
                     formData.rating === 4 ? 'Very Good' : 'Excellent'}
                  </div>
                </div>

                {/* Name Input */}
                <div className="mb-3">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '0.95rem', color: '#333', marginBottom: '8px' }}>
                    Name (Optional)
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    name="name"
                    placeholder="Enter your name"
                    value={formData.name}
                    onChange={handleChange}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      border: '2px solid #e5e7eb',
                      fontSize: '0.95rem',
                      transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = '#3980D0'}
                    onBlur={(e) => e.currentTarget.style.borderColor = '#e5e7eb'}
                  />
                </div>

                {/* Email Input */}
                <div className="mb-3">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '0.95rem', color: '#333', marginBottom: '8px' }}>
                    Email (Optional)
                  </label>
                  <input
                    type="email"
                    className="form-control"
                    name="email"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      border: '2px solid #e5e7eb',
                      fontSize: '0.95rem',
                      transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = '#3980D0'}
                    onBlur={(e) => e.currentTarget.style.borderColor = '#e5e7eb'}
                  />
                </div>

                {/* Feedback Textarea */}
                <div className="mb-3">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '0.95rem', color: '#333', marginBottom: '8px' }}>
                    Your Feedback *
                  </label>
                  <textarea
                    className="form-control"
                    name="feedback"
                    placeholder="Share your thoughts with us..."
                    value={formData.feedback}
                    onChange={handleChange}
                    rows="4"
                    required
                    maxLength={500}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      border: '2px solid #e5e7eb',
                      fontSize: '0.95rem',
                      transition: 'border-color 0.2s',
                      resize: 'vertical'
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = '#3980D0'}
                    onBlur={(e) => e.currentTarget.style.borderColor = '#e5e7eb'}
                  />
                  <div className="text-end text-muted mt-1" style={{ fontSize: '0.85rem' }}>
                    {formData.feedback.length}/500 characters
                  </div>
                </div>

                {/* Submit Button */}
                <div className="text-center">
                  <button 
                    type="submit" 
                    className="btn text-white w-100"
                    style={{
                      backgroundColor: '#3980D0',
                      padding: '14px 32px',
                      borderRadius: '12px',
                      fontSize: '1.05rem',
                      fontWeight: '600',
                      border: 'none',
                      boxShadow: '0 4px 15px rgba(57, 128, 208, 0.3)',
                      transition: 'all 0.3s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#2C5E97';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 6px 20px rgba(57, 128, 208, 0.4)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#3980D0';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 4px 15px rgba(57, 128, 208, 0.3)';
                    }}
                  >
                    Submit Feedback
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default FeedbackPage;