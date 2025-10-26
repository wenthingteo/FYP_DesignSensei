import React from "react";
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";

const WelcomePage = () => {
  return (
    <div className="d-flex flex-column align-items-center text-center px-4 py-4" style={{ minHeight: "100%", overflowY: "auto" }}>
      {/* Robot Animation Container */}
      <div 
        className="w-75 w-sm-50 w-md-33 mb-3"
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

      {/* Disclaimer Section */}
      <div className="mb-3" style={{ maxWidth: "900px" }}>
        <div className="card border-0 shadow-sm" style={{ backgroundColor: "#f8f9fa" }}>
          <div className="card-body px-5 py-4">
            <h5 className="fw-bold mb-3" style={{ color: "#004080", fontSize: "1.2rem" }}>
              📚 My Areas of Expertise
            </h5>
            <p className="text-muted mb-3" style={{ fontSize: "0.95rem" }}>
              I specialize exclusively in software design topics. Here's what I can help you with:
            </p>
            
            {/* Topics Grid */}
            <div className="row g-3 mb-3">
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  🎯 Design Patterns
                </div>
              </div>
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  🟢 SOLID Principles
                </div>
              </div>
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  🏛️ Architecture
                </div>
              </div>
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  🎨 Domain Driven Design
                </div>
              </div>
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  ✨ Quality
                </div>
              </div>
              <div className="col-6 col-md-4">
                <div className="badge bg-blue-dark text-white p-3 w-100" style={{ fontSize: "1.1rem" }}>
                  📂 Code Structure
                </div>
              </div>
            </div>
            
            <p className="text-muted mb-0" style={{ fontSize: "0.9rem" }}>
              <strong>Please note:</strong> I may not be able to answer questions beyond the topics mentioned above.
            </p>
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