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

  // Comparison State
  const [comparisonList, setComparisonList] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [comparisonDetails, setComparisonDetails] = useState([]);
  const [comparingLoading, setComparingLoading] = useState(false);

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

  const toggleCompare = (username, e) => {
    e.stopPropagation();
    if (comparisonList.includes(username)) {
      setComparisonList(comparisonList.filter((u) => u !== username));
    } else {
      if (comparisonList.length >= 4) {
        alert('You can compare up to 4 candidates at a time.');
        return;
      }
      setComparisonList([...comparisonList, username]);
    }
  };

  const handleOpenComparison = async () => {
    if (comparisonList.length < 2) return;
    setShowComparisonModal(true);
    setComparingLoading(true);

    try {
      const details = await Promise.all(
        comparisonList.map((u) => getRecruiterCandidate(u).catch(() => null))
      );
      setComparisonDetails(details.filter(Boolean));
    } catch {
      // ignore
    } finally {
      setComparingLoading(false);
    }
  };

  if (isForbidden) {
    return (
      <div className="page-container" style={{ maxWidth: '640px', padding: '4.5rem 1.5rem', textAlign: 'center' }}>
        <div className="card" style={{ padding: '3.5rem 2rem', borderRadius: '24px' }}>
          <span style={{ fontSize: '3.5rem', display: 'block', marginBottom: '1.25rem' }}>🛡️</span>
          <span className="badge badge-SECURITY" style={{ marginBottom: '1rem' }}>
            ACCESS RESTRICTED
          </span>
          <h1 style={{ fontSize: '1.9rem', fontWeight: 800, margin: '0.25rem 0 0.75rem' }}>
            Recruiter Access Required
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            Your account does not have <strong>Recruiter authorization</strong>. This dashboard is reserved for verified engineering recruitment partners.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <Link to="/dashboard" className="btn btn-primary">
              ← Return to Dashboard
            </Link>
            <Link to="/leaderboard" className="btn btn-secondary">
              View Public Leaderboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1240px' }}>
      {/* Header Banner */}
      <div className="recruiter-hero-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem' }}>
              ⚡ RECRUITER ASSESSMENT RADAR
            </span>
            <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 700 }}>
              ● VERIFIED DOCKER SANDBOX EVIDENCE
            </span>
          </div>
          <h1 className="recruiter-dashboard-title">
            Recruiter Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.96rem', margin: 0, fontWeight: 500 }}>
            Evaluate developer readiness through verifiable production engineering performance.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {comparisonList.length >= 2 && (
            <button
              type="button"
              className="btn-saas btn-saas-primary"
              onClick={handleOpenComparison}
              style={{ padding: '0.75rem 1.6rem', fontSize: '0.9rem' }}
            >
              <span>Compare ({comparisonList.length})</span>
              <span className="btn-arrow-icon">→</span>
            </button>
          )}

          <div className="recruiter-count-badge">
            <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)' }}>
              ASSESSED CANDIDATES
            </span>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', fontWeight: 900, color: '#2563eb', lineHeight: 1.1, margin: '0.2rem 0' }}>
              {candidates.length}
            </div>
            <span style={{ fontSize: '0.74rem', color: '#6366f1', fontWeight: 600 }}>
              Active Evaluated Engineers
            </span>
          </div>
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
              style={{ padding: '0.65rem 1.1rem', fontSize: '0.85rem' }}
            >
              ↻ Clear
            </button>
          )}
        </div>
      </div>

      {/* Main Table Card */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Loading candidate assessments..." />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', margin: '2rem 0' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.3rem', color: '#dc2626', marginBottom: '0.5rem' }}>Failed to Load Candidates</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={fetchCandidates}>
            ↻ Retry Request
          </button>
        </div>
      ) : candidates.length === 0 ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📂</span>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.4rem' }}>No Candidates Found</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
            No evaluated candidates match your active filters. Try broadening your criteria.
          </p>
          {(search || minSkillScore || challengeType) && (
            <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
              Reset Filters
            </button>
          )}
        </div>
      ) : (
        <div className="card" style={{ padding: '1.75rem', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '1.15rem' }}>📊</span>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>
                Candidate Assessments ({candidates.length})
              </h2>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select checkbox to compare candidates side-by-side
            </span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '40px', textAlign: 'center' }}>Compare</th>
                  <th style={{ width: '50px', textAlign: 'center' }}>#</th>
                  <th>Candidate</th>
                  <th style={{ textAlign: 'center' }}>Overall Score</th>
                  <th style={{ textAlign: 'right' }}>Total Points</th>
                  <th style={{ textAlign: 'center' }}>Solved</th>
                  <th style={{ textAlign: 'right' }}>Avg Score</th>
                  <th style={{ textAlign: 'center' }}>Completion</th>
                  <th style={{ textAlign: 'right' }}>Assessment</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((cand, idx) => {
                  const hasScore = cand.overall_skill_score !== null;
                  const isCompared = comparisonList.includes(cand.username);

                  return (
                    <tr
                      key={cand.user_id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleSelectCandidate(cand.username)}
                    >
                      <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isCompared}
                          onChange={(e) => toggleCompare(cand.username, e)}
                          style={{ cursor: 'pointer', width: 16, height: 16 }}
                          title="Select to compare"
                        />
                      </td>
                      <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontWeight: 700 }}>
                        {idx + 1}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div className="candidate-avatar">
                            {cand.username.substring(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <strong style={{ color: 'var(--text-primary)', fontSize: '0.94rem' }}>
                              {cand.username}
                            </strong>
                            <div>
                              <Link
                                to={`/profile/${encodeURIComponent(cand.username)}`}
                                style={{ fontSize: '0.76rem', color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                Public Profile ↗
                              </Link>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {hasScore ? (
                          <span
                            className="badge"
                            style={{
                              background: '#eff6ff',
                              color: '#2563eb',
                              border: '1px solid #bfdbfe',
                              fontFamily: 'var(--font-mono)',
                              fontWeight: 800,
                              fontSize: '0.85rem',
                            }}
                          >
                            {cand.overall_skill_score} / 100
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                            Not Measured
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#2563eb' }}>
                        {cand.total_points}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className="badge badge-BUG_FIX" style={{ fontSize: '0.74rem' }}>
                          {cand.challenges_completed}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {cand.average_score !== null ? cand.average_score : '—'}
                      </td>
                      <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: '#7c3aed', fontWeight: 700 }}>
                        {cand.completion_percentage}%
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectCandidate(cand.username);
                          }}
                        >
                          View Dossier →
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

      {/* Candidate Assessment Drawer */}
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
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>
                      @{selectedCandidate.username}
                    </h2>
                    <Link
                      to={`/profile/${encodeURIComponent(selectedCandidate.username)}`}
                      className="badge badge-SECURITY"
                      style={{ textDecoration: 'none', fontSize: '0.7rem' }}
                      target="_blank"
                    >
                      Public Profile ↗
                    </Link>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Evaluated Engineering Assessment Evidence
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleCloseDetail}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
              >
                ✕ Close
              </button>
            </div>

            {detailLoading ? (
              <div style={{ padding: '4rem 0' }}>
                <Loading message={`Loading assessment for @${selectedCandidate.username}...`} />
              </div>
            ) : detailError ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#dc2626' }}>
                <p>{detailError}</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
                {/* Readiness Score Box */}
                <div
                  style={{
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(59, 130, 246, 0.06) 100%)',
                    border: '1px solid #e2e8f0',
                    borderRadius: '16px',
                    padding: '1.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)' }}>
                      OVERALL READINESS SCORE
                    </span>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.2rem' }}>
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem', fontWeight: 900, color: selectedCandidate.overall_skill_score !== null ? '#2563eb' : 'var(--text-muted)', lineHeight: 1 }}>
                        {selectedCandidate.overall_skill_score !== null ? selectedCandidate.overall_skill_score : '—'}
                      </span>
                      <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 700 }}>/ 100</span>
                    </div>
                  </div>
                  <span className="badge badge-SECURITY">Deterministic Composite</span>
                </div>

                {/* 5-Tile Quick Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                  <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Total Points</div>
                    <strong style={{ fontSize: '1.15rem', color: '#2563eb' }}>{selectedCandidate.metrics?.total_points ?? 0}</strong>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Solved</div>
                    <strong style={{ fontSize: '1.15rem', color: '#059669' }}>{selectedCandidate.metrics?.challenges_completed ?? 0}</strong>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '12px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Avg Score</div>
                    <strong style={{ fontSize: '1.15rem', color: '#d97706' }}>{selectedCandidate.metrics?.average_score ?? '—'}</strong>
                  </div>
                </div>

                {/* Skill Dimensions */}
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '0.85rem' }}>
                    🎯 Skill Dimensions
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {SKILL_DIMENSIONS.map((dim) => {
                      const sData = selectedCandidate.skills?.[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
                      const isMeas = sData.status === 'measured' && sData.score !== null;

                      return (
                        <div key={dim.key} style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                              <span>{dim.icon}</span>
                              <strong style={{ fontSize: '0.88rem' }}>{dim.name}</strong>
                            </div>
                            {isMeas ? (
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: dim.color, fontSize: '0.88rem' }}>
                                {sData.score}/100 ({sData.sample_size} evals)
                              </span>
                            ) : (
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Not Measured</span>
                            )}
                          </div>
                          <AnimatedProgress value={isMeas ? sData.score : 0} color={dim.color} height={6} />
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Challenge Evidence Timeline */}
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '0.85rem' }}>
                    ⚡ Challenge Evidence ({selectedCandidate.challenge_evidence?.length ?? 0})
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {selectedCandidate.challenge_evidence?.map((ev, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '0.75rem 1rem',
                          background: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          borderRadius: '10px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.88rem' }}>{ev.challenge_title}</div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            {ev.challenge_type?.replace('_', ' ')} • {ev.difficulty}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className={`badge ${ev.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.68rem' }}>
                            {ev.status}
                          </span>
                          <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.85rem', color: '#2563eb', marginTop: '0.2rem' }}>
                            {ev.score} pts
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Candidate Comparison Modal Matrix */}
      {showComparisonModal && (
        <div className="recruiter-drawer-overlay" onClick={() => setShowComparisonModal(false)}>
          <div
            className="card"
            style={{
              maxWidth: '1000px',
              width: '95%',
              margin: 'auto',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '2.5rem',
              borderRadius: '24px',
              boxShadow: 'var(--shadow-xl)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0 }}>
                  Candidate Comparison Matrix
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: '0.2rem 0 0' }}>
                  Side-by-side engineering readiness comparison
                </p>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowComparisonModal(false)}
                style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem' }}
              >
                ✕ Close
              </button>
            </div>

            {comparingLoading ? (
              <div style={{ padding: '4rem 0' }}>
                <Loading message="Fetching candidate comparison data..." />
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th style={{ width: '180px' }}>Metric / Skill</th>
                      {comparisonDetails.map((c) => (
                        <th key={c.username} style={{ textAlign: 'center' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                            <div className="candidate-avatar">
                              {c.username.substring(0, 2).toUpperCase()}
                            </div>
                            <strong style={{ fontSize: '0.95rem' }}>@{c.username}</strong>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Readiness Score</strong></td>
                      {comparisonDetails.map((c) => (
                        <td key={c.username} style={{ textAlign: 'center', fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.25rem', color: '#2563eb' }}>
                          {c.overall_skill_score ?? '—'}/100
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Total Points</strong></td>
                      {comparisonDetails.map((c) => (
                        <td key={c.username} style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                          {c.metrics?.total_points ?? 0}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Solved Challenges</strong></td>
                      {comparisonDetails.map((c) => (
                        <td key={c.username} style={{ textAlign: 'center' }}>
                          <span className="badge badge-BUG_FIX">{c.metrics?.challenges_completed ?? 0}</span>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Avg Challenge Score</strong></td>
                      {comparisonDetails.map((c) => (
                        <td key={c.username} style={{ textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
                          {c.metrics?.average_score ?? '—'}
                        </td>
                      ))}
                    </tr>
                    {SKILL_DIMENSIONS.map((dim) => (
                      <tr key={dim.key}>
                        <td>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <span>{dim.icon}</span> {dim.name}
                          </span>
                        </td>
                        {comparisonDetails.map((c) => {
                          const sData = c.skills?.[dim.key];
                          const hasScore = sData?.status === 'measured' && sData.score !== null;
                          return (
                            <td key={c.username} style={{ textAlign: 'center' }}>
                              {hasScore ? (
                                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: dim.color }}>
                                  {sData.score}%
                                </span>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
