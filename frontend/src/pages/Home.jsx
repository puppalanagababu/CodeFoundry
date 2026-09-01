import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="hero-section">
      <h1 className="hero-title">Practice Real Software Engineering</h1>
      <p className="hero-subtitle">
        Solve realistic bugs, implement features, run sandboxed tests, and receive engineering feedback in an isolated execution environment.
      </p>

      <div className="hero-actions">
        {isAuthenticated ? (
          <Link to="/dashboard" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1.05rem' }}>
            Go to Dashboard &rarr;
          </Link>
        ) : (
          <Link to="/challenges" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1.05rem' }}>
            Start Practicing &rarr;
          </Link>
        )}
      </div>


      <div className="features-grid">
        <div className="feature-card">
          <h3>Real-World Scenarios</h3>
          <p>Tackle bug fixes, security validation, performance bottlenecks, and API integration challenges.</p>
        </div>
        <div className="feature-card">
          <h3>Isolated Docker Sandbox</h3>
          <p>Code executes securely in hardened container environments with strict resource constraints.</p>
        </div>
        <div className="feature-card">
          <h3>Automated Multi-Test Grading</h3>
          <p>Instant evaluation with hidden edge cases, test pass/fail breakdowns, and execution metrics.</p>
        </div>
      </div>
    </div>
  );
}
