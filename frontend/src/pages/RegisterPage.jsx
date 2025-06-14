import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/register/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
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
    }
  };

  return (
    <div className="container mt-5" style={{ maxWidth: "400px" }}>
      <h2 className="mb-4 text-center">Register</h2>
      {/* Display error message if present */}
      {errorMsg && (
        <div className="alert alert-danger" role="alert">
          {errorMsg}
        </div>
      )}
      <form onSubmit={handleRegister}>
        {/* Username Input */}
        <div className="mb-3">
          <label htmlFor="username" className="form-label">Username</label>
          <input
            type="text"
            id="username"
            className="form-control"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        {/* Password Input */}
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Password</label>
          <input
            type="password"
            id="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {/* Confirm Password Input */}
        <div className="mb-3">
          <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            className="form-control"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>

        {/* Register Button */}
        <button type="submit" className="btn bg-blue-dark text-white w-100"
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2C5E97')}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3980D0')}
        >
          Register
        </button>
      </form>

      {/* Link to Login Page */}
      <p className="mt-3 text-center">
        Already have an account?{" "}
        <button
          onClick={() => navigate("/login")}
          className="btn btn-link p-0 align-baseline text-blue"
        >
          Login here
        </button>
      </p>
    </div>
  );
}

export default RegisterPage;