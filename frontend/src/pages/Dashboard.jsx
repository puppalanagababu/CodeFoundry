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
    description: 'Maintainability & structure (Reserved)',
    color: '#64748b',
    icon: '📦',
  },
  {
    key: 'testing',
    name: 'Testing',
    description: 'Suite completeness & validation (Reserved)',
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
      <div className="page-container">
        <Loading message="Loading student dashboard & skill profile..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-container">
        <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', color: '#f87171', borderRadius: 'var(--radius-md)', padding: '1.25rem', margin: '2rem 0' }}>
          <p>{error || 'Failed to load dashboard data.'}</p>
        </div>
      </div>
    );
  }

  const { overview, recent_submissions, difficulty_progress } = data;
  const isBrandNew = overview.total_submissions === 0;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1200px' }}>
      {/* Top Welcome Header Framed in Gency Style */}
      <div className="gency-frame animate-fade-in-up" style={{ padding: '2rem 2.5rem', marginBottom: '2.5rem', background: 'linear-gradient(180deg, rgba(24, 34, 54, 0.75) 0%, rgba(14, 20, 32, 0.9) 100%)' }}>
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
          <Link to="/challenges" className="btn-gency btn-gency-primary" style={{ padding: '0.7rem 1.6rem', fontSize: '0.92rem' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">↗</span>
          </Link>
        </div>
      </div>

      {isBrandNew ? (
        <div className="gency-frame animate-scale-in" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, margin: '0 auto 1.25rem', background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-blue)', fontSize: '1.5rem', fontFamily: 'var(--font-mono)' }}>
            &lt;/&gt;
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>
            Welcome to DevForge
          </h3>
          <p style={{ maxWidth: '520px', margin: '0 auto 1.75rem', color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
            You haven't attempted any challenges yet. Pick your first engineering scenario to start practicing in the Docker sandbox.
          </p>
          <Link to="/challenges" className="btn-gency btn-gency-primary" style={{ padding: '0.75rem 1.85rem' }}>
            <span>Start Your First Challenge</span>
            <span className="btn-arrow-icon">↗</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
          {/* 1. Overview Metric Cards Grid with Animated Counters */}
          <div className="gency-stats-grid" style={{ marginTop: 0 }}>
            <div className="gency-stat-tile animate-fade-in-up stagger-1">
              <span className="gency-stat-label">Challenges Attempted</span>
              <span className="gency-stat-number">
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
              <span className="gency-stat-number">
                <AnimatedCounter value={overview.total_submissions} duration={800} />
              </span>
            </div>

            <div className="gency-stat-tile animate-fade-in-up stagger-4">
              <span className="gency-stat-label">Overall Skill Score</span>
              <div className="gency-stat-number" style={{ color: skillProfile?.overall_score != null ? getScoreColor(skillProfile.overall_score) : 'var(--text-muted)' }}>
                {skillProfile?.overall_score != null ? (
                  <>
                    <AnimatedCounter value={skillProfile.overall_score} duration={1000} />{' '}
                    <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 500 }}>/ 100</span>
                  </>
                ) : (
                  <span style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>Pending</span>
                )}
              </div>
            </div>
          </div>

          {/* 2. Skill Profile & Competencies Grid */}
          <div className="gency-frame animate-fade-in-up stagger-3" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.75rem' }}>
              <div>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 600, color: '#fff', margin: 0 }}>
                  Skill Profile &amp; Competencies
                </h2>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Deterministic competency evaluations derived from your best challenge submissions.
                </p>
              </div>
              {skillProfile?.total_evaluations_analyzed !== undefined && (
                <span className="user-pill" style={{ borderRadius: 'var(--radius-full)', padding: '0.35rem 0.9rem' }}>
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
                  <div key={dim.key} className={`skill-card gency-frame animate-fade-in-up stagger-${(idx % 6) + 1}`} style={{ padding: '1.25rem' }}>
                    <div className="skill-card-top">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.1rem' }}>{dim.icon}</span>
                        <span className="skill-name" style={{ fontFamily: 'var(--font-display)', fontSize: '1rem' }}>{dim.name}</span>
                      </div>
                      <span className="skill-score" style={{ color: isMeasured ? getScoreColor(skillData.score) : 'var(--text-muted)' }}>
                        {isMeasured ? (
                          <>
                            <AnimatedCounter value={skillData.score} duration={800} />/100
                          </>
                        ) : isNotMeasured ? (
                          'Reserved'
                        ) : (
                          'Need Data'
                        )}
                      </span>
                    </div>

                    <AnimatedProgress
                      value={isMeasured ? skillData.score : 0}
                      max={100}
                      height={8}
                      color={dim.color}
                    />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                      <span>{dim.description}</span>
                      {skillData.sample_size > 0 && (
                        <span>
                          {skillData.sample_size} attempt{skillData.sample_size > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 3. Challenge Progress Breakdown */}
          {difficulty_progress && difficulty_progress.length > 0 && (
            <div className="gency-frame animate-fade-in-up stagger-4" style={{ padding: '2rem' }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.35rem', fontWeight: 600, color: '#fff', marginBottom: '1.25rem' }}>
                Challenge Progress by Difficulty
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
                {difficulty_progress.map((dp, idx) => {
                  const percent = dp.total > 0 ? Math.round((dp.passed / dp.total) * 100) : 0;
                  return (
                    <div key={dp.difficulty} className={`gency-stat-tile animate-fade-in-up stagger-${idx + 1}`} style={{ padding: '1.25rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: '0.6rem' }}>
                        <span className={`badge badge-${dp.difficulty}`}>{dp.difficulty}</span>
                        <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff' }}>
                          <AnimatedCounter value={dp.passed} duration={700} /> / {dp.total}
                        </span>
                      </div>
                      <AnimatedProgress
                        value={percent}
                        max={100}
                        height={7}
                        color={dp.difficulty === 'BEGINNER' ? '#10b981' : dp.difficulty === 'INTERMEDIATE' ? '#f59e0b' : '#ef4444'}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 4. Recent Activity Feed */}
          {recent_submissions && recent_submissions.length > 0 && (
            <div className="gency-frame animate-fade-in-up stagger-5" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.35rem', fontWeight: 600, color: '#fff', margin: 0 }}>
                  Recent Submissions
                </h2>
                <Link to="/submissions" style={{ fontSize: '0.88rem', color: 'var(--accent-blue)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span>View All</span>
                  <span className="btn-arrow-icon">↗</span>
                </Link>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {recent_submissions.slice(0, 5).map((sub, idx) => (
                  <div
                    key={sub.id}
                    className={`gency-stat-tile animate-fade-in-up stagger-${idx + 1}`}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '1rem 1.5rem',
                      flexWrap: 'wrap',
                      gap: '1rem',
                    }}
                  >
                    <div>
                      <Link
                        to={`/challenges/${sub.challenge_id || sub.challenge?.id}`}
                        style={{ fontWeight: 600, color: '#fff', fontSize: '1rem' }}
                      >
                        {sub.challenge_title || sub.challenge?.title || `Challenge #${sub.challenge}`}
                      </Link>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        {formatTimestamp(sub.submitted_at)}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span className={`status-pill ${sub.status === 'PASSED' ? 'status-passed' : sub.status === 'FAILED' ? 'status-failed' : 'status-pending'}`}>
                        <span className="status-dot" />
                        <span>{sub.status}</span>
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1rem', color: getScoreColor(sub.score || 0) }}>
                        <AnimatedCounter value={sub.score || 0} duration={600} />/100
                      </span>
                      <Link
                        to={`/workspace/${sub.challenge_id || sub.challenge?.id}`}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.9rem', fontSize: '0.82rem', borderRadius: 'var(--radius-full)' }}
                      >
                        Open Workspace
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
