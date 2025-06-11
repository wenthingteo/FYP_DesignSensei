import React, { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faClock } from '@fortawesome/free-solid-svg-icons';

const FeedbackPage = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    feedback: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Add your form submission logic here (e.g., API call)
    console.log("Form submitted:", formData);
    alert("Thank you for your feedback!");
    setFormData({ name: "", email: "", feedback: "" }); // Reset form
  };

  return (
    <div className="d-flex flex-column vh-100">
      {/* Header */}
      <div className="d-flex align-items-center justify-content-between px-3 py-2 bg-white border-bottom">
        <h1 className="h5 m-0">Design Sensei</h1>
        <FontAwesomeIcon icon={faClock} size="lg" />
      </div>

      {/* Feedback Form */}
      <div className="flex-grow-1 d-flex justify-content-center align-items-center p-4 bg-blue-light">
        <form onSubmit={handleSubmit} style={{ width: "400px", background: "white", padding: "20px", borderRadius: "10px" }}>
          <h2 className="text-center mb-4">Feedback Form</h2>
          <p className="text-center mb-4">Let us know — your feedback helps us improve!</p>
          
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
            <button type="submit" className="btn bg-blue-dark text-white">Send Feedback</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FeedbackPage;