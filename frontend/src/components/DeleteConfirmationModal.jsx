import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';
import './DeleteConfirmationModal.css'; 

const DeleteConfirmationModal = ({ show, onConfirm, onCancel }) => {
  if (!show) {
    return null;
  }

  return (
    <div
      className="modal-overlay position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center"
      onClick={onCancel}
    >
      <div
        className="modal-dialog modal-dialog-centered"
        onClick={(e) => e.stopPropagation()} 
      >
        <div className="modal-content"> 
          <button type="button" className="btn-close" aria-label="Close" onClick={onCancel}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
          
          <div className="modal-header d-flex justify-content-between align-items-center mb-3">
            <h5 className="modal-title mb-0">Confirm Deletion</h5>
          </div>
          
          <div className="modal-body mb-3">
            <p>Are you sure you want to delete this conversation? This action cannot be undone.</p>
          </div>
          
          <div className="modal-footer d-flex justify-content-end gap-2">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={onConfirm}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;