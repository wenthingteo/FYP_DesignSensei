import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API_BASE from "../config";
import { getAccessToken, clearTokens } from "../utils/auth";
import "./AdminDashboard.css";

function AdminDashboard() {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFeedbacks();
  }, []);

  const fetchFeedbacks = async () => {
    try {
      const token = getAccessToken();
      const response = await axios.get(`${API_BASE}/api/admin/feedback/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data.success) {
        setFeedbacks(response.data.feedbacks);
        setIsAdmin(true);
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching feedbacks:", err);

      if (err.response?.status === 403) {
        setError("Access denied. Admin privileges required.");
        setIsAdmin(false);
      } else if (err.response?.status === 401) {
        setError("Not authenticated. Please login.");
        setTimeout(() => navigate("/login"), 2000);
      } else {
        setError("Failed to load feedback submissions.");
      }
      setLoading(false);
    }
  };

  const handleDelete = async (feedbackId) => {
    if (!window.confirm("Are you sure you want to delete this feedback?")) {
      return;
    }

    try {
      const token = getAccessToken();
      await axios.delete(`${API_BASE}/api/admin/feedback/${feedbackId}/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // Remove from local state
      setFeedbacks(feedbacks.filter((fb) => fb.id !== feedbackId));
      alert("Feedback deleted successfully!");
    } catch (err) {
      console.error("Error deleting feedback:", err);
      if (err.response?.status === 403) {
        alert("Access denied. Admin privileges required.");
      } else if (err.response?.status === 404) {
        alert("Feedback not found.");
      } else {
        alert("Failed to delete feedback. Please try again.");
      }
    }
  };

  const formatDate = (dateString) => {
    // Backend already sends Malaysia time (GMT+8), just format it nicely
    const [datePart, timePart] = dateString.split(" ");
    const [year, month, day] = datePart.split("-");
    const [hour, minute, second] = timePart.split(":");

    const date = new Date(year, month - 1, day, hour, minute, second);

    const monthNames = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    let displayHour = parseInt(hour);
    const ampm = displayHour >= 12 ? "PM" : "AM";
    displayHour = displayHour % 12 || 12;

    return `${day} ${
      monthNames[date.getMonth()]
    } ${year}, ${displayHour}:${minute} ${ampm}`;
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading">Loading feedback submissions...</div>
      </div>
    );
  }

  if (error && !isAdmin) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate("/login")} className="back-button">
          Go Back to Login
        </button>
      </div>
    );
  }

  const exportToCSV = () => {
    // Prepare CSV headers
    const headers = [
      "ID",
      "User",
      "Email",
      "Type",
      "Rating",
      "Comment",
      "Submitted At",
    ];

    // Prepare CSV rows
    const rows = feedbacks.map((fb) => [
      fb.id,
      fb.user,
      fb.email,
      fb.feedback_type,
      fb.rating,
      `"${fb.comment.replace(/"/g, '""')}"`, // Escape quotes in comment
      fb.created_at,
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    // Create blob and download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `feedback_export_${new Date().toISOString().split("T")[0]}.csv`
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Admin Dashboard - User Feedback</h1>
        <div>
          <button
            onClick={() => navigate("/admin/evaluation")}
            className="evaluation-button"
            style={{ marginRight: "10px" }}
          >
            📊 Evaluation Dashboard
          </button>
          <button
            onClick={exportToCSV}
            className="export-button"
            style={{ marginRight: "10px" }}
          >
            Export to CSV
          </button>
          <button onClick={() => navigate("/login")} className="back-button">
            Back to Home
          </button>
        </div>
      </div>

      <div className="feedback-stats">
        <div className="stat-card">
          <div className="stat-number">{feedbacks.length}</div>
          <div className="stat-label">Total Submissions</div>
        </div>
      </div>

      {feedbacks.length === 0 ? (
        <div className="no-feedback">
          <p>No feedback submissions yet.</p>
        </div>
      ) : (
        <div className="feedback-table-container">
          <table className="feedback-table">
            <thead>
              <tr>
                <th>No.</th>
                <th>User</th>
                <th>Email</th>
                <th>Type</th>
                <th>Rating</th>
                <th>Comment</th>
                <th>Submitted At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {feedbacks.map((feedback, index) => (
                <tr key={feedback.id}>
                  <td>{index + 1}</td>
                  <td>{feedback.user}</td>
                  <td>{feedback.email}</td>
                  <td>
                    <span
                      className={`type-badge type-${feedback.feedback_type?.toLowerCase()}`}
                    >
                      {feedback.feedback_type}
                    </span>
                  </td>
                  <td>
                    <div className="rating-container">
                      <span
                        className={`rating-badge rating-${
                          feedback.rating || 0
                        }`}
                      >
                        {feedback.rating || 0}/5
                      </span>
                      <div className="rating-bar">
                        <div
                          className="rating-fill"
                          style={{
                            width: `${((feedback.rating || 0) / 5) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="comment-cell">
                    <div className="comment-content">{feedback.comment}</div>
                  </td>
                  <td className="date-cell">
                    {formatDate(feedback.created_at)}
                  </td>
                  <td>
                    <button
                      onClick={() => handleDelete(feedback.id)}
                      className="delete-button"
                      title="Delete feedback"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
