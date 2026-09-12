import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDashboard, getSkillProfile } from '../api/dashboard';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';

const SKILL_DIMENSIONS = [
  {
    key: 'problem_solving',
    name: 'Problem Solving',
    description: 'Functional correctness & algorithm logic',
    color: '#3b82f6',
    icon: '⚡',
  },
  {
    key: 'debugging',
    name: 'Debugging',
    description: 'Fault localization & bug fix accuracy',
    color: '#f59e0b',
    icon: '🐛',
  },
  {
    key: 'security',
    name: 'Security',
    description: 'Vulnerability prevention & authorization',
    color: '#8b5cf6',
    icon: '🛡️',
  },
  {
    key: 'performance',
    name: 'Performance',
    description: 'Execution speed & memory efficiency',
    color: '#10b981',
    icon: '🚀',
  },
  {
    key: 'code_quality',
    name: 'Code Quality',
    description: 'Maintainability & structure',
    color: '#64748b',
    icon: '📦',
  },
  {
    key: 'testing',
    name: 'Testing',
    description: 'Suite completeness & validation',
    color: '#06b6d4',
    icon: '🧪',
  },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [skillProfile, setSkillProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getDashboard(),
      getSkillProfile().catch(() => null),
    ])
      .then(([dashboardRes, skillRes]) => {
        if (!isMounted) return;
        setData(dashboardRes);
        setSkillProfile(skillRes);
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

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return (
      <div className="page-container" style={{ padding: '4rem 1.5rem' }}>
        <Loading message="Loading student dashboard & skill profile..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-container">
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 'var(--radius-md)', padding: '1.25rem', margin: '2rem 0' }}>
          <p>{error || 'Failed to load dashboard data.'}</p>
        </div>
      </div>
    );
  }

  const { overview, recent_submissions } = data;
  const isBrandNew = overview.total_submissions === 0;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1200px' }}>
      {/* Top Welcome Header Framed in Modern SaaS Style */}
      <div
        className="card animate-fade-in-up"
        style={{
          padding: '2.25rem 2.5rem',
          marginBottom: '2.5rem',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)',
          borderRadius: '24px',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <h1 className="page-title" style={{ margin: 0, fontSize: '2rem' }}>
                Welcome back, {user?.username}
              </h1>
              <span style={{ fontSize: '1.4rem' }}>👋</span>
            </div>
            <p className="page-description" style={{ margin: 0 }}>
              Build verified software engineering competencies across realistic repositories, bug fixes, and sandbox test suites.
            </p>
          </div>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '0.94rem' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      </div>

      {isBrandNew ? (
        <div className="card animate-scale-in" style={{ padding: '4.5rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <div style={{ width: 56, height: 56, margin: '0 auto 1.25rem', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)', fontSize: '1.5rem', fontFamily: 'var(--font-mono)' }}>
            &gt;_
          </div>
          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Welcome to CodeFoundry
          </h3>
          <p style={{ maxWidth: '520px', margin: '0 auto 1.75rem', color: 'var(--text-secondary)', fontSize: '0.96rem', lineHeight: 1.6 }}>
            You haven&apos;t attempted any challenges yet. Pick your first engineering scenario to start practicing in the Docker sandbox.
          </p>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.8rem 2rem' }}>
            <span>Start Your First Challenge</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
          {/* 1. Overview Metric Cards Grid */}
          <div className="gency-stats-grid" style={{ marginTop: 0 }}>
            <div className="gency-stat-tile animate-fade-in-up stagger-1">
              <span className="gency-stat-label">Challenges Attempted</span>
              <span className="gency-stat-number" style={{ color: '#2563eb' }}>
                <AnimatedCounter value={overview.challenges_attempted} duration={800} />
              </span>
            </div>

            <div className="gency-stat-tile animate-fade-in-up stagger-2">
              <span className="gency-stat-label">Challenges Passed</span>
              <span className="gency-stat-number" style={{ color: '#10b981' }}>
                <AnimatedCounter value={overview.challenges_passed} duration={800} />
              </span>
            </div>

            <div className="gency-stat-tile animate-fade-in-up stagger-3">
              <span className="gency-stat-label">Total Submissions</span>
              <span className="gency-stat-number" style={{ color: '#8b5cf6' }}>
                <AnimatedCounter value={overview.total_submissions} duration={800} />
              </span>
            </div>

            <div className="gency-stat-tile animate-fade-in-up stagger-4">
              <span className="gency-stat-label">Overall Skill Score</span>
              <div className="gency-stat-number" style={{ color: skillProfile?.overall_score != null ? getScoreColor(skillProfile.overall_score) : 'var(--text-muted)' }}>
                {skillProfile?.overall_score != null ? (
                  <>
                    <AnimatedCounter value={skillProfile.overall_score} duration={1000} />{' '}
                    <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>/ 100</span>
                  </>
                ) : (
                  <span style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>Pending</span>
                )}
              </div>
            </div>
          </div>

          {/* 2. Skill Profile & Competencies Grid */}
          <div className="card animate-fade-in-up stagger-3" style={{ padding: '2rem 2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.75rem' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                  Skill Profile &amp; Competencies
                </h2>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Deterministic competency evaluations derived from your best challenge submissions.
                </p>
              </div>
              {skillProfile?.total_evaluations_analyzed !== undefined && (
                <span className="user-pill" style={{ padding: '0.35rem 0.95rem' }}>
                  Evaluations Analyzed: <strong>{skillProfile.total_evaluations_analyzed}</strong>
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
              {SKILL_DIMENSIONS.map((dim, idx) => {
                const skillData = skillProfile?.skills?.[dim.key] || {
                  score: null,
                  sample_size: 0,
                  status: 'insufficient_data',
                };
                const isMeasured = skillData.status === 'measured' && skillData.score !== null;
                const isNotMeasured = skillData.status === 'not_measured';

                return (
                  <div key={dim.key} className={`skill-card animate-fade-in-up stagger-${(idx % 6) + 1}`} style={{ padding: '1.35rem' }}>
                    <div className="skill-card-top">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.1rem' }}>{dim.icon}</span>
                        <span className="skill-name" style={{ fontSize: '0.98rem' }}>{dim.name}</span>
                      </div>
                      <span className="skill-score" style={{ color: isMeasured ? getScoreColor(skillData.score) : 'var(--text-muted)' }}>
                        {isMeasured ? (
                          <>
                            <AnimatedCounter value={skillData.score} duration={800} />/100
                          </>
                        ) : isNotMeasured ? (
                          'Reserved'
                        ) : (
                          '—'
                        )}
                      </span>
                    </div>

                    <div style={{ marginBottom: '0.75rem' }}>
                      <AnimatedProgress
                        value={isMeasured ? skillData.score : 0}
                        color={dim.color}
                        height={6}
                      />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      <span>{dim.description}</span>
                      <span>{skillData.sample_size || 0} evals</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 3. Recent Activity Section */}
          <div className="card animate-fade-in-up stagger-4" style={{ padding: '2rem 2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>
                Recent Submissions
              </h2>
              <Link to="/submissions" style={{ color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 600, textDecoration: 'none' }}>
                View All Submissions →
              </Link>
            </div>

            {recent_submissions && recent_submissions.length > 0 ? (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Challenge</th>
                      <th>Status</th>
                      <th>Score</th>
                      <th>Date</th>
                      <th style={{ textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent_submissions.map((sub) => (
                      <tr key={sub.id}>
                        <td style={{ fontWeight: 600 }}>
                          {sub.challenge_title || `Challenge #${sub.challenge}`}
                        </td>
                        <td>
                          <span className={`badge ${sub.status === 'PASSED' ? 'badge-passed' : sub.status === 'FAILED' ? 'badge-failed' : 'badge-pending'}`}>
                            {sub.status}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                          {sub.score !== null ? `${sub.score}/100` : '—'}
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                          {formatTimestamp(sub.created_at)}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <Link
                            to={`/workspace/${sub.challenge}`}
                            className="btn btn-secondary"
                            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
                          >
                            Open Workspace →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
                No recent submissions found.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
