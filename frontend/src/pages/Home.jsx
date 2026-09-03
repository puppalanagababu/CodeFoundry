import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedCounter from '../components/motion/AnimatedCounter';

export default function Home() {
  const { isAuthenticated } = useAuth();

  const skills = [
    '🐛 Bug Diagnostics & Root Cause Analysis',
    '⚡ Performance Profiling & Optimization',
    '🛡️ API Security & Input Sanitization',
    '🗄️ Database Indexing & Query Tuning',
    '🧪 Unit & Integration Test Suites',
    '📦 Multi-File Architecture Refactoring',
  ];

  return (
    <div className="page-container" style={{ maxWidth: '1120px', padding: '3rem 1.5rem 5rem' }}>
      {/* Gency Hero Double-Border Frame */}
      <div className="gency-hero-card animate-fade-in-up" style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
        <div className="gency-hero-badge">
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#818cf8', display: 'inline-block', boxShadow: '0 0 8px #818cf8' }} />
          <span>Real-World Engineering Simulation</span>
        </div>

        <h1 className="hero-title animate-fade-in-up stagger-1">
          Practice Software Engineering.<br />
          <span className="accent-gradient">Not Just Syntax Puzzles.</span>
        </h1>

        <p className="hero-subtitle animate-fade-in-up stagger-2" style={{ margin: '0 auto 2.5rem' }}>
          Immerse yourself in production-grade multi-file codebases. Diagnose bugs, secure API endpoints, eliminate performance bottlenecks, and receive deterministic engineering evaluations in a hardened Docker sandbox.
        </p>

        <div className="animate-fade-in-up stagger-3" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="btn-gency btn-gency-primary"
              style={{ padding: '0.85rem 2.25rem', fontSize: '1.05rem' }}
            >
              <span>Explore Dashboard</span>
              <span className="btn-arrow-icon">↗</span>
            </Link>
          ) : (
            <>
              <Link
                to="/register"
                className="btn-gency btn-gency-primary"
                style={{ padding: '0.85rem 2.25rem', fontSize: '1.05rem' }}
              >
                <span>Start Practicing Free</span>
                <span className="btn-arrow-icon">↗</span>
              </Link>
              <Link
                to="/login"
                className="btn-gency btn-gency-secondary"
                style={{ padding: '0.85rem 2.1rem', fontSize: '1.05rem' }}
              >
                Sign In
              </Link>
            </>
          )}
        </div>

        {/* Floating Developer IDE Window Mockup */}
        <div className="hero-code-preview animate-scale-in stagger-4">
          <div className="hero-code-header">
            <div className="hero-code-dots">
              <div className="hero-code-dot" style={{ backgroundColor: '#ef4444' }} />
              <div className="hero-code-dot" style={{ backgroundColor: '#f59e0b' }} />
              <div className="hero-code-dot" style={{ backgroundColor: '#10b981' }} />
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              auth_service/session_manager.py — DevForge Sandbox
            </span>
            <span className="status-pill status-passed" style={{ fontSize: '0.68rem', padding: '0.1rem 0.5rem' }}>
              <span className="status-dot" /> Isolated
            </span>
          </div>
          <div className="hero-code-body">
            <div><span style={{ color: '#c084fc' }}>def</span> <span style={{ color: '#60a5fa' }}>validate_bearer_token</span>(auth_header: <span style={{ color: '#38bdf8' }}>str</span>) -&gt; <span style={{ color: '#38bdf8' }}>SessionContext</span>:</div>
            <div style={{ paddingLeft: '1.5rem', color: '#94a3b8' }}># DevForge Hardened Evaluation Sandbox v2.0</div>
            <div style={{ paddingLeft: '1.5rem' }}><span style={{ color: '#c084fc' }}>if not</span> auth_header.<span style={{ color: '#60a5fa' }}>startswith</span>(<span style={{ color: '#34d399' }}>"Bearer "</span>):</div>
            <div style={{ paddingLeft: '3rem' }}><span style={{ color: '#c084fc' }}>raise</span> <span style={{ color: '#f87171' }}>AuthenticationError</span>(<span style={{ color: '#34d399' }}>"Invalid token schema"</span>)</div>
            <div style={{ paddingLeft: '1.5rem' }}><span style={{ color: '#c084fc' }}>return</span> <span style={{ color: '#60a5fa' }}>decode_and_verify_signature</span>(auth_header[<span style={{ color: '#fbbf24' }}>7</span>:])</div>
          </div>
        </div>
      </div>

      {/* Live Animated Metric Counter Banner */}
      <div className="gency-stats-grid animate-fade-in-up stagger-4" style={{ marginBottom: '3.5rem' }}>
        <div className="gency-stat-tile">
          <span className="gency-stat-label">Sandbox Isolation</span>
          <span className="gency-stat-number" style={{ color: '#38bdf8' }}>
            <AnimatedCounter value={100} suffix="%" duration={1000} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Docker Container Sandboxes</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Evaluation Speed</span>
          <span className="gency-stat-number" style={{ color: '#34d399' }}>
            &lt;<AnimatedCounter value={500} suffix="ms" duration={800} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Asynchronous Celery Execution</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Skill Dimensions</span>
          <span className="gency-stat-number" style={{ color: '#a78bfa' }}>
            <AnimatedCounter value={6} duration={700} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Deterministic Profiling</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Code Reliability</span>
          <span className="gency-stat-number" style={{ color: '#fbbf24' }}>
            <AnimatedCounter value={100} suffix="%" duration={1100} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Verified Test Assertions</span>
        </div>
      </div>

      {/* Gency Skill Marquee Ticker */}
      <div className="gency-ticker-container animate-fade-in-up stagger-5" style={{ marginBottom: '4.5rem' }}>
        <div className="gency-ticker-track">
          {skills.concat(skills).map((skill, index) => (
            <div key={index} className="gency-ticker-item">
              {skill}
            </div>
          ))}
        </div>
      </div>

      {/* Gency Feature Grid */}
      <div className="animate-fade-in-up stagger-5" style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2.1rem', color: '#fff', marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          Built for Realistic Engineering Depth
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', maxWidth: '620px', margin: '0 auto' }}>
          Engineered to mirror actual day-to-day software development workflows.
        </p>
      </div>

      <div className="features-grid">
        <div className="feature-card gency-frame animate-fade-in-up stagger-6">
          <div className="feature-icon" style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.3)' }}>
            &lt;/&gt;
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>Multi-File Repositories</h3>
          <p>
            Work with realistic application structures containing models, service layers, helpers, and test suites inside a full Monaco IDE workspace.
          </p>
        </div>

        <div className="feature-card gency-frame animate-fade-in-up stagger-7">
          <div className="feature-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
            &#128737;
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>Hardened Docker Sandbox</h3>
          <p>
            Execute untrusted code in resource-constrained, network-disabled containers with strict CPU, memory, and timeout safeguards.
          </p>
        </div>

        <div className="feature-card gency-frame animate-fade-in-up stagger-8">
          <div className="feature-icon" style={{ background: 'rgba(245, 158, 11, 0.12)', color: '#fbbf24', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
            &#9874;
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>Deterministic Skill Profiling</h3>
          <p>
            Evaluate your engineering depth across Problem Solving, Debugging, Security, and Performance with transparent test breakdowns.
          </p>
        </div>
      </div>
    </div>
  );
}
