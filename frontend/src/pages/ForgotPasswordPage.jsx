import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../config';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEnvelope, faArrowLeft } from '@fortawesome/free-solid-svg-icons';
import '../colors.css';

const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/api/password-reset/request/`, {
        email: email.trim().toLowerCase()
      });

      setMessage(response.data.message);
      setEmail(''); // Clear email field
      
    } catch (err) {
      console.error('Error requesting password reset:', err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('An error occurred. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
      <div className="card shadow-lg" style={{ width: '100%', maxWidth: '450px', borderRadius: '15px' }}>
        <div className="card-body p-5">
          {/* Header */}
          <div className="text-center mb-4">
            <h2 className="fw-bold mb-2" style={{ color: '#3980D0' }}>Forgot Password?</h2>
            <p className="text-muted mb-0">
              Enter your email address and we'll send you a link to reset your password.
            </p>
          </div>

          {/* Success Message */}
          {message && (
            <div className="alert alert-success d-flex align-items-center mb-4" role="alert">
              <FontAwesomeIcon icon={faEnvelope} className="me-2" />
              <div>{message}</div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert alert-danger mb-4" role="alert">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="email" className="form-label fw-semibold">
                Email Address
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white">
                  <FontAwesomeIcon icon={faEnvelope} style={{ color: '#6c757d' }} />
                </span>
                <input
                  type="email"
                  className="form-control"
                  id="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  style={{ 
                    borderLeft: 'none',
                    padding: '12px'
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn w-100 text-white fw-semibold mb-3"
              disabled={isLoading}
              style={{
                backgroundColor: '#3980D0',
                padding: '12px',
                fontSize: '16px',
                borderRadius: '8px',
                border: 'none'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#2C5E97'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#3980D0'}
            >
              {isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Sending...
                </>
              ) : (
                'Send Reset Link'
              )}
            </button>

            {/* Back to Login */}
            <div className="text-center">
              <button
                type="button"
                className="btn btn-link text-decoration-none"
                onClick={() => navigate('/login')}
                disabled={isLoading}
                style={{ color: '#3980D0' }}
              >
                <FontAwesomeIcon icon={faArrowLeft} className="me-2" />
                Back to Login
              </button>
            </div>
          </form>

          {/* Info Text */}
          {message && (
            <div className="mt-4 p-3 bg-light rounded">
              <p className="mb-0 text-muted small">
                <strong>Next Steps:</strong>
                <br />
                1. Check your email inbox (and spam folder)
                <br />
                2. Click the reset link in the email
                <br />
                3. Enter your new password
                <br />
                <br />
                <em>The link will expire in 1 hour.</em>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
