import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRotate, faExclamationTriangle, faWifi, faServer } from '@fortawesome/free-solid-svg-icons';
import './ErrorMessage.css';

const ErrorMessage = ({ errorState, errorMessage, onRetry, isRetryDisabled }) => {
  const getErrorIcon = () => {
    switch (errorState) {
      case 'timeout':
        return faExclamationTriangle;
      case 'network':
        return faWifi;
      case 'server':
        return faServer;
      default:
        return faExclamationTriangle;
    }
  };

  const getErrorTitle = () => {
    switch (errorState) {
      case 'timeout':
        return 'Request Timeout';
      case 'network':
        return 'Connection Issue';
      case 'server':
        return 'Server Error';
      default:
        return 'Error';
    }
  };

  const getErrorColorClass = () => {
    switch (errorState) {
      case 'timeout':
        return 'error-warning';
      case 'network':
        return 'error-danger';
      case 'server':
        return 'error-danger';
      default:
        return 'error-warning';
    }
  };

  if (!errorState) return null;

  return (
    <div className={`error-message-container ${getErrorColorClass()}`}>
      <div className="error-content">
        <div className="error-header">
          <FontAwesomeIcon icon={getErrorIcon()} className="error-icon" />
          <h4 className="error-title">{getErrorTitle()}</h4>
        </div>
        <p className="error-description">{errorMessage}</p>
        <button
          className="error-retry-btn"
          onClick={onRetry}
          disabled={isRetryDisabled}
        >
          <FontAwesomeIcon icon={faRotate} className="me-2" />
          Regenerate Response
        </button>
      </div>
    </div>
  );
};

export default ErrorMessage;
