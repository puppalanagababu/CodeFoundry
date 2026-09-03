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
  BUG_SLAYER: { glow: 'rgba(245, 158, 11, 0.25)', border: 'rgba(245, 158, 11, 0.4)', text: '#fbbf24', bg: 'rgba(245, 158, 11, 0.08)' },
  SECURITY_HUNTER: { glow: 'rgba(139, 92, 246, 0.25)', border: 'rgba(139, 92, 246, 0.4)', text: '#c084fc', bg: 'rgba(139, 92, 246, 0.08)' },
  PERFORMANCE_ENGINEER: { glow: 'rgba(16, 185, 129, 0.25)', border: 'rgba(16, 185, 129, 0.4)', text: '#34d399', bg: 'rgba(16, 185, 129, 0.08)' },
  TEST_MASTER: { glow: 'rgba(6, 182, 212, 0.25)', border: 'rgba(6, 182, 212, 0.4)', text: '#38bdf8', bg: 'rgba(6, 182, 212, 0.08)' },
  PERFECT_RUN: { glow: 'rgba(251, 191, 36, 0.3)', border: 'rgba(251, 191, 36, 0.45)', text: '#fde047', bg: 'rgba(251, 191, 36, 0.08)' },
  DEVFORGE_VETERAN: { glow: 'rgba(99, 102, 241, 0.3)', border: 'rgba(99, 102, 241, 0.45)', text: '#818cf8', bg: 'rgba(99, 102, 241, 0.08)' },
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

  // Loading State
  if (loading) {
    return (
      <div className="container" style={{ maxWidth: '1100px', margin: '0 auto', padding: '4rem 1.5rem' }}>
        <Loading message={`Loading verified profile for @${username}...`} />
      </div>
    );
  }

  // 404 Not Found State
  if (isNotFound) {
    return (
      <div className="container" style={{ maxWidth: '680px', margin: '4rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
        <div
          className="card"
          style={{
            padding: '3.5rem 2rem',
            background: 'linear-gradient(180deg, rgba(22, 32, 52, 0.7) 0%, rgba(10, 15, 26, 0.9) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
          }}
        >
          <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '1.25rem' }}>🔍</span>
          <span className="badge badge-SECURITY" style={{ marginBottom: '1rem', display: 'inline-block' }}>
            404 NOT FOUND
          </span>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: '#fff', margin: '0.25rem 0 0.75rem' }}>
            Profile Not Found
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.98rem', maxWidth: '440px', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            The developer profile for <strong style={{ color: '#fff' }}>@{username}</strong> doesn't exist or has no active engineering activity.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/leaderboard" className="btn btn-primary" style={{ padding: '0.6rem 1.4rem' }}>
              ← Back to Leaderboard
            </Link>
            <Link to="/challenges" className="btn btn-secondary" style={{ padding: '0.6rem 1.4rem' }}>
              Explore Challenges
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Generic Error State
  if (error || !profile) {
    return (
      <div className="container" style={{ maxWidth: '600px', margin: '4rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
        <div
          className="card"
          style={{
            padding: '3rem 2rem',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            background: 'rgba(239, 68, 68, 0.05)',
          }}
        >
          <span style={{ fontSize: '2.75rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.4rem', color: '#f87171', marginBottom: '0.5rem' }}>Profile Unavailable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.75rem' }}>
            We could not retrieve this public profile right now. Please check your connection.
          </p>
          <button type="button" className="btn btn-primary" onClick={fetchProfile} style={{ padding: '0.6rem 1.5rem' }}>
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
    <div className="public-profile-page container" style={{ maxWidth: '1140px', margin: '0 auto', padding: '2rem 1.5rem 5rem' }}>
      {/* Profile Hero Header */}
      <div className="profile-hero-card">
        <div className="profile-hero-content">
          <div className="profile-avatar-large">
            {profile.username.substring(0, 2).toUpperCase()}
          </div>
          <div className="profile-hero-text">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', marginBottom: '0.35rem' }}>
              <span className="badge badge-SECURITY" style={{ fontSize: '0.75rem', padding: '0.2rem 0.65rem' }}>
                ⚡ PUBLIC ENGINEERING RECORD
              </span>
              <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
                ● VERIFIED DEVFORGE EVALUATIONS
              </span>
            </div>
            <h1 className="profile-username-title">
              @{profile.username}
            </h1>
            <p style={{ color: '#94a3b8', fontSize: '0.95rem', margin: 0, fontWeight: 500 }}>
              Software Engineering Readiness Profile · Evaluated Production Challenges
            </p>
          </div>
        </div>

        {/* Overall Score Highlight Badge */}
        <div className="profile-hero-score-badge">
          <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
            ENGINEERING READINESS
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem', margin: '0.25rem 0' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.6rem', fontWeight: 900, color: overall_skill_score !== null ? '#38bdf8' : 'var(--text-muted)', lineHeight: 1 }}>
              {overall_skill_score !== null ? overall_skill_score : '—'}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 700 }}>
              / 100
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#a5b4fc', fontWeight: 600 }}>
            {overall_skill_score !== null ? 'Deterministic Composite' : 'Awaiting Evaluations'}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="profile-metrics-grid">
        <div className="profile-metric-tile">
          <span className="profile-metric-label">TOTAL POINTS</span>
          <div className="profile-metric-value" style={{ color: '#38bdf8' }}>
            <AnimatedCounter value={total_points} />
            <small style={{ fontSize: '0.75rem', marginLeft: '0.25rem', color: 'var(--text-muted)' }}>PTS</small>
          </div>
          <span className="profile-metric-sub">Evaluated challenge total</span>
        </div>

        <div className="profile-metric-tile">
          <span className="profile-metric-label">SOLVED CHALLENGES</span>
          <div className="profile-metric-value" style={{ color: '#10b981' }}>
            <AnimatedCounter value={challenges_completed} />
          </div>
          <span className="profile-metric-sub">Distinct scenarios passed</span>
        </div>

        <div className="profile-metric-tile">
          <span className="profile-metric-label">ATTEMPTED</span>
          <div className="profile-metric-value" style={{ color: '#fbbf24' }}>
            <AnimatedCounter value={challenges_attempted} />
          </div>
          <span className="profile-metric-sub">Active scenarios explored</span>
        </div>

        <div className="profile-metric-tile">
          <span className="profile-metric-label">COMPLETION RATE</span>
          <div className="profile-metric-value" style={{ color: '#a855f7' }}>
            {completion_percentage}%
          </div>
          <span className="profile-metric-sub">Solved / Attempted ratio</span>
        </div>

        <div className="profile-metric-tile">
          <span className="profile-metric-label">AVERAGE SCORE</span>
          <div className="profile-metric-value" style={{ color: '#06b6d4' }}>
            {average_score !== null ? `${average_score}` : '—'}
          </div>
          <span className="profile-metric-sub">Across best attempts</span>
        </div>

        <div className="profile-metric-tile">
          <span className="profile-metric-label">READINESS INDEX</span>
          <div className="profile-metric-value" style={{ color: '#f43f5e' }}>
            {overall_skill_score !== null ? `${overall_skill_score}%` : '—'}
          </div>
          <span className="profile-metric-sub">Measured capability</span>
        </div>
      </div>

      {/* Main Two-Column Layout: Skill Breakdown + Activity/Achievements */}
      <div className="profile-main-layout">
        {/* Left Column: 6 Engineering Skill Dimensions */}
        <div className="profile-skills-card">
          <div className="profile-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '1.2rem' }}>🎯</span>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                Engineering Skill Dimensions
              </h2>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              6 Competencies
            </span>
          </div>

          <div className="profile-skills-list">
            {SKILL_DIMENSIONS.map((dim) => {
              const skillData = skill_breakdown[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
              const isMeasured = skillData.status === 'measured' && skillData.score !== null;

              return (
                <div key={dim.key} className="profile-skill-item">
                  <div className="profile-skill-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>{dim.icon}</span>
                      <div>
                        <strong style={{ color: '#fff', fontSize: '0.92rem', display: 'block' }}>
                          {dim.name}
                        </strong>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {isMeasured
                            ? `Measured across ${skillData.sample_size} scenario${skillData.sample_size !== 1 ? 's' : ''}`
                            : 'No evaluated evidence yet'}
                        </span>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      {isMeasured ? (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.05rem', fontWeight: 800, color: dim.color }}>
                          {skillData.score} <small style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>/ 100</small>
                        </span>
                      ) : (
                        <span className="badge badge-insufficient" style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                          NOT MEASURED
                        </span>
                      )}
                    </div>
                  </div>

                  {isMeasured ? (
                    <div style={{ marginTop: '0.6rem' }}>
                      <AnimatedProgress value={skillData.score} max={100} color={dim.color} />
                    </div>
                  ) : (
                    <div className="unmeasured-progress-bar" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Achievements & Recent Activity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {/* Real Achievements / Badges Section */}
          <div className="profile-achievements-card">
            <div className="profile-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🏆</span>
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                    Achievements
                  </h2>
                </div>
              </div>
              <span className="badge badge-SECURITY" style={{ fontSize: '0.72rem', padding: '0.18rem 0.6rem' }}>
                {achievements.length} EARNED
              </span>
            </div>

            <div style={{ padding: '1.25rem 1.5rem' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', margin: '0 0 1.25rem', lineHeight: 1.45 }}>
                Verified milestones earned through evaluated engineering challenges.
              </p>

              {achievements.length === 0 ? (
                <div className="profile-achievements-empty">
                  <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.6rem' }}>🎖️</span>
                  <strong style={{ color: '#fff', fontSize: '0.98rem', display: 'block', marginBottom: '0.35rem' }}>
                    No engineering badges earned yet.
                  </strong>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', margin: 0, lineHeight: 1.5 }}>
                    Complete evaluated challenges to unlock verified DevForge achievements.
                  </p>
                </div>
              ) : (
                <div className="profile-achievements-grid">
                  {achievements.map((ach) => {
                    const variant = BADGE_VARIANTS[ach.code] || {
                      glow: 'rgba(56, 189, 248, 0.25)',
                      border: 'rgba(56, 189, 248, 0.4)',
                      text: '#38bdf8',
                      bg: 'rgba(56, 189, 248, 0.08)',
                    };

                    return (
                      <div
                        key={ach.code || ach.name}
                        className="profile-achievement-card"
                        style={{
                          borderColor: variant.border,
                          boxShadow: `0 8px 24px rgba(0, 0, 0, 0.5), 0 0 16px ${variant.glow}`,
                        }}
                      >
                        <div
                          className="profile-achievement-icon-wrapper"
                          style={{ background: variant.bg, borderColor: variant.border }}
                        >
                          <span className="profile-achievement-icon" role="img" aria-label={ach.name}>
                            {ach.icon || '🏆'}
                          </span>
                        </div>
                        <div className="profile-achievement-details">
                          <strong className="profile-achievement-name">
                            {ach.name}
                          </strong>
                          <p className="profile-achievement-desc">
                            {ach.description}
                          </p>
                          <div className="profile-achievement-earned" style={{ color: variant.text }}>
                            <span>✓ EARNED · {formatEarnedDate(ach.earned_at)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity Timeline */}
          <div className="profile-activity-card">
            <div className="profile-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>⚡</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                  Recent Evaluated Activity
                </h2>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Latest {recent_activity.length}
              </span>
            </div>

            <div className="profile-activity-body">
              {recent_activity.length === 0 ? (
                <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                  <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>📂</span>
                  Complete a challenge to start building your engineering history.
                </div>
              ) : (
                <div className="profile-activity-list">
                  {recent_activity.map((act, index) => (
                    <div key={index} className="profile-activity-item">
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                        <span className={`badge badge-${act.challenge_type}`} style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                          {act.challenge_type.replace('_', ' ')}
                        </span>
                        <span className={`status-badge status-${act.status}`} style={{ fontSize: '0.72rem', padding: '0.15rem 0.55rem' }}>
                          {act.status}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <Link
                          to={`/challenges/${act.challenge_id}`}
                          className="activity-challenge-title"
                        >
                          {act.challenge_title}
                        </Link>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.9rem', color: '#38bdf8', flexShrink: 0 }}>
                          {act.score} pts
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.35rem', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        <span>Difficulty: <strong style={{ color: '#cbd5e1' }}>{act.difficulty}</strong></span>
                        <span>·</span>
                        <span>
                          {act.evaluated_at
                            ? new Date(act.evaluated_at).toLocaleDateString(undefined, {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })
                            : 'Recently'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
