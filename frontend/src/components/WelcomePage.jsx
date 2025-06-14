import React from "react";
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";

const WelcomePage = () => {
  return (
    <div className="d-flex flex-column justify-content-center align-items-center h-100 text-center px-4">
      {/* Robot Animation */}
      <div style={{ width: "300px", height: "300px", marginBottom: "2rem" }}>
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

      {/* Features */}
      <div className="row text-start" style={{ maxWidth: "800px" }}>
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