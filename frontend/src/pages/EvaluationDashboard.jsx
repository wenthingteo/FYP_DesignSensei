import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import API_BASE from "../config";
import { getAccessToken } from "../utils/auth";
import "./EvaluationDashboard.css";

function EvaluationDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [performanceReport, setPerformanceReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const token = getAccessToken();
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch both dashboard and performance report
      const [dashboardRes, reportRes] = await Promise.all([
        axios.get(`${API_BASE}/api/evaluation/dashboard/`, { headers }),
        axios.get(`${API_BASE}/api/evaluation/performance-report/`, {
          headers,
        }),
      ]);

      setDashboardData(dashboardRes.data);
      setPerformanceReport(reportRes.data);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching evaluation data:", err);
      if (err.response?.status === 401) {
        setError("Not authenticated. Please login.");
        setTimeout(() => navigate("/login"), 2000);
      } else if (err.response?.status === 403) {
        setError("Access denied. Admin privileges required.");
      } else {
        setError("Failed to load evaluation data.");
      }
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return "N/A";
    return `${(value * 100).toFixed(1)}%`;
  };

  const getStatusBadge = (met) => {
    return met ? (
      <span className="status-badge status-met">✅ MET</span>
    ) : (
      <span className="status-badge status-not-met">⚠️ NOT MET</span>
    );
  };

  const getModeColor = (mode) => {
    switch (mode) {
      case "GRAPH_RAG":
        return "#10b981";
      case "LLM_ONLY":
        return "#f59e0b";
      case "HYBRID_BLEND":
        return "#8b5cf6";
      default:
        return "#6b7280";
    }
  };

  if (loading) {
    return (
      <div className="evaluation-dashboard">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading evaluation metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="evaluation-dashboard">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate("/login")} className="back-button">
          Go Back to Login
        </button>
      </div>
    );
  }

  return (
    <div className="evaluation-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>📊 Evaluation Dashboard</h1>
          <p className="header-subtitle">
            GraphRAG Chatbot Performance Metrics
          </p>
        </div>
        <div className="header-actions">
          <button
            onClick={() => navigate("/admin/feedback")}
            className="nav-button"
          >
            User Feedback
          </button>
          <button onClick={() => navigate("/chatbot")} className="back-button">
            Back to Chatbot
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={`tab-button ${activeTab === "metrics" ? "active" : ""}`}
          onClick={() => setActiveTab("metrics")}
        >
          Quality Metrics
        </button>
        <button
          className={`tab-button ${activeTab === "timeline" ? "active" : ""}`}
          onClick={() => setActiveTab("timeline")}
        >
          Timeline
        </button>
        <button
          className={`tab-button ${activeTab === "flagged" ? "active" : ""}`}
          onClick={() => setActiveTab("flagged")}
        >
          Flagged Queries
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && performanceReport && (
        <div className="tab-content">
          {/* FYP Objective Status */}
          <div className="objective-card">
            <h2>🎯 FYP Objective Status</h2>
            <p className="objective-text">{performanceReport.fyp_objective}</p>
            <div
              className={`conclusion-badge ${
                performanceReport.conclusion.includes("ACHIEVED")
                  ? "achieved"
                  : "pending"
              }`}
            >
              {performanceReport.conclusion}
            </div>
          </div>

          {/* Success Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-icon">🎯</span>
                <span className="metric-title">Accuracy</span>
              </div>
              <div className="metric-value">
                {formatPercentage(
                  performanceReport.success_metrics.accuracy_achieved
                )}
              </div>
              <div className="metric-target">
                Target:{" "}
                {formatPercentage(
                  performanceReport.success_metrics.accuracy_target
                )}
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill accuracy"
                  style={{
                    width: `${
                      (performanceReport.success_metrics.accuracy_achieved ||
                        0) * 100
                    }%`,
                  }}
                />
              </div>
              {getStatusBadge(performanceReport.success_metrics.accuracy_met)}
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-icon">📚</span>
                <span className="metric-title">Completeness</span>
              </div>
              <div className="metric-value">
                {formatPercentage(
                  performanceReport.success_metrics.completeness_achieved
                )}
              </div>
              <div className="metric-target">
                Target:{" "}
                {formatPercentage(
                  performanceReport.success_metrics.completeness_target
                )}
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill completeness"
                  style={{
                    width: `${
                      (performanceReport.success_metrics
                        .completeness_achieved || 0) * 100
                    }%`,
                  }}
                />
              </div>
              {getStatusBadge(
                performanceReport.success_metrics.completeness_met
              )}
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-icon">🎓</span>
                <span className="metric-title">Educational Value</span>
              </div>
              <div className="metric-value">
                {formatPercentage(
                  performanceReport.success_metrics.educational_value_achieved
                )}
              </div>
              <div className="metric-target">
                Target:{" "}
                {formatPercentage(
                  performanceReport.success_metrics.educational_value_target
                )}
              </div>
              <div className="metric-bar">
                <div
                  className="metric-fill educational"
                  style={{
                    width: `${
                      (performanceReport.success_metrics
                        .educational_value_achieved || 0) * 100
                    }%`,
                  }}
                />
              </div>
              {getStatusBadge(
                performanceReport.success_metrics.educational_value_met
              )}
            </div>

            <div className="metric-card highlight">
              <div className="metric-header">
                <span className="metric-icon">📈</span>
                <span className="metric-title">GraphRAG Improvement</span>
              </div>
              <div className="metric-value improvement">
                +{performanceReport.success_metrics.improvement_percentage || 0}
                %
              </div>
              <div className="metric-target">vs LLM-Only mode</div>
              {getStatusBadge(
                performanceReport.success_metrics.graph_rag_better_than_llm
              )}
            </div>
          </div>

          {/* Mode Distribution */}
          {dashboardData && (
            <div className="distribution-section">
              <h3>📊 Query Distribution by Mode</h3>
              <div className="mode-bars">
                {dashboardData.mode_distribution.map((item) => {
                  const total = dashboardData.mode_distribution.reduce(
                    (sum, m) => sum + m.count,
                    0
                  );
                  const percentage =
                    total > 0 ? ((item.count / total) * 100).toFixed(1) : 0;
                  return (
                    <div key={item.mode} className="mode-bar-item">
                      <div className="mode-label">
                        <span
                          className="mode-dot"
                          style={{ background: getModeColor(item.mode) }}
                        ></span>
                        {item.mode.replace("_", " ")}
                      </div>
                      <div className="mode-bar-container">
                        <div
                          className="mode-bar-fill"
                          style={{
                            width: `${percentage}%`,
                            background: getModeColor(item.mode),
                          }}
                        />
                      </div>
                      <div className="mode-count">
                        {item.count} ({percentage}%)
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {performanceReport.recommendations &&
            performanceReport.recommendations.length > 0 && (
              <div className="recommendations-section">
                <h3>💡 Recommendations</h3>
                <ul className="recommendations-list">
                  {performanceReport.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      )}

      {/* Quality Metrics Tab */}
      {activeTab === "metrics" && dashboardData && (
        <div className="tab-content">
          <h3>📈 Accuracy by Mode</h3>
          <div className="accuracy-comparison">
            {dashboardData.accuracy_by_mode.map((item) => (
              <div key={item.mode} className="accuracy-card">
                <div
                  className="accuracy-mode"
                  style={{ color: getModeColor(item.mode) }}
                >
                  {item.mode.replace("_", " ")}
                </div>
                <div className="accuracy-value">
                  {formatPercentage(item.accuracy)}
                </div>
                <div className="accuracy-bar">
                  <div
                    className="accuracy-bar-fill"
                    style={{
                      width: `${(item.accuracy || 0) * 100}%`,
                      background: getModeColor(item.mode),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <h3>📚 Ground Truth Coverage</h3>
          <div className="ground-truth-stats">
            <div className="gt-stat">
              <div className="gt-value">
                {dashboardData.ground_truth_coverage.total_ground_truths}
              </div>
              <div className="gt-label">Total Ground Truths</div>
            </div>
            <div className="gt-stat">
              <div className="gt-value">
                {
                  dashboardData.ground_truth_coverage
                    .evaluations_with_ground_truth
                }
              </div>
              <div className="gt-label">Matched Evaluations</div>
            </div>
            <div className="gt-stat">
              <div className="gt-value">
                {dashboardData.ground_truth_coverage.avg_similarity
                  ? formatPercentage(
                      dashboardData.ground_truth_coverage.avg_similarity
                    )
                  : "N/A"}
              </div>
              <div className="gt-label">Avg Similarity</div>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === "timeline" && dashboardData && (
        <div className="tab-content">
          <h3>📅 Recent Evaluations (Last 30)</h3>
          <div className="timeline-table-container">
            <table className="timeline-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Mode</th>
                  <th>Accuracy</th>
                  <th>Completeness</th>
                  <th>Educational Value</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.quality_timeline.map((item) => (
                  <tr key={item.id}>
                    <td>#{item.id}</td>
                    <td>
                      <span
                        className="mode-badge"
                        style={{ background: getModeColor(item.mode) }}
                      >
                        {item.mode.replace("_", " ")}
                      </span>
                    </td>
                    <td
                      className={
                        item.accuracy >= 0.7 ? "score-good" : "score-low"
                      }
                    >
                      {formatPercentage(item.accuracy)}
                    </td>
                    <td
                      className={
                        item.completeness >= 0.75 ? "score-good" : "score-low"
                      }
                    >
                      {formatPercentage(item.completeness)}
                    </td>
                    <td
                      className={
                        item.educational_value >= 0.8
                          ? "score-good"
                          : "score-low"
                      }
                    >
                      {formatPercentage(item.educational_value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Flagged Queries Tab */}
      {activeTab === "flagged" && dashboardData && (
        <div className="tab-content">
          <h3>🚨 Quality Assurance</h3>
          <div className="flagged-summary">
            <div className="flagged-card passed">
              <div className="flagged-icon">✅</div>
              <div className="flagged-value">
                {dashboardData.flagged_summary.passed}
              </div>
              <div className="flagged-label">Passed</div>
            </div>
            <div className="flagged-card flagged">
              <div className="flagged-icon">🚨</div>
              <div className="flagged-value">
                {dashboardData.flagged_summary.flagged}
              </div>
              <div className="flagged-label">Flagged for Review</div>
            </div>
            <div className="flagged-card total">
              <div className="flagged-icon">📊</div>
              <div className="flagged-value">
                {dashboardData.flagged_summary.total}
              </div>
              <div className="flagged-label">Total Evaluations</div>
            </div>
          </div>

          {dashboardData.flagged_summary.flagged === 0 ? (
            <div className="no-flagged-message">
              <span className="success-icon">🎉</span>
              <p>
                No queries have been flagged for review. The chatbot is
                performing well!
              </p>
            </div>
          ) : (
            <div className="flagged-alert">
              <p>
                ⚠️ {dashboardData.flagged_summary.flagged} queries need human
                review.
              </p>
              <p>
                These responses scored below 60% accuracy and may contain
                errors.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EvaluationDashboard;
