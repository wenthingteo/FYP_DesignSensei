import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { ChatContext } from "../context/ChatContext";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
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

  return (
    <div className="container mt-5" style={{ maxWidth: "400px" }}>
      <h2 className="mb-4 text-center">Login</h2>
      {errorMsg && <div className="alert alert-danger">{errorMsg}</div>}
      <form onSubmit={handleLogin}>
        <div className="mb-3">
          <label className="form-label">Username</label>
          <input
            type="text"
            className="form-control"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="mb-3">
          <label className="form-label">Password</label>
          <input
            type="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn bg-blue-dark text-white w-100"
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#2C5E97')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#3980D0')}
        >
          Login
        </button>
      </form>
      {/* Link to Register Page */}
      <p className="mt-3 text-center">
        Don't have an account?{" "}
        <button
          onClick={() => navigate("/register")}
          className="btn btn-link p-0 align-baseline text-blue"
        >
          Register here
        </button>
      </p>
    </div>
  );
}

export default LoginPage;
