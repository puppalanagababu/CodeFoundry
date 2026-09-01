import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDashboard } from '../api/dashboard';
import Loading from '../components/Loading';

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getDashboard()
      .then((res) => {
        if (!isMounted) return;
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load dashboard metrics.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <Loading message="Loading student dashboard metrics..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-container">
        <div className="error-box">
          <p>{error || 'Failed to load dashboard data.'}</p>
        </div>
      </div>
    );
  }

  const { overview, recent_submissions, difficulty_progress } = data;
  const isBrandNew = overview.total_submissions === 0;

  return (
    <div className="page-container">
      {/* Top Welcome Header */}
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">Welcome back, {user?.username}</h1>
          <p className="page-description">
            Track your coding practice, submission metrics, and skill progress across challenges.
          </p>
        </div>
        <div>
          <Link to="/challenges" className="btn btn-primary" style={{ padding: '0.65rem 1.25rem' }}>
            Browse Challenges &rarr;
          </Link>
        </div>
      </div>

      {isBrandNew ? (
        <div className="empty-state" style={{ padding: '3.5rem 2rem' }}>
          <div className="empty-icon">&lt;/&gt;</div>
          <h3>Welcome to CodeFoundry</h3>
          <p style={{ maxWidth: '480px', margin: '0.5rem auto 1.5rem auto' }}>
            You haven&apos;t attempted any challenges yet. Pick a challenge to start practicing in the Docker sandbox.
          </p>
          <Link to="/challenges" className="btn btn-primary">
            Explore Challenges
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* 1. Overview Metric Cards Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1.25rem',
            }}
          >
            <div className="stat-card">
              <div className="stat-label">Challenges Attempted</div>
              <div className="stat-value">{overview.challenges_attempted}</div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Challenges Passed</div>
              <div className="stat-value" style={{ color: '#3fb950' }}>
                {overview.challenges_passed}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Total Submissions</div>
              <div className="stat-value">{overview.total_submissions}</div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Average Score</div>
              <div className="stat-value" style={{ color: '#58a6ff' }}>
                {overview.average_score} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 100</span>
              </div>
            </div>
          </div>

          {/* 2. Engineering Progress by Difficulty */}
          <div className="detail-section" style={{ margin: 0 }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Engineering Progress</h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '1rem',
              }}
            >
              {difficulty_progress.map((item) => (
                <div
                  key={item.difficulty}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className={`badge badge-${item.difficulty}`}>{item.difficulty}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Avg: <strong style={{ color: 'var(--text-primary)' }}>{item.average_score} pts</strong>
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Attempted: {item.attempted}</span>
                    <span style={{ color: item.passed > 0 ? '#3fb950' : 'var(--text-muted)' }}>
                      Passed: {item.passed}
                    </span>
                  </div>

                  {/* Progress track bar */}
                  <div
                    style={{
                      height: '6px',
                      backgroundColor: 'var(--bg-tertiary)',
                      borderRadius: '3px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${item.attempted > 0 ? Math.min(100, (item.passed / item.attempted) * 100) : 0}%`,
                        backgroundColor: '#3fb950',
                        borderRadius: '3px',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3. Recent Activity Section */}
          <div className="detail-section" style={{ margin: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem' }}>Recent Activity</h2>
              <Link to="/submissions" style={{ fontSize: '0.85rem', color: 'var(--accent-blue)' }}>
                View all submissions &rarr;
              </Link>
            </div>

            {recent_submissions.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>No recent submissions.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {recent_submissions.map((sub) => (
                  <div
                    key={sub.id}
                    style={{
                      backgroundColor: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.85rem 1.15rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <Link
                        to={`/challenges/${sub.challenge}`}
                        style={{
                          fontSize: '0.95rem',
                          fontWeight: '600',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {sub.challenge_title || `Challenge #${sub.challenge}`}
                      </Link>
                      <span className={`badge badge-${sub.status}`} style={{ fontSize: '0.7rem' }}>
                        {sub.status}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.85rem' }}>
                      <span
                        style={{
                          fontWeight: '700',
                          color: sub.status === 'PASSED' ? '#3fb950' : 'var(--text-primary)',
                        }}
                      >
                        {sub.score} pts
                      </span>
                      <span style={{ color: 'var(--text-muted)' }}>{sub.language}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{formatTimestamp(sub.submitted_at)}</span>
                      <Link
                        to={`/workspace/${sub.challenge}`}
                        className="btn btn-secondary"
                        style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                      >
                        Workspace
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
