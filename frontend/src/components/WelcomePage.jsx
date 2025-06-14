import React from "react";
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";

const WelcomePage = () => {
  return (
    <div className="d-flex flex-column align-items-center text-center px-4 py-4" style={{ minHeight: "100%", overflowY: "auto" }}>
      {/* Robot Animation Container */}
      <div 
        className="w-75 w-sm-50 w-md-33 mb-4"
        style={{ maxWidth: "300px", height: "auto" }}
      >
        <Lottie animationData={robotAnimation} loop />
      </div>
      
      {/* Welcome Message */}
      <div className="mb-4">
        <h1 className="display-4 mb-3" style={{ color: "#004080", fontWeight: "600" }}>
          Hello! 👋
        </h1>
        <p className="lead text-muted mb-4" style={{ fontSize: "1.25rem", maxWidth: "600px" }}>
          Welcome to Software Design Sensei! I'm here to help you with all your software design questions and challenges.
        </p>
      </div>

      {/* Features Section */}
      <div className="row text-start" style={{ maxWidth: "800px" }}>
        {/* Feature 1: Design Patterns */}
        <div className="col-md-4 mb-3">
          <div className="d-flex align-items-start gap-3">
            <div className="bg-blue-light rounded-circle p-2" style={{ minWidth: "40px", height: "40px" }}>
              <span style={{ fontSize: "1.2rem" }}>💡</span>
            </div>
            <div>
              <h6 className="fw-bold mb-1">Design Patterns</h6>
              <small className="text-muted">Get help with software design patterns and best practices</small>
            </div>
          </div>
        </div>
        
        {/* Feature 2: Architecture */}
        <div className="col-md-4 mb-3">
          <div className="d-flex align-items-start gap-3">
            <div className="bg-blue-light rounded-circle p-2" style={{ minWidth: "40px", height: "40px" }}>
              <span style={{ fontSize: "1.2rem" }}>🏗️</span>
            </div>
            <div>
              <h6 className="fw-bold mb-1">Architecture</h6>
              <small className="text-muted">Discuss system architecture and design decisions</small>
            </div>
          </div>
        </div>
        
        {/* Feature 3: Code Review */}
        <div className="col-md-4 mb-3">
          <div className="d-flex align-items-start gap-3">
            <div className="bg-blue-light rounded-circle p-2" style={{ minWidth: "40px", height: "40px" }}>
              <span style={{ fontSize: "1.2rem" }}>🔧</span>
            </div>
            <div>
              <h6 className="fw-bold mb-1">Code Review</h6>
              <small className="text-muted">Get feedback on your code structure and design</small>
            </div>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="mt-4">
        <p className="text-muted mb-0" style={{ fontSize: "1.1rem" }}>
          Start by typing your question in the chat box below! 💬
        </p>
      </div>
    </div>
  );
};

export default WelcomePage;