import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { ChatContext } from "../context/ChatContext";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminError, setAdminError] = useState("");
  const [adminLoading, setAdminLoading] = useState(false);
  
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState("");
  const [resetError, setResetError] = useState("");
  
  const navigate = useNavigate();
  const { fetchChats } = useContext(ChatContext);

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://127.0.0.1:8000/api/login/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log("Login success:", data);
        await fetchChats();
        navigate("/chatbot");
      } else {
        setErrorMsg(data.error || "Login failed");
      }
    } catch (error) {
      console.error("Login error:", error);
      setErrorMsg("Something went wrong. Please try again.");
    }
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setAdminError("");
    setAdminLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/login/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: adminUsername, password: adminPassword }),
      });

      const data = await response.json();

      if (response.ok) {
        // Now check if user has admin access by trying to fetch feedback
        try {
          const feedbackResponse = await fetch("http://127.0.0.1:8000/api/admin/feedback/", {
            method: "GET",
            credentials: "include",
          });

          if (feedbackResponse.ok) {
            // User is admin, navigate to dashboard
            setShowAdminModal(false);
            navigate("/admin/feedback");
          } else if (feedbackResponse.status === 403) {
            setAdminError("Access denied. Admin privileges required.");
          } else {
            setAdminError("Failed to verify admin access.");
          }
        } catch (error) {
          console.error("Admin verification error:", error);
          setAdminError("Failed to verify admin access.");
        }
      } else {
        setAdminError(data.error || "Invalid credentials");
      }
    } catch (error) {
      console.error("Admin login error:", error);
      setAdminError("Something went wrong. Please try again.");
    } finally {
      setAdminLoading(false);
    }
  };

  const openAdminModal = () => {
    setShowAdminModal(true);
    setAdminUsername("");
    setAdminPassword("");
    setAdminError("");
  };

  const closeAdminModal = () => {
    setShowAdminModal(false);
    setAdminUsername("");
    setAdminPassword("");
    setAdminError("");
  };

  const openForgotPasswordModal = () => {
    setShowForgotPasswordModal(true);
    setResetEmail("");
    setResetMessage("");
    setResetError("");
  };

  const closeForgotPasswordModal = () => {
    setShowForgotPasswordModal(false);
    setResetEmail("");
    setResetMessage("");
    setResetError("");
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setResetError("");
    setResetMessage("");

    if (!resetEmail.trim()) {
      setResetError("Please enter your email address");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(resetEmail)) {
      setResetError("Please enter a valid email address");
      return;
    }

    setResetLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/password-reset/request/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: resetEmail.trim().toLowerCase() }),
      });

      const data = await response.json();

      if (response.ok) {
        setResetMessage(data.message);
        setResetEmail("");
      } else {
        setResetError(data.error || "Failed to send reset email");
      }
    } catch (error) {
      console.error("Forgot password error:", error);
      setResetError("Something went wrong. Please try again.");
    } finally {
      setResetLoading(false);
    }
  };

  const styles = {
    container: {
      display: "flex",
      width: "100%",
      minHeight: "100vh",
    },
    leftPanel: {
      flex: "0 0 50%",
      background: "linear-gradient(135deg, #0ea5e9 0%, #1e40af 100%)",
      position: "relative",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "3rem",
    },
    leftContent: {
      textAlign: "center",
      color: "white",
      zIndex: 2,
    },
    leftTitle: {
      fontSize: "3.5rem",
      fontWeight: "700",
      marginBottom: "2rem",
      textShadow: "0 2px 4px rgba(0,0,0,0.1)",
    },
    gradientOverlay: {
      position: "absolute",
      inset: 0,
      background: "radial-gradient(circle at 30% 50%, rgba(255,255,255,0.1) 0%, transparent 50%)",
      pointerEvents: "none",
    },
    rightPanel: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
      backgroundColor: "#ffffff",
      overflowY: "auto",
    },
    formContainer: {
      width: "100%",
      maxWidth: "500px",
    },
    mobileLogoContainer: {
      textAlign: "center",
      marginBottom: "2.5rem",
    },
    mobileLogo: {
      color: "#0ea5e9",
      fontWeight: "700",
      fontSize: "2.25rem",
    },
    formTitle: {
      fontSize: "2.5rem",
      fontWeight: "600",
      color: "#1f2937",
      marginBottom: "0.75rem",
    },
    formSubtitle: {
      color: "#6b7280",
      marginBottom: "2.5rem",
      fontSize: "1.125rem",
    },
    errorMessage: {
      padding: "1rem 1.25rem",
      backgroundColor: "#fee2e2",
      border: "1px solid #fecaca",
      borderRadius: "0.5rem",
      color: "#991b1b",
      marginBottom: "1.75rem",
      fontSize: "1.05rem",
    },
    formGroup: {
      marginBottom: "1.5rem",
    },
    label: {
      display: "block",
      marginBottom: "0.625rem",
      color: "#374151",
      fontSize: "1.05rem",
      fontWeight: "500",
    },
    input: {
      width: "100%",
      padding: "1rem 1.25rem",
      border: "1px solid #d1d5db",
      borderRadius: "0.5rem",
      fontSize: "1.05rem",
      transition: "all 0.2s",
    },
    formOptions: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      // marginBottom: "1.05rem",
    },
    checkbox: {
      marginRight: "0.625rem",
      cursor: "pointer",
      width: "18px",
      height: "18px",
    },
    forgotPassword: {
      background: "none",
      border: "none",
      color: "#3b82f6",
      fontSize: "1.00rem",
      cursor: "pointer",
      padding: 0,
      fontWeight: "500",
    },
    loginBtn: {
      width: "100%",
      padding: "1rem",
      backgroundColor: "#3b82f6",
      color: "white",
      border: "none",
      borderRadius: "0.5rem",
      fontSize: "1.125rem",
      fontWeight: "600",
      cursor: "pointer",
      transition: "all 0.2s",
      boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
    },
    signupLink: {
      textAlign: "center",
      marginTop: "2rem",
      color: "#6b7280",
      fontSize: "1.05rem",
    },
    linkBtn: {
      background: "none",
      border: "none",
      color: "#3b82f6",
      cursor: "pointer",
      padding: 0,
      fontWeight: "600",
      fontSize: "1.05rem",
    },
    adminBtn: {
      width: "100%",
      padding: "0.875rem 1rem",
      backgroundColor: "#6b7280",
      color: "white",
      border: "none",
      borderRadius: "0.5rem",
      fontSize: "1rem",
      fontWeight: "600",
      cursor: "pointer",
      transition: "all 0.2s",
      marginTop: "1.5rem",
      boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
    },
    divider: {
      display: "flex",
      alignItems: "center",
      textAlign: "center",
      margin: "2rem 0 1rem 0",
    },
    dividerLine: {
      flex: 1,
      borderBottom: "1px solid #d1d5db",
    },
    dividerText: {
      padding: "0 1rem",
      color: "#9ca3af",
      fontSize: "0.95rem",
      fontWeight: "500",
    },
    modalOverlay: {
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(0, 0, 0, 0.5)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 1000,
    },
    modalContent: {
      backgroundColor: "white",
      borderRadius: "1rem",
      padding: "2rem",
      width: "90%",
      maxWidth: "450px",
      boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    },
    modalHeader: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "1.5rem",
    },
    modalTitle: {
      fontSize: "1.5rem",
      fontWeight: "600",
      color: "#1f2937",
      margin: 0,
    },
    closeBtn: {
      background: "none",
      border: "none",
      fontSize: "1.5rem",
      color: "#9ca3af",
      cursor: "pointer",
      padding: "0",
      width: "32px",
      height: "32px",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      borderRadius: "0.375rem",
      transition: "all 0.2s",
    },
    modalBody: {
      marginBottom: "1.5rem",
    },
    modalSubtitle: {
      color: "#6b7280",
      marginBottom: "1.5rem",
      fontSize: "0.95rem",
    },
  };

  const mediaQueryStyle = `
    @media (max-width: 1024px) {
      .left-panel-hide {
        display: none !important;
      }
      .mobile-logo-show {
        display: block !important;
      }
    }
    @media (min-width: 1025px) {
      .mobile-logo-show {
        display: none !important;
      }
    }
  `;

  return (
    <>
      <style>{mediaQueryStyle}</style>
      <div style={styles.container}>
        {/* Left Panel */}
        <div style={styles.leftPanel} className="left-panel-hide">
          <div style={styles.leftContent}>
            <h1 style={styles.leftTitle}>Software Design Sensei</h1>
            <svg width="400" height="400" viewBox="0 0 400 400" style={{ filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.2))" }}>
              <g transform="translate(100, 150)">
                <path d="M 0,80 L 80,40 L 240,40 L 160,80 Z" fill="#1e3a8a" opacity="0.9"/>
                <path d="M 60,40 L 140,0 L 140,-120 L 60,-80 Z" fill="#1e40af"/>
                <path d="M 60,-80 L 140,-120 L 220,-120 L 140,-80 Z" fill="#0ea5e9"/>
                <g opacity="0.8">
                  <rect x="70" y="-105" width="60" height="3" fill="#10b981" rx="1"/>
                  <rect x="70" y="-95" width="45" height="3" fill="#f59e0b" rx="1"/>
                  <rect x="70" y="-85" width="50" height="3" fill="#ec4899" rx="1"/>
                  <circle cx="145" cy="-60" r="15" fill="#ec4899" stroke="#fff" strokeWidth="3"/>
                </g>
                <g opacity="0.6">
                  <rect x="15" y="52" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                  <rect x="23" y="52" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                  <rect x="31" y="52" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                  <rect x="15" y="58" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                  <rect x="23" y="58" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                  <rect x="31" y="58" width="4" height="2" fill="#93c5fd" rx="0.5"/>
                </g>
              </g>
              <g opacity="0.7">
                <circle cx="80" cy="100" r="8" fill="#60a5fa"/>
                <circle cx="320" cy="150" r="6" fill="#34d399"/>
                <circle cx="70" cy="280" r="10" fill="#fbbf24"/>
                <rect x="300" y="80" width="15" height="15" fill="#a78bfa" opacity="0.6" transform="rotate(45 307.5 87.5)"/>
              </g>
              <g transform="translate(180, 200)">
                <circle cx="0" cy="-10" r="8" fill="#fbbf24"/>
                <rect x="-6" y="0" width="12" height="20" fill="#fff" rx="2"/>
                <rect x="-8" y="8" width="5" height="15" fill="#fff" rx="2"/>
                <rect x="3" y="8" width="5" height="15" fill="#fff" rx="2"/>
              </g>
            </svg>
          </div>
          <div style={styles.gradientOverlay}></div>
        </div>

        {/* Right Panel */}
        <div style={styles.rightPanel}>
          <div style={styles.formContainer}>
            {/* Mobile Logo */}
            <div style={styles.mobileLogoContainer} className="mobile-logo-show">
              <h2 style={styles.mobileLogo}>Design Sensei</h2>
            </div>

            <div>
              <h2 style={styles.formTitle}>Login to your Account</h2>
              <p style={styles.formSubtitle}>Welcome back! Please enter your details</p>
            </div>

            {errorMsg && (
              <div style={styles.errorMessage}>
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleLogin}>
              {/* Username Input */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                  style={styles.input}
                  onFocus={(e) => {
                    e.currentTarget.style.outline = "2px solid #3b82f6";
                    e.currentTarget.style.outlineOffset = "0px";
                    e.currentTarget.style.borderColor = "#3b82f6";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.outline = "none";
                    e.currentTarget.style.borderColor = "#d1d5db";
                  }}
                />
              </div>

              {/* Password Input */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={styles.input}
                  onFocus={(e) => {
                    e.currentTarget.style.outline = "2px solid #3b82f6";
                    e.currentTarget.style.outlineOffset = "0px";
                    e.currentTarget.style.borderColor = "#3b82f6";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.outline = "none";
                    e.currentTarget.style.borderColor = "#d1d5db";
                  }}
                />
              </div>

              {/* Login Button */}
              <button
                type="submit"
                style={styles.loginBtn}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#2563eb";
                  e.currentTarget.style.boxShadow = "0 4px 6px rgba(59,130,246,0.3)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "#3b82f6";
                  e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
                }}
              >
                Login
              </button>
            </form>

            {/* Forgot Password Link */}
            <div style={{ textAlign: 'center', margin: '1rem 0' }}>
              <button
                onClick={openForgotPasswordModal}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#3b82f6',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  padding: '0',
                  textDecoration: 'none'
                }}
                onMouseEnter={(e) => e.currentTarget.style.textDecoration = "underline"}
                onMouseLeave={(e) => e.currentTarget.style.textDecoration = "none"}
              >
                Forgot Password?
              </button>
            </div>

            {/* Sign Up Link */}
            <p style={styles.signupLink}>
              Not Registered Yet?{" "}
              <button
                onClick={() => navigate("/register")}
                style={styles.linkBtn}
                onMouseEnter={(e) => e.currentTarget.style.textDecoration = "underline"}
                onMouseLeave={(e) => e.currentTarget.style.textDecoration = "none"}
              >
                Create an account
              </button>
            </p>

            {/* Divider */}
            <div style={styles.divider}>
              <div style={styles.dividerLine}></div>
              <span style={styles.dividerText}>ADMIN ACCESS</span>
              <div style={styles.dividerLine}></div>
            </div>

            {/* Admin Feedback Button */}
            <button
              type="button"
              onClick={openAdminModal}
              style={styles.adminBtn}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#4b5563";
                e.currentTarget.style.boxShadow = "0 4px 6px rgba(107,114,128,0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "#6b7280";
                e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
              }}
            >
              View Feedback (Admin)
            </button>
          </div>
        </div>
      </div>

      {/* Admin Login Modal */}
      {showAdminModal && (
        <div style={styles.modalOverlay} onClick={closeAdminModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>Admin Login</h3>
              <button
                onClick={closeAdminModal}
                style={styles.closeBtn}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                  e.currentTarget.style.color = "#1f2937";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "#9ca3af";
                }}
              >
                ×
              </button>
            </div>

            <div style={styles.modalBody}>
              <p style={styles.modalSubtitle}>
                Please enter your admin credentials to access the feedback dashboard.
              </p>

              {adminError && (
                <div style={styles.errorMessage}>
                  {adminError}
                </div>
              )}

              <form onSubmit={handleAdminLogin}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Admin Username</label>
                  <input
                    type="text"
                    value={adminUsername}
                    onChange={(e) => setAdminUsername(e.target.value)}
                    placeholder="Enter admin username"
                    required
                    disabled={adminLoading}
                    style={styles.input}
                    onFocus={(e) => {
                      e.currentTarget.style.outline = "2px solid #3b82f6";
                      e.currentTarget.style.outlineOffset = "0px";
                      e.currentTarget.style.borderColor = "#3b82f6";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.outline = "none";
                      e.currentTarget.style.borderColor = "#d1d5db";
                    }}
                  />
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Admin Password</label>
                  <input
                    type="password"
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    disabled={adminLoading}
                    style={styles.input}
                    onFocus={(e) => {
                      e.currentTarget.style.outline = "2px solid #3b82f6";
                      e.currentTarget.style.outlineOffset = "0px";
                      e.currentTarget.style.borderColor = "#3b82f6";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.outline = "none";
                      e.currentTarget.style.borderColor = "#d1d5db";
                    }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={adminLoading}
                  style={{
                    ...styles.loginBtn,
                    opacity: adminLoading ? 0.6 : 1,
                    cursor: adminLoading ? "not-allowed" : "pointer",
                  }}
                  onMouseEnter={(e) => {
                    if (!adminLoading) {
                      e.currentTarget.style.backgroundColor = "#2563eb";
                      e.currentTarget.style.boxShadow = "0 4px 6px rgba(59,130,246,0.3)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!adminLoading) {
                      e.currentTarget.style.backgroundColor = "#3b82f6";
                      e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
                    }
                  }}
                >
                  {adminLoading ? "Verifying..." : "Login as Admin"}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {showForgotPasswordModal && (
        <div style={styles.modalOverlay} onClick={closeForgotPasswordModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>Reset Password</h3>
              <button
                onClick={closeForgotPasswordModal}
                style={styles.closeBtn}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f3f4f6";
                  e.currentTarget.style.color = "#1f2937";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "#9ca3af";
                }}
              >
                ×
              </button>
            </div>

            <div style={styles.modalBody}>
              <p style={styles.modalSubtitle}>
                Enter your email address and we'll send you a link to reset your password.
              </p>

              {resetError && (
                <div style={styles.errorMessage}>
                  {resetError}
                </div>
              )}

              {resetMessage && (
                <div style={{
                  ...styles.errorMessage,
                  backgroundColor: '#d1fae5',
                  color: '#065f46',
                  borderColor: '#6ee7b7'
                }}>
                  {resetMessage}
                </div>
              )}

              {!resetMessage && (
                <form onSubmit={handleForgotPassword}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Email Address</label>
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="Enter your email"
                      required
                      disabled={resetLoading}
                      style={styles.input}
                      onFocus={(e) => {
                        e.currentTarget.style.outline = "2px solid #3b82f6";
                        e.currentTarget.style.outlineOffset = "0px";
                        e.currentTarget.style.borderColor = "#3b82f6";
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.outline = "none";
                        e.currentTarget.style.borderColor = "#d1d5db";
                      }}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={resetLoading}
                    style={{
                      ...styles.loginBtn,
                      opacity: resetLoading ? 0.6 : 1,
                      cursor: resetLoading ? "not-allowed" : "pointer",
                    }}
                    onMouseEnter={(e) => {
                      if (!resetLoading) {
                        e.currentTarget.style.backgroundColor = "#2563eb";
                        e.currentTarget.style.boxShadow = "0 4px 6px rgba(59,130,246,0.3)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!resetLoading) {
                        e.currentTarget.style.backgroundColor = "#3b82f6";
                        e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
                      }
                    }}
                  >
                    {resetLoading ? "Sending..." : "Send Reset Link"}
                  </button>
                </form>
              )}

              {resetMessage && (
                <button
                  onClick={closeForgotPasswordModal}
                  style={{
                    ...styles.loginBtn,
                    marginTop: '1rem'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "#2563eb";
                    e.currentTarget.style.boxShadow = "0 4px 6px rgba(59,130,246,0.3)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "#3b82f6";
                    e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
                  }}
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default LoginPage;