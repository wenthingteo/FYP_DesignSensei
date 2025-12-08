import React from "react";
import Lottie from "lottie-react";
import robotAnimation from "../assets/robot_animation.json";

const WelcomePage = () => {
  return (
    <div 
      className="d-flex align-items-center justify-content-center px-4" 
      style={{ 
        minHeight: "100%", 
        height: "100%", 
        overflow: "hidden",
      }}
    >
      <div className="row w-100 g-5 align-items-center" style={{ maxWidth: "1400px" }}>
        {/* Left Side - Robot Animation with Glow Effect */}
        <div className="col-12 col-md-5 d-flex justify-content-center">
          <div 
            style={{ 
              maxWidth: "500px", 
              width: "100%",
            }}
          >
            <Lottie animationData={robotAnimation} loop />
          </div>
        </div>
        
        {/* Right Side - Content with Glass Morphism */}
        <div className="col-12 col-md-7">
          {/* Welcome Message */}
          <div className="mb-4">
            <h1 
              className="display-4 mb-3" 
              style={{ 
                fontWeight: "700",
                textShadow: "2px 2px 4px rgba(0,0,0,0.2)"
              }}
            >
              Hello!
            </h1>
            <p 
              className="lead mb-4" 
              style={{ 
                fontSize: "1.2rem",
                lineHeight: "1.6"
              }}
            >
              Welcome to <strong>Software Design Sensei</strong>! I'm here to help you master software design concepts and tackle your challenges.
            </p>
          </div>

          {/* Expertise Card with Glass Effect */}
          <div style={{ maxWidth: "750px" }}>
            <div 
              className="card border-0" 
              style={{ 
                background: "rgba(255, 255, 255, 0.95)",
                borderRadius: "20px",
                boxShadow: "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
                backdropFilter: "blur(10px)",
                border: "1px solid rgba(255, 255, 255, 0.18)"
              }}
            >
              <div className="card-body px-4 py-4">
                <h5 
                  className="fw-bold mb-3 d-flex align-items-center" 
                  style={{ 
                    color: "#3980D0", 
                    fontSize: "1.3rem"
                  }}
                >
                  My Areas of Expertise
                </h5>
                <p className="text-muted mb-3" style={{ fontSize: "0.95rem", lineHeight: "1.5" }}>
                  I specialize exclusively in software design topics. Let me guide you through:
                </p>
                
                {/* Topics Grid with Modern Style */}
                <div className="row g-3 mb-3">
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      Design Patterns
                    </div>
                  </div>
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      SOLID Principles
                    </div>
                  </div>
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      Architecture
                    </div>
                  </div>
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      Domain Driven Design
                    </div>
                  </div>
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      Quality
                    </div>
                  </div>
                  <div className="col-6 col-lg-4">
                    <div 
                      className="text-white p-3 w-100 text-center" 
                      style={{ 
                        fontSize: "0.95rem",
                        backgroundColor: "#3980D0",
                        borderRadius: "12px",
                        fontWeight: "500",
                        boxShadow: "0 4px 15px rgba(57, 128, 208, 0.4)",
                        transition: "transform 0.2s",
                        cursor: "default"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
                      onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                    >
                      Code Structure
                    </div>
                  </div>
                </div>
                
                <div 
                  className="p-3" 
                  style={{ 
                    backgroundColor: "#fff3cd",
                    borderRadius: "10px",
                    borderLeft: "4px solid #ffc107"
                  }}
                >
                  <p className="mb-0" style={{ fontSize: "0.9rem", color: "#856404" }}>
                    <strong>Note:</strong> I may not be able to answer questions beyond the topics mentioned above.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Call to Action with Animated Arrow */}
          <div className="mt-4 text-center">
            <p 
              className="mb-0" 
              style={{ 
                fontSize: "1.15rem",
                fontWeight: "500",
                textShadow: "1px 1px 2px rgba(0,0,0,0.2)"
              }}
            >
              Start by typing your question below!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;