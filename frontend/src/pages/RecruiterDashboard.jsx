import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getRecruiterCandidates, getRecruiterCandidate } from '../api/recruiter';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';
import {
  getSkillIcon,
  ShieldAlert,
  Search,
  Users,
  BarChart3,
  Award,
  CheckCircle2,
  Zap,
  AlertTriangle,
  RotateCcw,
  X,
} from '../components/RealisticIcons';

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
  { key: 'problem_solving', name: 'Problem Solving', color: '#6D45C5' },
  { key: 'debugging', name: 'Debugging', color: '#C77A14' },
  { key: 'security', name: 'Security', color: '#5B34B0' },
  { key: 'performance', name: 'Performance', color: '#21885B' },
  { key: 'code_quality', name: 'Code Quality', color: '#1E5EA8' },
  { key: 'testing', name: 'Testing', color: '#0F766E' },
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
        <div className="card panel-pastel-peach" style={{ padding: '3.5rem 2rem', borderRadius: '24px', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.25rem' }}>
            <ShieldAlert size={54} color="#D93847" />
          </div>
          <span className="badge badge-SECURITY" style={{ marginBottom: '1rem' }}>
            ACCESS RESTRICTED
          </span>
          <h1 style={{ fontSize: '1.9rem', fontWeight: 800, margin: '0.25rem 0 0.75rem', fontFamily: 'var(--font-display)' }}>
            Recruiter Access Required
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            Your account does not have <strong>Recruiter authorization</strong>. This talent evaluation terminal is reserved for verified engineering recruitment partners.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
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
      {/* 1. Header Banner */}
      <div className="recruiter-hero-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <span className="badge badge-SECURITY" style={{ fontSize: '0.74rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
              <Zap size={12} /> RECRUITER ASSESSMENT RADAR
            </span>
            <span style={{ fontSize: '0.78rem', color: 'var(--accent-success)', fontWeight: 700 }}>
              ● VERIFIED DOCKER SANDBOX EVIDENCE
            </span>
          </div>
          <h1 className="recruiter-dashboard-title">
            Recruiter Talent Terminal
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.96rem', margin: 0, fontWeight: 500 }}>
            Evaluate developer production readiness through verifiable engineering telemetry.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {comparisonList.length >= 2 && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleOpenComparison}
              style={{ padding: '0.75rem 1.6rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <span>Compare ({comparisonList.length})</span>
              <span>→</span>
            </button>
          )}

          <div className="recruiter-count-badge">
            <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-muted)' }}>
              ASSESSED CANDIDATES
            </span>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.2rem', fontWeight: 900, color: 'var(--accent-primary)', lineHeight: 1.1, margin: '0.2rem 0' }}>
              <AnimatedCounter value={candidates.length} />
            </div>
            <span style={{ fontSize: '0.74rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              Evaluated Engineers
            </span>
          </div>
        </div>
      </div>

      {/* 2. Filter Toolbar */}
      <div className="recruiter-filter-toolbar">
        <div className="recruiter-search-box">
          <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center' }}>
            <Search size={16} />
          </span>
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
              style={{ padding: '0.55rem 1.1rem', fontSize: '0.85rem' }}
            >
              ↻ Clear
            </button>
          )}
        </div>
      </div>

      {/* 3. Main Table Card */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Loading candidate assessments..." />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center', margin: '2rem 0', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <AlertTriangle size={48} color="var(--accent-danger)" />
          </div>
          <h2 style={{ fontSize: '1.3rem', color: 'var(--accent-danger)', marginBottom: '0.5rem', fontWeight: 800 }}>Failed to Load Candidates</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={fetchCandidates} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <RotateCcw size={14} /> Retry Request
          </button>
        </div>
      ) : candidates.length === 0 ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', borderRadius: '24px', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Users size={48} color="var(--text-muted)" />
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.4rem', fontFamily: 'var(--font-display)' }}>No Candidates Found</h2>
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
        <div className="card" style={{ padding: '1.75rem', borderRadius: '24px', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <BarChart3 size={18} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-display)' }}>
                Candidate Assessments ({candidates.length})
              </h2>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select checkbox to compare candidates side-by-side (up to 4)
            </span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '44px', textAlign: 'center' }}>Compare</th>
                  <th style={{ width: '50px', textAlign: 'center' }}>#</th>
                  <th>Candidate</th>
                  <th style={{ textAlign: 'center' }}>Readiness Score</th>
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
                          style={{ cursor: 'pointer', width: 17, height: 17, accentColor: 'var(--accent-primary)' }}
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
                              background: 'var(--pastel-lavender-light)',
                              color: 'var(--pastel-lavender-text)',
                              border: '1px solid var(--pastel-lavender-border)',
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
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-primary)' }}>
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
                      <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--pastel-lavender-text)', fontWeight: 700 }}>
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

      {/* 4. Candidate Assessment Drawer */}
      {selectedCandidate && (
        <div className="recruiter-drawer-overlay" onClick={handleCloseDetail}>
          <div className="recruiter-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="recruiter-drawer-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <div className="candidate-avatar-large">
                  {selectedCandidate.username.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-display)' }}>
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
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <X size={14} /> Close
              </button>
            </div>

            {detailLoading ? (
              <div style={{ padding: '4rem 0' }}>
                <Loading message={`Loading assessment for @${selectedCandidate.username}...`} />
              </div>
            ) : detailError ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-danger)' }}>
                <p>{detailError}</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
                {/* Readiness Score Box */}
                <div
                  className="panel-pastel-lavender"
                  style={{
                    borderRadius: '16px',
                    padding: '1.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--pastel-lavender-text)' }}>
                      OVERALL READINESS SCORE
                    </span>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.2rem' }}>
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 900, color: selectedCandidate.overall_skill_score !== null ? 'var(--pastel-lavender-text)' : 'var(--text-muted)', lineHeight: 1 }}>
                        {selectedCandidate.overall_skill_score !== null ? selectedCandidate.overall_skill_score : '—'}
                      </span>
                      <span style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 700 }}>/ 100</span>
                    </div>
                  </div>
                  <span className="badge badge-SECURITY">Deterministic Composite</span>
                </div>

                {/* 3-Tile Quick Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                  <div style={{ background: 'var(--bg-primary)', padding: '0.85rem', borderRadius: '12px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Total Points</div>
                    <strong style={{ fontSize: '1.2rem', color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>{selectedCandidate.metrics?.total_points ?? 0}</strong>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', padding: '0.85rem', borderRadius: '12px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Solved</div>
                    <strong style={{ fontSize: '1.2rem', color: 'var(--accent-success)', fontFamily: 'var(--font-mono)' }}>{selectedCandidate.metrics?.challenges_completed ?? 0}</strong>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', padding: '0.85rem', borderRadius: '12px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Avg Score</div>
                    <strong style={{ fontSize: '1.2rem', color: 'var(--accent-warning)', fontFamily: 'var(--font-mono)' }}>{selectedCandidate.metrics?.average_score ?? '—'}</strong>
                  </div>
                </div>

                {/* Skill Dimensions */}
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, marginBottom: '0.85rem', fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <BarChart3 size={18} color="var(--accent-primary)" />
                    <span>Verified Competency Matrix</span>
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {SKILL_DIMENSIONS.map((dim) => {
                      const sData = selectedCandidate.skills?.[dim.key] || { score: null, status: 'not_measured', sample_size: 0 };
                      const isMeas = sData.status === 'measured' && sData.score !== null;

                      return (
                        <div key={dim.key} style={{ padding: '0.85rem 1rem', background: 'var(--bg-primary)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                              <span style={{ display: 'inline-flex', alignItems: 'center' }}>{getSkillIcon(dim.key, 16, dim.color)}</span>
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
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, marginBottom: '0.85rem', fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Zap size={15} color="var(--accent-primary)" /> Challenge Evidence ({selectedCandidate.challenge_evidence?.length ?? 0})
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {selectedCandidate.challenge_evidence?.map((ev, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '0.75rem 1rem',
                          background: 'var(--bg-primary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{ev.challenge_title}</div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            {ev.challenge_type?.replace('_', ' ')} • {ev.difficulty}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className={`badge ${ev.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.68rem' }}>
                            {ev.status}
                          </span>
                          <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.85rem', color: 'var(--accent-primary)', marginTop: '0.2rem' }}>
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

      {/* 5. Candidate Comparison Modal Matrix */}
      {showComparisonModal && (
        <div className="recruiter-drawer-overlay" onClick={() => setShowComparisonModal(false)}>
          <div
            className="card animate-scale-in"
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-display)' }}>
                  Candidate Comparison Matrix
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: '0.2rem 0 0' }}>
                  Side-by-side engineering readiness telemetry comparison
                </p>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowComparisonModal(false)}
                style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <X size={14} /> Close
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
                        <td key={c.username} style={{ textAlign: 'center', fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: '1.3rem', color: 'var(--accent-primary)' }}>
                          {c.overall_skill_score ?? '—'}/100
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Total Points</strong></td>
                      {comparisonDetails.map((c) => (
                        <td key={c.username} style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-primary)' }}>
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
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ display: 'inline-flex', alignItems: 'center' }}>{getSkillIcon(dim.key, 15, dim.color)}</span>
                            <span>{dim.name}</span>
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
