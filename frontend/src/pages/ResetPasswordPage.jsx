import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLock, faEye, faEyeSlash, faCheckCircle } from '@fortawesome/free-solid-svg-icons';
import '../colors.css';

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [isValidating, setIsValidating] = useState(true);
  const [isValid, setIsValid] = useState(false);
  const [tokenError, setTokenError] = useState('');
  const [userEmail, setUserEmail] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Validate token on mount
  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setTokenError('Invalid reset link. Please request a new password reset.');
        setIsValidating(false);
        return;
      }

      try {
        const response = await axios.get(
          `http://127.0.0.1:8000/api/password-reset/validate/?token=${token}`
        );

        if (response.data.valid) {
          setIsValid(true);
          setUserEmail(response.data.email);
        } else {
          setTokenError(response.data.error || 'Invalid reset link');
        }
      } catch (err) {
        console.error('Error validating token:', err);
        setTokenError('Failed to validate reset link. Please try again.');
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!newPassword || !confirmPassword) {
      setError('Please fill in both password fields');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await axios.post('http://127.0.0.1:8000/api/password-reset/confirm/', {
        token: token,
        new_password: newPassword
      });

      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);

    } catch (err) {
      console.error('Error resetting password:', err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state
  if (isValidating) {
    return (
      <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
        <div className="text-center">
          <div className="spinner-border text-primary mb-3" style={{ width: '3rem', height: '3rem' }} role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted">Validating reset link...</p>
        </div>
      </div>
    );
  }

  // Invalid token
  if (!isValid) {
    return (
      <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
        <div className="card shadow-lg" style={{ width: '100%', maxWidth: '450px', borderRadius: '15px' }}>
          <div className="card-body p-5 text-center">
            <div className="mb-4">
              <div 
                className="rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
                style={{ width: '80px', height: '80px', backgroundColor: '#f8d7da' }}
              >
                <FontAwesomeIcon icon={faLock} size="2x" style={{ color: '#dc3545' }} />
              </div>
              <h2 className="fw-bold mb-2" style={{ color: '#dc3545' }}>Invalid Reset Link</h2>
              <p className="text-muted">{tokenError}</p>
            </div>
            
            <button
              className="btn btn-primary w-100 mb-2"
              onClick={() => navigate('/forgot-password')}
              style={{ 
                backgroundColor: '#3980D0',
                borderColor: '#3980D0',
                padding: '12px'
              }}
            >
              Request New Reset Link
            </button>
            
            <button
              className="btn btn-link text-decoration-none"
              onClick={() => navigate('/login')}
              style={{ color: '#3980D0' }}
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
        <div className="card shadow-lg" style={{ width: '100%', maxWidth: '450px', borderRadius: '15px' }}>
          <div className="card-body p-5 text-center">
            <div className="mb-4">
              <div 
                className="rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
                style={{ width: '80px', height: '80px', backgroundColor: '#d1e7dd' }}
              >
                <FontAwesomeIcon icon={faCheckCircle} size="2x" style={{ color: '#198754' }} />
              </div>
              <h2 className="fw-bold mb-2" style={{ color: '#198754' }}>Password Reset Successful!</h2>
              <p className="text-muted">
                Your password has been successfully reset.
                <br />
                Redirecting to login page...
              </p>
            </div>
            
            <button
              className="btn w-100"
              onClick={() => navigate('/login')}
              style={{ 
                backgroundColor: '#3980D0',
                borderColor: '#3980D0',
                color: 'white',
                padding: '12px'
              }}
            >
              Go to Login Now
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Reset password form
  return (
    <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
      <div className="card shadow-lg" style={{ width: '100%', maxWidth: '450px', borderRadius: '15px' }}>
        <div className="card-body p-5">
          {/* Header */}
          <div className="text-center mb-4">
            <h2 className="fw-bold mb-2" style={{ color: '#3980D0' }}>Reset Your Password</h2>
            <p className="text-muted mb-0">
              Enter your new password for
              <br />
              <strong>{userEmail}</strong>
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="alert alert-danger mb-4" role="alert">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {/* New Password */}
            <div className="mb-3">
              <label htmlFor="newPassword" className="form-label fw-semibold">
                New Password
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white">
                  <FontAwesomeIcon icon={faLock} style={{ color: '#6c757d' }} />
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-control"
                  id="newPassword"
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={isLoading}
                  style={{ 
                    borderLeft: 'none',
                    borderRight: 'none',
                    padding: '12px'
                  }}
                />
                <span 
                  className="input-group-text bg-white"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <FontAwesomeIcon 
                    icon={showPassword ? faEyeSlash : faEye} 
                    style={{ color: '#6c757d' }} 
                  />
                </span>
              </div>
              <small className="text-muted">Must be at least 8 characters</small>
            </div>

            {/* Confirm Password */}
            <div className="mb-4">
              <label htmlFor="confirmPassword" className="form-label fw-semibold">
                Confirm New Password
              </label>
              <div className="input-group">
                <span className="input-group-text bg-white">
                  <FontAwesomeIcon icon={faLock} style={{ color: '#6c757d' }} />
                </span>
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="form-control"
                  id="confirmPassword"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isLoading}
                  style={{ 
                    borderLeft: 'none',
                    borderRight: 'none',
                    padding: '12px'
                  }}
                />
                <span 
                  className="input-group-text bg-white"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  <FontAwesomeIcon 
                    icon={showConfirmPassword ? faEyeSlash : faEye} 
                    style={{ color: '#6c757d' }} 
                  />
                </span>
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
                  Resetting Password...
                </>
              ) : (
                'Reset Password'
              )}
            </button>

            <div className="text-center">
              <button
                type="button"
                className="btn btn-link text-decoration-none"
                onClick={() => navigate('/login')}
                disabled={isLoading}
                style={{ color: '#3980D0' }}
              >
                Back to Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
