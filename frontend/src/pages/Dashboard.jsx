import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDashboard, getSkillProfile } from '../api/dashboard';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';
import { getSkillIcon } from '../components/RealisticIcons';

const SKILL_DIMENSIONS = [
  {
    key: 'problem_solving',
    name: 'Problem Solving',
    description: 'Functional correctness & algorithm logic',
    color: '#1D4ED8',
    badgeClass: 'badge-API',
  },
  {
    key: 'debugging',
    name: 'Debugging',
    description: 'Fault localization & bug fix accuracy',
    color: '#DC2626',
    badgeClass: 'badge-BUG_FIX',
  },
  {
    key: 'security',
    name: 'Security',
    description: 'Vulnerability prevention & authorization',
    color: '#6D28D9',
    badgeClass: 'badge-SECURITY',
  },
  {
    key: 'performance',
    name: 'Performance',
    description: 'Execution speed & memory efficiency',
    color: '#047857',
    badgeClass: 'badge-PERFORMANCE',
  },
  {
    key: 'code_quality',
    name: 'Code Quality',
    description: 'Maintainability & structure',
    color: '#D97706',
    badgeClass: 'badge-CODE_QUALITY',
  },
  {
    key: 'testing',
    name: 'Testing',
    description: 'Suite completeness & validation',
    color: '#0E7490',
    badgeClass: 'badge-TESTING',
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
    if (score >= 80) return 'var(--pastel-mint-text)';
    if (score >= 50) return 'var(--pastel-peach-text)';
    return 'var(--accent-danger)';
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
        <div style={{ background: 'var(--accent-danger-light)', border: '1px solid var(--accent-danger-border)', color: 'var(--accent-danger)', borderRadius: 'var(--radius-md)', padding: '1.25rem', margin: '2rem 0' }}>
          <p>{error || 'Failed to load dashboard data.'}</p>
        </div>
      </div>
    );
  }

  const { overview, recent_submissions } = data;
  const isBrandNew = overview.total_submissions === 0;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1200px' }}>
      {/* 1. Top Welcome Banner in Light Pastel Framing */}
      <div
        className="card panel-pastel-lavender animate-fade-in-up"
        style={{
          padding: '2.5rem',
          marginBottom: '2.5rem',
          borderRadius: '24px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
              <h1 className="page-title" style={{ margin: 0, fontSize: '2.1rem' }}>
                Welcome back, {user?.username}
              </h1>
              <span className="badge badge-API" style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem', fontWeight: 700 }}>
                ACTIVE DEVELOPER
              </span>
            </div>
            <p className="page-description" style={{ margin: 0, maxWidth: '640px' }}>
              Practice software engineering on real multi-file codebases, patch structural defects, and verify your skills in isolated Docker sandboxes.
            </p>
          </div>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.85rem 1.85rem', fontSize: '0.96rem' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      </div>

      {isBrandNew ? (
        <div className="card panel-pastel-blue animate-scale-in" style={{ padding: '4.5rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <div style={{ width: 56, height: 56, margin: '0 auto 1.25rem', background: '#ffffff', border: '1px solid var(--pastel-blue-border)', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--pastel-blue-text)', fontSize: '1.5rem', fontFamily: 'var(--font-mono)', fontWeight: 800, boxShadow: 'var(--shadow-sm)' }}>
            &gt;_
          </div>
          <h3 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Welcome to CodeFoundry
          </h3>
          <p style={{ maxWidth: '520px', margin: '0 auto 1.75rem', color: 'var(--text-secondary)', fontSize: '0.98rem', lineHeight: 1.6 }}>
            You haven&apos;t attempted any challenges yet. Pick your first engineering scenario to begin practicing in isolated Docker sandboxes.
          </p>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.85rem 2.2rem' }}>
            <span>Start Your First Challenge</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
          {/* 2. Top Metric Tiles with Alternating Pastel Accents */}
          <div className="gency-stats-grid" style={{ marginTop: 0 }}>
            {/* Tile 1: Attempted */}
            <div className="card panel-pastel-blue animate-fade-in-up stagger-1" style={{ padding: '1.75rem 2rem', borderRadius: '20px' }}>
              <span className="gency-stat-label" style={{ color: 'var(--pastel-blue-text)' }}>Challenges Attempted</span>
              <span className="gency-stat-number" style={{ color: 'var(--pastel-blue-text)', marginTop: '0.4rem' }}>
                <AnimatedCounter value={overview.challenges_attempted} duration={800} />
              </span>
            </div>

            {/* Tile 2: Passed */}
            <div className="card panel-pastel-mint animate-fade-in-up stagger-2" style={{ padding: '1.75rem 2rem', borderRadius: '20px' }}>
              <span className="gency-stat-label" style={{ color: 'var(--pastel-mint-text)' }}>Challenges Passed</span>
              <span className="gency-stat-number" style={{ color: 'var(--pastel-mint-text)', marginTop: '0.4rem' }}>
                <AnimatedCounter value={overview.challenges_passed} duration={800} />
              </span>
            </div>

            {/* Tile 3: Total Submissions */}
            <div className="card panel-pastel-lavender animate-fade-in-up stagger-3" style={{ padding: '1.75rem 2rem', borderRadius: '20px' }}>
              <span className="gency-stat-label" style={{ color: 'var(--pastel-lavender-text)' }}>Total Submissions</span>
              <span className="gency-stat-number" style={{ color: 'var(--pastel-lavender-text)', marginTop: '0.4rem' }}>
                <AnimatedCounter value={overview.total_submissions} duration={800} />
              </span>
            </div>

            {/* Tile 4: Overall Score */}
            <div className="card panel-pastel-peach animate-fade-in-up stagger-4" style={{ padding: '1.75rem 2rem', borderRadius: '20px' }}>
              <span className="gency-stat-label" style={{ color: 'var(--pastel-peach-text)' }}>Overall Skill Score</span>
              <div className="gency-stat-number" style={{ marginTop: '0.4rem', color: skillProfile?.overall_score != null ? getScoreColor(skillProfile.overall_score) : 'var(--text-muted)' }}>
                {skillProfile?.overall_score != null ? (
                  <>
                    <AnimatedCounter value={skillProfile.overall_score} duration={1000} />{' '}
                    <span style={{ fontSize: '1.1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>/ 100</span>
                  </>
                ) : (
                  <span style={{ fontSize: '1.15rem', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>Pending</span>
                )}
              </div>
            </div>
          </div>

          {/* 3. Skill Profile & Competencies Breakdown */}
          <div className="card animate-fade-in-up stagger-3" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '2rem' }}>
              <div>
                <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                  Skill Profile &amp; Competencies
                </h2>
                <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  Deterministic competency evaluations derived from your best challenge submissions.
                </p>
              </div>
              {skillProfile?.total_evaluations_analyzed !== undefined && (
                <span className="user-pill" style={{ padding: '0.4rem 1rem' }}>
                  Evaluations Analyzed: <strong>{skillProfile.total_evaluations_analyzed}</strong>
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: '1.35rem' }}>
              {SKILL_DIMENSIONS.map((dim, idx) => {
                const skillData = skillProfile?.skills?.[dim.key] || {
                  score: null,
                  sample_size: 0,
                  status: 'insufficient_data',
                };
                const isMeasured = skillData.status === 'measured' && skillData.score !== null;
                const isNotMeasured = skillData.status === 'not_measured';

                return (
                  <div key={dim.key} className={`skill-card animate-fade-in-up stagger-${(idx % 6) + 1}`} style={{ padding: '1.5rem', borderRadius: '18px' }}>
                    <div className="skill-card-top" style={{ marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                          {getSkillIcon(dim.key, 18, dim.color)}
                        </span>
                        <span className="skill-name" style={{ fontSize: '1rem' }}>{dim.name}</span>
                      </div>
                      <span className="skill-score" style={{ color: isMeasured ? getScoreColor(skillData.score) : 'var(--text-muted)' }}>
                        {isMeasured ? (
                          <>
                            <AnimatedCounter value={skillData.score} duration={800} />
                            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500 }}>/100</span>
                          </>
                        ) : isNotMeasured ? (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Reserved</span>
                        ) : (
                          '—'
                        )}
                      </span>
                    </div>

                    <div style={{ marginBottom: '0.85rem' }}>
                      <AnimatedProgress
                        value={isMeasured ? skillData.score : 0}
                        color={dim.color}
                        height={7}
                      />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <span>{dim.description}</span>
                      <span style={{ fontWeight: 600 }}>{skillData.sample_size || 0} evals</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Recent Activity Section */}
          <div className="card animate-fade-in-up stagger-4" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.45rem', fontWeight: 800, margin: 0 }}>
                Recent Submissions
              </h2>
              <Link to="/submissions" style={{ color: 'var(--accent-primary)', fontSize: '0.92rem', fontWeight: 700, textDecoration: 'none' }}>
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
                        <td style={{ fontWeight: 700 }}>
                          {sub.challenge_title || `Challenge #${sub.challenge}`}
                        </td>
                        <td>
                          <span className={`badge ${sub.status === 'PASSED' ? 'badge-passed' : sub.status === 'FAILED' ? 'badge-failed' : 'badge-pending'}`}>
                            {sub.status}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {sub.score !== null ? `${sub.score}/100` : '—'}
                        </td>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.86rem' }}>
                          {formatTimestamp(sub.submitted_at)}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <Link
                            to={`/workspace/${sub.challenge}`}
                            className="btn btn-secondary"
                            style={{ padding: '0.4rem 0.95rem', fontSize: '0.82rem' }}
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
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderRadius: '16px' }}>
                No recent submissions found.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
