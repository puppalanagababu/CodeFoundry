import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPublicProfile } from '../api/profile';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';

const SKILL_DIMENSIONS = [
  { key: 'problem_solving', name: 'Problem Solving', icon: '⚡', color: '#3b82f6' },
  { key: 'debugging', name: 'Debugging', icon: '🐛', color: '#f59e0b' },
  { key: 'security', name: 'Security', icon: '🛡️', color: '#8b5cf6' },
  { key: 'performance', name: 'Performance', icon: '🚀', color: '#10b981' },
  { key: 'code_quality', name: 'Code Quality', icon: '📦', color: '#64748b' },
  { key: 'testing', name: 'Testing', icon: '🧪', color: '#06b6d4' },
];

const BADGE_VARIANTS = {
  BUG_SLAYER: { border: '#fde68a', text: '#d97706', bg: '#fffbeb' },
  SECURITY_HUNTER: { border: '#ddd6fe', text: '#7c3aed', bg: '#f5f3ff' },
  PERFORMANCE_ENGINEER: { border: '#a7f3d0', text: '#059669', bg: '#ecfdf5' },
  TEST_MASTER: { border: '#a5f3fc', text: '#0891b2', bg: '#ecfeff' },
  PERFECT_RUN: { border: '#fef08a', text: '#ca8a04', bg: '#fefce8' },
  DEVFORGE_VETERAN: { border: '#c7d2fe', text: '#4f46e5', bg: '#eef2ff' },
};

function formatEarnedDate(dateString) {
  if (!dateString) return 'RECENTLY';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'RECENTLY';
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
    }).toUpperCase();
  } catch {
    return 'RECENTLY';
  }
}

export default function PublicProfile() {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [error, setError] = useState(null);

  const fetchProfile = async () => {
    if (!username) return;
    setLoading(true);
    setIsNotFound(false);
    setError(null);

    try {
      const data = await getPublicProfile(username);
      setProfile(data);
    } catch (err) {
      if (err?.status === 404 || err?.response?.status === 404) {
        setIsNotFound(true);
      } else {
        setError('Profile unavailable. Unable to load developer profile.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [username]);

  if (loading) {
    return (
      <div className="page-container" style={{ padding: '4rem 1.5rem' }}>
        <Loading message={`Loading verified profile for @${username}...`} />
      </div>
    );
  }

  if (isNotFound) {
    return (
      <div className="page-container" style={{ maxWidth: '640px', padding: '4rem 1.5rem', textAlign: 'center' }}>
        <div className="card" style={{ padding: '3.5rem 2rem', borderRadius: '24px' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🔍</span>
          <span className="badge badge-SECURITY" style={{ marginBottom: '1rem' }}>
            404 NOT FOUND
          </span>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, margin: '0.25rem 0 0.75rem' }}>
            Profile Not Found
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.96rem', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            The developer profile for <strong>@{username}</strong> doesn&apos;t exist or has no active engineering activity.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <Link to="/leaderboard" className="btn btn-secondary">
              ← Back to Leaderboard
            </Link>
            <Link to="/challenges" className="btn-saas btn-saas-primary">
              Explore Challenges
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="page-container" style={{ maxWidth: '600px', padding: '4rem 1.5rem', textAlign: 'center' }}>
        <div className="card" style={{ padding: '3rem 2rem', border: '1px solid #fecaca', background: '#fef2f2', borderRadius: '24px' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.35rem', color: '#dc2626', marginBottom: '0.5rem' }}>Profile Unavailable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
            {error}
          </p>
          <button type="button" className="btn btn-primary" onClick={fetchProfile}>
            ↻ Try Again
          </button>
        </div>
      </div>
    );
  }

  const {
    overall_skill_score,
    skill_breakdown = {},
    challenges_completed = 0,
    challenges_attempted = 0,
    completion_percentage = 0.0,
    average_score = null,
    total_points = 0,
    achievements = [],
    recent_activity = [],
  } = profile;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1140px' }}>
      {/* Profile Hero Header */}
      <div
        className="card animate-fade-in-up"
        style={{
          padding: '2.5rem',
          borderRadius: '24px',
          marginBottom: '2.25rem',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)',
          border: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="candidate-avatar-large" style={{ width: 64, height: 64, fontSize: '1.5rem' }}>
            {profile.username.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem' }}>
                ⚡ VERIFIED PROFILE
              </span>
              <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 700 }}>
                ● CODEFOUNDRY EVALUATIONS
              </span>
            </div>
            <h1 style={{ fontSize: '2.1rem', fontWeight: 900, margin: 0, color: 'var(--text-primary)' }}>
              @{profile.username}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', margin: '0.2rem 0 0' }}>
              Software Engineering Readiness Profile · Evaluated Production Challenges
            </p>
          </div>
        </div>

        {/* Overall Score Highlight Card */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.25rem 1.75rem',
            textAlign: 'center',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            READINESS SCORE
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '0.3rem', margin: '0.2rem 0' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 900, color: overall_skill_score !== null ? '#2563eb' : 'var(--text-muted)', lineHeight: 1 }}>
              {overall_skill_score !== null ? overall_skill_score : '—'}
            </span>
            <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 700 }}>/ 100</span>
          </div>
          <span style={{ fontSize: '0.74rem', color: '#6366f1', fontWeight: 600 }}>
            {overall_skill_score !== null ? 'Deterministic Composite' : 'Awaiting Evaluations'}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="gency-stats-grid" style={{ marginTop: 0, marginBottom: '2.5rem' }}>
        <div className="gency-stat-tile">
          <span className="gency-stat-label">Total Points</span>
          <span className="gency-stat-number" style={{ color: '#2563eb' }}>
            <AnimatedCounter value={total_points} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Evaluated challenge total</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Solved</span>
          <span className="gency-stat-number" style={{ color: '#10b981' }}>
            <AnimatedCounter value={challenges_completed} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Distinct scenarios passed</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Attempted</span>
          <span className="gency-stat-number" style={{ color: '#f59e0b' }}>
            <AnimatedCounter value={challenges_attempted} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Active scenarios explored</span>
        </div>

        <div className="gency-stat-tile">
          <span className="gency-stat-label">Completion Rate</span>
          <span className="gency-stat-number" style={{ color: '#8b5cf6' }}>
            {completion_percentage}%
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Solved / Attempted ratio</span>
        </div>
      </div>

      {/* Main Two-Column Layout: Skill Dimensions + Achievements/Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        {/* Left Column: 6 Engineering Skill Dimensions */}
        <div className="card" style={{ padding: '2rem', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '1.2rem' }}>🎯</span>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
                Engineering Skill Dimensions
              </h2>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              6 Competencies
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {SKILL_DIMENSIONS.map((dim) => {
              const skillData = skill_breakdown[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
              const isMeasured = skillData.status === 'measured' && skillData.score !== null;

              return (
                <div key={dim.key} style={{ padding: '1rem', background: '#f8fafc', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.1rem' }}>{dim.icon}</span>
                      <strong style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>{dim.name}</strong>
                    </div>
                    {isMeasured ? (
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: dim.color }}>
                        {skillData.score}/100
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Not Measured</span>
                    )}
                  </div>
                  <AnimatedProgress value={isMeasured ? skillData.score : 0} color={dim.color} height={6} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Achievements & Recent Activity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Achievements */}
          <div className="card" style={{ padding: '2rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', paddingBottom: '0.85rem', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🏆</span>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>Achievements</h2>
              </div>
              <span className="badge badge-SECURITY">{achievements.length} EARNED</span>
            </div>

            {achievements.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', background: '#f8fafc', borderRadius: '14px' }}>
                No engineering badges earned yet. Complete evaluated challenges to unlock milestones.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                {achievements.map((ach) => {
                  const variant = BADGE_VARIANTS[ach.code] || {
                    border: '#e2e8f0',
                    text: '#2563eb',
                    bg: '#eff6ff',
                  };

                  return (
                    <div
                      key={ach.code || ach.name}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        background: variant.bg,
                        border: `1px solid ${variant.border}`,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.4rem',
                      }}
                    >
                      <span style={{ fontSize: '1.5rem' }}>{ach.icon || '🏆'}</span>
                      <strong style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>{ach.name}</strong>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                        {ach.description}
                      </p>
                      <span style={{ fontSize: '0.7rem', color: variant.text, fontWeight: 700, marginTop: 'auto' }}>
                        ✓ {formatEarnedDate(ach.earned_at)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Recent Activity */}
          <div className="card" style={{ padding: '2rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', paddingBottom: '0.85rem', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>⚡</span>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>Recent Activity</h2>
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Latest {recent_activity.length}</span>
            </div>

            {recent_activity.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', background: '#f8fafc', borderRadius: '14px' }}>
                No recent activity recorded yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recent_activity.map((act, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.85rem 1.1rem',
                      background: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <Link
                        to={`/challenges/${act.challenge_id}`}
                        style={{ fontWeight: 700, color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.92rem' }}
                      >
                        {act.challenge_title}
                      </Link>
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.2rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>{act.difficulty}</span>
                        <span>•</span>
                        <span>{act.challenge_type?.replace('_', ' ')}</span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`badge ${act.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.7rem' }}>
                        {act.status}
                      </span>
                      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.88rem', color: '#2563eb', marginTop: '0.2rem' }}>
                        {act.score} pts
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
