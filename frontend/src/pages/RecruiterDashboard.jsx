import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getRecruiterCandidates, getRecruiterCandidate } from '../api/recruiter';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';

const CHALLENGE_TYPES = [
  { value: '', label: 'All Challenge Types' },
  { value: 'BUG_FIX', label: 'Bug Fix' },
  { value: 'FEATURE', label: 'Feature' },
  { value: 'API', label: 'API Integration' },
  { value: 'DATABASE', label: 'Database' },
  { value: 'PERFORMANCE', label: 'Performance' },
  { value: 'SECURITY', label: 'Security' },
  { value: 'TESTING', label: 'Testing' },
  { value: 'CODE_REVIEW', label: 'Code Review' },
  { value: 'DEBUGGING', label: 'Debugging' },
];

const SKILL_DIMENSIONS = [
  { key: 'problem_solving', name: 'Problem Solving', icon: '⚡', color: '#3b82f6' },
  { key: 'debugging', name: 'Debugging', icon: '🐛', color: '#f59e0b' },
  { key: 'security', name: 'Security', icon: '🛡️', color: '#8b5cf6' },
  { key: 'performance', name: 'Performance', icon: '🚀', color: '#10b981' },
  { key: 'code_quality', name: 'Code Quality', icon: '📦', color: '#64748b' },
  { key: 'testing', name: 'Testing', icon: '🧪', color: '#06b6d4' },
];

export default function RecruiterDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isForbidden, setIsForbidden] = useState(false);

  // Filter States
  const [search, setSearch] = useState('');
  const [minSkillScore, setMinSkillScore] = useState('');
  const [challengeType, setChallengeType] = useState('');

  // Candidate Detail Drawer State
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    setIsForbidden(false);

    try {
      const params = {};
      if (search) params.search = search;
      if (minSkillScore) params.min_skill_score = minSkillScore;
      if (challengeType) params.challenge_type = challengeType;

      const data = await getRecruiterCandidates(params);
      setCandidates(data.results || []);
    } catch (err) {
      if (err?.status === 403 || err?.response?.status === 403) {
        setIsForbidden(true);
      } else {
        setError(err.message || 'Unable to load candidates.');
      }
    } finally {
      setLoading(false);
    }
  }, [search, minSkillScore, challengeType]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const handleSelectCandidate = async (username) => {
    setDetailLoading(true);
    setDetailError(null);
    setSelectedCandidate({ username });

    try {
      const data = await getRecruiterCandidate(username);
      setSelectedCandidate(data);
    } catch (err) {
      setDetailError('Unable to load candidate assessment.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedCandidate(null);
    setDetailError(null);
  };

  const handleClearFilters = () => {
    setSearch('');
    setMinSkillScore('');
    setChallengeType('');
  };

  // 403 Forbidden Access State
  if (isForbidden) {
    return (
      <div className="container" style={{ maxWidth: '640px', margin: '4.5rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
        <div
          className="card"
          style={{
            padding: '3.5rem 2rem',
            background: 'linear-gradient(180deg, rgba(22, 32, 54, 0.9) 0%, rgba(10, 15, 26, 0.95) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(239, 68, 68, 0.15)',
          }}
        >
          <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '1.25rem' }}>🛡️</span>
          <span className="badge badge-SECURITY" style={{ marginBottom: '1rem', display: 'inline-block' }}>
            ACCESS RESTRICTED
          </span>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.9rem', color: '#fff', margin: '0.25rem 0 0.75rem' }}>
            Recruiter Access Required
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', maxWidth: '440px', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            Your account does not have <strong>Recruiter authorization</strong>. This dashboard is reserved for verified engineering recruitment partners.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/dashboard" className="btn btn-primary" style={{ padding: '0.6rem 1.4rem' }}>
              ← Return to Dashboard
            </Link>
            <Link to="/leaderboard" className="btn btn-secondary" style={{ padding: '0.6rem 1.4rem' }}>
              View Public Leaderboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="recruiter-dashboard-page container" style={{ maxWidth: '1240px', margin: '0 auto', padding: '2rem 1.5rem 5rem' }}>
      {/* Dashboard Header */}
      <div className="recruiter-hero-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem', padding: '0.2rem 0.65rem' }}>
              ⚡ RECRUITER ASSESSMENT RADAR
            </span>
            <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
              ● REAL PRODUCTION EVIDENCE
            </span>
          </div>
          <h1 className="recruiter-dashboard-title">
            Recruiter Dashboard
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.96rem', margin: 0, fontWeight: 500 }}>
            Evaluate developer readiness through real engineering performance.
          </p>
        </div>

        <div className="recruiter-count-badge">
          <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
            ASSESSED CANDIDATES
          </span>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', fontWeight: 900, color: '#38bdf8', lineHeight: 1.1, margin: '0.2rem 0' }}>
            {candidates.length}
          </div>
          <span style={{ fontSize: '0.72rem', color: '#a5b4fc', fontWeight: 600 }}>
            Active Evaluated Engineers
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="recruiter-filter-toolbar">
        <div className="recruiter-search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="recruiter-input"
            placeholder="Search candidate by username..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="recruiter-filter-selects">
          <select
            className="recruiter-select"
            value={minSkillScore}
            onChange={(e) => setMinSkillScore(e.target.value)}
          >
            <option value="">Min Skill Score: Any</option>
            <option value="60">Min Score: 60+</option>
            <option value="70">Min Score: 70+</option>
            <option value="80">Min Score: 80+</option>
            <option value="90">Min Score: 90+</option>
          </select>

          <select
            className="recruiter-select"
            value={challengeType}
            onChange={(e) => setChallengeType(e.target.value)}
          >
            {CHALLENGE_TYPES.map((ct) => (
              <option key={ct.value} value={ct.value}>
                {ct.label}
              </option>
            ))}
          </select>

          {(search || minSkillScore || challengeType) && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClearFilters}
              style={{ padding: '0.55rem 1rem', fontSize: '0.82rem', whiteSpace: 'nowrap' }}
            >
              ↻ Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Loading candidate assessments..." />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', margin: '2rem 0' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.3rem', color: '#f87171', marginBottom: '0.5rem' }}>Failed to Load Candidates</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={fetchCandidates}>
            ↻ Retry Request
          </button>
        </div>
      ) : candidates.length === 0 ? (
        <div className="recruiter-empty-state">
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📂</span>
          <h2 style={{ fontSize: '1.35rem', color: '#fff', marginBottom: '0.4rem' }}>No Candidates Found</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '420px', margin: '0 auto 1.5rem', lineHeight: 1.5 }}>
            No evaluated candidates match your active filters. Try broadening your score or domain criteria.
          </p>
          {(search || minSkillScore || challengeType) && (
            <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
              Reset Filters
            </button>
          )}
        </div>
      ) : (
        <div className="recruiter-table-card">
          <div className="recruiter-table-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '1.15rem' }}>📊</span>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                Candidate Assessments ({candidates.length})
              </h2>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Sorted by Overall Readiness
            </span>
          </div>

          <div className="recruiter-table-wrapper">
            <table className="recruiter-table">
              <thead>
                <tr>
                  <th style={{ width: '60px', textAlign: 'center' }}>#</th>
                  <th>Candidate</th>
                  <th style={{ textAlign: 'center' }}>Overall Score</th>
                  <th style={{ textAlign: 'right' }}>Total Points</th>
                  <th style={{ textAlign: 'center' }}>Solved</th>
                  <th style={{ textAlign: 'right' }}>Avg Score</th>
                  <th style={{ textAlign: 'center' }}>Completion</th>
                  <th style={{ textAlign: 'center' }}>Badges</th>
                  <th style={{ textAlign: 'right' }}>Assessment</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((cand, idx) => {
                  const hasScore = cand.overall_skill_score !== null;
                  return (
                    <tr
                      key={cand.user_id}
                      className="recruiter-candidate-row"
                      onClick={() => handleSelectCandidate(cand.username)}
                    >
                      <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontWeight: 700 }}>
                        {idx + 1}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div className="candidate-avatar">
                            {cand.username.substring(0, 2).toUpperCase()}
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <strong style={{ color: '#fff', fontSize: '0.94rem' }}>
                              {cand.username}
                            </strong>
                            <Link
                              to={`/profile/${encodeURIComponent(cand.username)}`}
                              className="candidate-profile-link"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Public Profile ↗
                            </Link>
                          </div>
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {hasScore ? (
                          <span
                            className="badge"
                            style={{
                              background: 'rgba(56, 189, 248, 0.12)',
                              color: '#38bdf8',
                              border: '1px solid rgba(56, 189, 248, 0.35)',
                              fontFamily: 'var(--font-mono)',
                              fontWeight: 800,
                              fontSize: '0.85rem',
                              padding: '0.25rem 0.65rem',
                            }}
                          >
                            {cand.overall_skill_score} / 100
                          </span>
                        ) : (
                          <span className="badge badge-insufficient" style={{ fontSize: '0.72rem' }}>
                            Not Measured
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#38bdf8' }}>
                        {cand.total_points}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className="badge badge-BUG_FIX" style={{ fontSize: '0.74rem', padding: '0.15rem 0.55rem' }}>
                          {cand.challenges_completed}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {cand.average_score !== null ? cand.average_score : '—'}
                      </td>
                      <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: '#a855f7', fontWeight: 700 }}>
                        {cand.completion_percentage}%
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fbbf24' }}>
                          🏆 {cand.achievements_count}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.8rem', fontSize: '0.78rem' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectCandidate(cand.username);
                          }}
                        >
                          View Assessment →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Candidate Detailed Assessment Drawer / Modal */}
      {selectedCandidate && (
        <div className="recruiter-drawer-overlay" onClick={handleCloseDetail}>
          <div className="recruiter-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="recruiter-drawer-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <div className="candidate-avatar-large">
                  {selectedCandidate.username.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 900, color: '#fff', margin: 0 }}>
                      @{selectedCandidate.username}
                    </h2>
                    <Link
                      to={`/profile/${encodeURIComponent(selectedCandidate.username)}`}
                      className="badge badge-SECURITY"
                      style={{ textDecoration: 'none', fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}
                      target="_blank"
                    >
                      Public Profile ↗
                    </Link>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Evaluated Engineering Assessment Evidence
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="recruiter-drawer-close"
                onClick={handleCloseDetail}
                aria-label="Close assessment"
              >
                ✕
              </button>
            </div>

            <div className="recruiter-drawer-body">
              {detailLoading ? (
                <div style={{ padding: '4rem 0' }}>
                  <Loading message={`Loading assessment for @${selectedCandidate.username}...`} />
                </div>
              ) : detailError ? (
                <div style={{ padding: '2rem', textAlign: 'center' }}>
                  <p style={{ color: '#f87171' }}>{detailError}</p>
                </div>
              ) : (
                <>
                  {/* Readiness Score Box */}
                  <div className="recruiter-score-banner">
                    <div>
                      <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)' }}>
                        OVERALL READINESS SCORE
                      </span>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.2rem' }}>
                        <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem', fontWeight: 900, color: selectedCandidate.overall_skill_score !== null ? '#38bdf8' : 'var(--text-muted)', lineHeight: 1 }}>
                          {selectedCandidate.overall_skill_score !== null ? selectedCandidate.overall_skill_score : '—'}
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 700 }}>
                          / 100
                        </span>
                      </div>
                    </div>
                    <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem' }}>
                      Deterministic Composite
                    </span>
                  </div>

                  {/* Metrics 5-Tile Grid */}
                  <div className="recruiter-drawer-metrics">
                    <div className="drawer-metric-item">
                      <span className="drawer-metric-label">TOTAL POINTS</span>
                      <strong className="drawer-metric-val" style={{ color: '#38bdf8' }}>
                        {selectedCandidate.metrics?.total_points ?? 0}
                      </strong>
                    </div>
                    <div className="drawer-metric-item">
                      <span className="drawer-metric-label">SOLVED</span>
                      <strong className="drawer-metric-val" style={{ color: '#10b981' }}>
                        {selectedCandidate.metrics?.challenges_completed ?? 0}
                      </strong>
                    </div>
                    <div className="drawer-metric-item">
                      <span className="drawer-metric-label">ATTEMPTED</span>
                      <strong className="drawer-metric-val" style={{ color: '#fbbf24' }}>
                        {selectedCandidate.metrics?.challenges_attempted ?? 0}
                      </strong>
                    </div>
                    <div className="drawer-metric-item">
                      <span className="drawer-metric-label">AVG SCORE</span>
                      <strong className="drawer-metric-val" style={{ color: '#06b6d4' }}>
                        {selectedCandidate.metrics?.average_score ?? '—'}
                      </strong>
                    </div>
                    <div className="drawer-metric-item">
                      <span className="drawer-metric-label">COMPLETION</span>
                      <strong className="drawer-metric-val" style={{ color: '#a855f7' }}>
                        {selectedCandidate.metrics?.completion_percentage ?? 0}%
                      </strong>
                    </div>
                  </div>

                  {/* 6 Engineering Skills */}
                  <div className="recruiter-drawer-section">
                    <h3 className="drawer-section-title">
                      <span>🎯</span> Skill Dimensions
                    </h3>
                    <div className="drawer-skills-list">
                      {SKILL_DIMENSIONS.map((dim) => {
                        const sData = selectedCandidate.skills?.[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
                        const isMeas = sData.status === 'measured' && sData.score !== null;

                        return (
                          <div key={dim.key} className="drawer-skill-row">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                                <span>{dim.icon}</span>
                                <strong style={{ color: '#fff', fontSize: '0.88rem' }}>{dim.name}</strong>
                              </div>
                              {isMeas ? (
                                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: dim.color, fontSize: '0.92rem' }}>
                                  {sData.score} <small style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>/ 100 ({sData.sample_size} evals)</small>
                                </span>
                              ) : (
                                <span className="badge badge-insufficient" style={{ fontSize: '0.66rem' }}>
                                  Not Measured
                                </span>
                              )}
                            </div>
                            {isMeas ? (
                              <AnimatedProgress value={sData.score} max={100} color={dim.color} />
                            ) : (
                              <div className="unmeasured-progress-bar" />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Earned Badges */}
                  <div className="recruiter-drawer-section">
                    <h3 className="drawer-section-title">
                      <span>🏆</span> Earned Achievements ({selectedCandidate.achievements?.length ?? 0})
                    </h3>
                    {selectedCandidate.achievements?.length === 0 ? (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                        No badges earned yet.
                      </p>
                    ) : (
                      <div className="drawer-achievements-list">
                        {selectedCandidate.achievements.map((ach) => (
                          <div key={ach.code} className="drawer-achievement-pill">
                            <span style={{ fontSize: '1.2rem' }}>{ach.icon || '🏆'}</span>
                            <div>
                              <strong style={{ color: '#fff', fontSize: '0.84rem', display: 'block' }}>
                                {ach.name}
                              </strong>
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                {ach.description}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Challenge Evidence Timeline */}
                  <div className="recruiter-drawer-section">
                    <h3 className="drawer-section-title">
                      <span>⚡</span> Evaluated Challenge Evidence ({selectedCandidate.challenge_evidence?.length ?? 0})
                    </h3>
                    {selectedCandidate.challenge_evidence?.length === 0 ? (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                        No evaluated challenge evidence available.
                      </p>
                    ) : (
                      <div className="drawer-evidence-list">
                        {selectedCandidate.challenge_evidence.map((ev, idx) => (
                          <div key={idx} className="drawer-evidence-item">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                              <span className={`badge badge-${ev.challenge_type}`} style={{ fontSize: '0.66rem', padding: '0.12rem 0.45rem' }}>
                                {ev.challenge_type.replace('_', ' ')}
                              </span>
                              <span className={`status-badge status-${ev.status}`} style={{ fontSize: '0.68rem', padding: '0.12rem 0.5rem' }}>
                                {ev.status}
                              </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '0.5rem' }}>
                              <strong style={{ color: '#fff', fontSize: '0.88rem' }}>
                                {ev.challenge_title}
                              </strong>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#38bdf8', fontSize: '0.86rem' }}>
                                {ev.score} pts
                              </span>
                            </div>

                            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.3rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              <span>Difficulty: <strong style={{ color: '#cbd5e1' }}>{ev.difficulty}</strong></span>
                              <span>·</span>
                              <span>
                                {ev.evaluated_at
                                  ? new Date(ev.evaluated_at).toLocaleDateString(undefined, {
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
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
