import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    // Validate email ends with .com
    if (!email.toLowerCase().endsWith('.com')) {
      setErrorMsg("Email must end with .com");
      return;
    }

    // Validate password length
    if (password.length < 8) {
      setErrorMsg("Password must be at least 8 characters long");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/register/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, email, password1: password, password2: confirmPassword }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log("Registration success:", data);
        navigate("/login");
      } else {
        setErrorMsg(data.error || "Registration failed.");
      }
    } catch (error) {
      console.error("Registration error:", error);
      setErrorMsg("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
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
    registerBtn: {
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
      marginTop: "0.75rem",
    },
    signinLink: {
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
              <h2 style={styles.formTitle}>Sign Up with Us</h2>
              <p style={styles.formSubtitle}>Create your account to get started</p>
            </div>

            {errorMsg && (
              <div style={styles.errorMessage}>
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleRegister}>
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

              {/* Email Input */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="username@domain.com"
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

              {/* Confirm Password Input */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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

              {/* Register Button */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  ...styles.registerBtn,
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.currentTarget.style.backgroundColor = "#2563eb";
                    e.currentTarget.style.boxShadow = "0 4px 6px rgba(59,130,246,0.3)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading) {
                    e.currentTarget.style.backgroundColor = "#3b82f6";
                    e.currentTarget.style.boxShadow = "0 1px 2px rgba(0,0,0,0.05)";
                  }
                }}
              >
                {loading ? "Signing Up..." : "Sign Up"}
              </button>
            </form>

            {/* Sign In Link */}
            <p style={styles.signinLink}>
              Already have an account?{" "}
              <button
                onClick={() => navigate("/login")}
                style={styles.linkBtn}
                onMouseEnter={(e) => e.currentTarget.style.textDecoration = "underline"}
                onMouseLeave={(e) => e.currentTarget.style.textDecoration = "none"}
              >
                Sign In
              </button>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

export default RegisterPage;