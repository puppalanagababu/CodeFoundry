import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPublicProfile } from '../api/profile';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';
import {
  getSkillIcon,
  UserX,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Award,
  Activity,
  Zap,
} from '../components/RealisticIcons';

const SKILL_DIMENSIONS = [
  { key: 'problem_solving', name: 'Problem Solving', color: '#1D4ED8' },
  { key: 'debugging', name: 'Debugging', color: '#DC2626' },
  { key: 'security', name: 'Security', color: '#6D28D9' },
  { key: 'performance', name: 'Performance', color: '#047857' },
  { key: 'code_quality', name: 'Code Quality', color: '#D97706' },
  { key: 'testing', name: 'Testing', color: '#0E7490' },
];

const BADGE_VARIANTS = {
  BUG_SLAYER: { border: 'var(--pastel-yellow-border)', text: 'var(--pastel-yellow-text)', bg: 'var(--pastel-yellow-light)' },
  SECURITY_HUNTER: { border: 'var(--pastel-lavender-border)', text: 'var(--pastel-lavender-text)', bg: 'var(--pastel-lavender-light)' },
  PERFORMANCE_ENGINEER: { border: 'var(--pastel-mint-border)', text: 'var(--pastel-mint-text)', bg: 'var(--pastel-mint-light)' },
  TEST_MASTER: { border: 'var(--pastel-blue-border)', text: 'var(--pastel-blue-text)', bg: 'var(--pastel-blue-light)' },
  PERFECT_RUN: { border: 'var(--pastel-yellow-border)', text: 'var(--pastel-yellow-text)', bg: 'var(--pastel-yellow-light)' },
  DEVFORGE_VETERAN: { border: 'var(--pastel-lavender-border)', text: 'var(--pastel-lavender-text)', bg: 'var(--pastel-lavender-light)' },
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
        <div className="card panel-pastel-lavender" style={{ padding: '3.5rem 2rem', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <UserX size={48} color="var(--text-muted)" />
          </div>
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
        <div className="card" style={{ padding: '3rem 2rem', border: '1px solid var(--accent-danger-border)', background: 'var(--accent-danger-light)', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <AlertTriangle size={48} color="var(--accent-danger)" />
          </div>
          <h2 style={{ fontSize: '1.35rem', color: 'var(--accent-danger)', marginBottom: '0.5rem' }}>Profile Unavailable</h2>
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
    total_points = 0,
    achievements = [],
    recent_activity = [],
  } = profile;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1140px' }}>
      {/* 1. Profile Hero Header */}
      <div
        className="card panel-pastel-lavender animate-fade-in-up"
        style={{
          padding: '2.5rem',
          borderRadius: '24px',
          marginBottom: '2.25rem',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="candidate-avatar-large" style={{ width: 68, height: 68, fontSize: '1.6rem', background: 'var(--pastel-lavender)', color: 'var(--pastel-lavender-text)', border: '2px solid var(--pastel-lavender-border)' }}>
            {profile.username.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={12} /> VERIFIED CANDIDATE
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--pastel-mint-text)', fontWeight: 800 }}>
                ● PRODUCTION EVALUATIONS
              </span>
            </div>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 900, margin: 0, color: 'var(--text-primary)' }}>
              @{profile.username}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0.2rem 0 0' }}>
              Software Engineering Readiness Profile · Evaluated Codebase Simulations
            </p>
          </div>
        </div>

        {/* Overall Score Highlight Card */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: '18px',
            padding: '1.25rem 1.85rem',
            textAlign: 'center',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <span style={{ fontSize: '0.76rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            READINESS SCORE
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: '0.3rem', margin: '0.25rem 0' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.6rem', fontWeight: 900, color: overall_skill_score !== null ? 'var(--accent-primary)' : 'var(--text-muted)', lineHeight: 1 }}>
              {overall_skill_score !== null ? overall_skill_score : '—'}
            </span>
            <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 700 }}>/ 100</span>
          </div>
          <span style={{ fontSize: '0.76rem', color: 'var(--accent-primary)', fontWeight: 700 }}>
            {overall_skill_score !== null ? 'Deterministic Composite' : 'Awaiting Evaluations'}
          </span>
        </div>
      </div>

      {/* 2. Top Metric Tiles */}
      <div className="gency-stats-grid" style={{ marginTop: 0, marginBottom: '2.5rem' }}>
        <div className="card panel-pastel-blue" style={{ padding: '1.6rem 1.85rem', borderRadius: '20px' }}>
          <span className="gency-stat-label" style={{ color: 'var(--pastel-blue-text)' }}>Total Points</span>
          <span className="gency-stat-number" style={{ color: 'var(--pastel-blue-text)', marginTop: '0.35rem' }}>
            <AnimatedCounter value={total_points} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Evaluated challenge total</span>
        </div>

        <div className="card panel-pastel-mint" style={{ padding: '1.6rem 1.85rem', borderRadius: '20px' }}>
          <span className="gency-stat-label" style={{ color: 'var(--pastel-mint-text)' }}>Solved</span>
          <span className="gency-stat-number" style={{ color: 'var(--pastel-mint-text)', marginTop: '0.35rem' }}>
            <AnimatedCounter value={challenges_completed} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Distinct scenarios passed</span>
        </div>

        <div className="card panel-pastel-peach" style={{ padding: '1.6rem 1.85rem', borderRadius: '20px' }}>
          <span className="gency-stat-label" style={{ color: 'var(--pastel-peach-text)' }}>Attempted</span>
          <span className="gency-stat-number" style={{ color: 'var(--pastel-peach-text)', marginTop: '0.35rem' }}>
            <AnimatedCounter value={challenges_attempted} />
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Active scenarios explored</span>
        </div>

        <div className="card panel-pastel-lavender" style={{ padding: '1.6rem 1.85rem', borderRadius: '20px' }}>
          <span className="gency-stat-label" style={{ color: 'var(--pastel-lavender-text)' }}>Completion Rate</span>
          <span className="gency-stat-number" style={{ color: 'var(--pastel-lavender-text)', marginTop: '0.35rem' }}>
            {completion_percentage}%
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Solved / Attempted ratio</span>
        </div>
      </div>

      {/* 3. Main Two-Column Layout: Skill Dimensions + Achievements/Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        {/* Left Column: 6 Engineering Skill Dimensions */}
        <div className="card animate-fade-in-up" style={{ padding: '2.25rem', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <BarChart3 size={20} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0 }}>
                Engineering Competencies
              </h2>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
              6 Dimensions
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {SKILL_DIMENSIONS.map((dim) => {
              const skillData = skill_breakdown[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
              const isMeasured = skillData.status === 'measured' && skillData.score !== null;

              return (
                <div key={dim.key} style={{ padding: '1.1rem 1.25rem', background: '#ffffff', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.55rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center' }}>{getSkillIcon(dim.key, 18, dim.color)}</span>
                      <strong style={{ fontSize: '0.94rem', color: 'var(--text-primary)' }}>{dim.name}</strong>
                    </div>
                    {isMeasured ? (
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: dim.color }}>
                        {skillData.score}/100
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Not Measured</span>
                    )}
                  </div>
                  <AnimatedProgress value={isMeasured ? skillData.score : 0} color={dim.color} height={7} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Achievements & Recent Activity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Achievements Gallery */}
          <div className="card animate-fade-in-up" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.35rem', paddingBottom: '0.85rem', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Award size={20} color="var(--accent-warning)" />
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0 }}>Achievements</h2>
              </div>
              <span className="badge badge-SECURITY">{achievements.length} EARNED</span>
            </div>

            {achievements.length === 0 ? (
              <div style={{ padding: '2.25rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderRadius: '16px' }}>
                No engineering badges earned yet. Complete evaluated challenges to unlock milestones.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                {achievements.map((ach) => {
                  const variant = BADGE_VARIANTS[ach.code] || {
                    border: 'var(--pastel-blue-border)',
                    text: 'var(--pastel-blue-text)',
                    bg: 'var(--pastel-blue-light)',
                  };

                  return (
                    <div
                      key={ach.code || ach.name}
                      style={{
                        padding: '1.15rem',
                        borderRadius: '16px',
                        background: variant.bg,
                        border: `1px solid ${variant.border}`,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.45rem',
                      }}
                    >
                      <div style={{ marginBottom: '0.25rem' }}>
                        <Award size={24} color={variant.text} />
                      </div>
                      <strong style={{ fontSize: '0.94rem', color: 'var(--text-primary)' }}>{ach.name}</strong>
                      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.45 }}>
                        {ach.description}
                      </p>
                      <span style={{ fontSize: '0.72rem', color: variant.text, fontWeight: 800, marginTop: 'auto', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle2 size={12} /> {formatEarnedDate(ach.earned_at)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Recent Activity */}
          <div className="card animate-fade-in-up" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.35rem', paddingBottom: '0.85rem', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Activity size={20} color="#1E5EA8" />
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0 }}>Recent Activity</h2>
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>Latest {recent_activity.length}</span>
            </div>

            {recent_activity.length === 0 ? (
              <div style={{ padding: '2.25rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderRadius: '16px' }}>
                No recent activity recorded yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {recent_activity.map((act, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.95rem 1.25rem',
                      background: '#ffffff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '14px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  >
                    <div>
                      <Link
                        to={`/challenges/${act.challenge_id}`}
                        style={{ fontWeight: 800, color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.94rem' }}
                      >
                        {act.challenge_title}
                      </Link>
                      <div style={{ display: 'flex', gap: '0.55rem', marginTop: '0.2rem', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                        <span>{act.difficulty}</span>
                        <span>•</span>
                        <span>{act.challenge_type?.replace('_', ' ')}</span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`badge ${act.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.72rem' }}>
                        {act.status}
                      </span>
                      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.92rem', color: 'var(--accent-primary)', marginTop: '0.25rem' }}>
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
