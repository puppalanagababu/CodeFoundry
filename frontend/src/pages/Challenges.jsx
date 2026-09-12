import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getChallenges, getChallengeProgress } from '../api/challenges';
import Loading from '../components/Loading';

const DIFFICULTIES = [
  { label: 'All Difficulties', value: '' },
  { label: 'Beginner', value: 'BEGINNER' },
  { label: 'Intermediate', value: 'INTERMEDIATE' },
  { label: 'Advanced', value: 'ADVANCED' },
  { label: 'Expert', value: 'EXPERT' },
];

const CHALLENGE_TYPES = [
  { label: 'All Categories', value: '' },
  { label: 'Bug Fix', value: 'BUG_FIX' },
  { label: 'API Integration', value: 'API' },
  { label: 'Security', value: 'SECURITY' },
  { label: 'Performance', value: 'PERFORMANCE' },
  { label: 'Database', value: 'DATABASE' },
  { label: 'Testing', value: 'TESTING' },
];

export default function Challenges() {
  const [challenges, setChallenges] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [progressSummary, setProgressSummary] = useState(null);
  const [progressMap, setProgressMap] = useState({});

  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [challengeType, setChallengeType] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getChallenges({
        search,
        difficulty,
        challenge_type: challengeType,
        page,
        page_size: pageSize,
      }),
      getChallengeProgress().catch(() => null),
    ])
      .then(([challengesData, progressData]) => {
        if (!isMounted) return;

        if (challengesData && challengesData.results) {
          setChallenges(challengesData.results);
          setCount(challengesData.count || 0);
        } else if (Array.isArray(challengesData)) {
          setChallenges(challengesData);
          setCount(challengesData.length);
        } else {
          setChallenges([]);
          setCount(0);
        }

        if (progressData && progressData.summary) {
          setProgressSummary(progressData.summary);
          const map = {};
          (progressData.challenges || []).forEach((p) => {
            map[p.challenge_id] = p;
          });
          setProgressMap(map);
        }

        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load challenge library.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [search, difficulty, challengeType, page]);

  const totalPages = Math.ceil(count / pageSize) || 1;

  const handleClearFilters = () => {
    setSearch('');
    setDifficulty('');
    setChallengeType('');
    setPage(1);
  };

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1240px' }}>
      {/* Header Banner */}
      <div
        className="card animate-fade-in-up"
        style={{
          padding: '2.5rem',
          marginBottom: '2.5rem',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)',
          borderRadius: '24px',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <span className="badge badge-API" style={{ fontSize: '0.75rem' }}>
                Engineering Sandbox
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Production Scenarios
              </span>
            </div>
            <h1 className="page-title" style={{ margin: 0, fontSize: '2.2rem' }}>
              Engineering Challenges
            </h1>
            <p className="page-description" style={{ marginTop: '0.4rem', marginBottom: 0 }}>
              Solve production bugs, optimize slow endpoints, and secure vulnerable services in real multi-file codebases.
            </p>
          </div>

          {progressSummary && (
            <div style={{ display: 'flex', gap: '1.5rem', background: '#ffffff', padding: '1rem 1.5rem', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
                  Passed
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 800, color: '#10b981' }}>
                  {progressSummary.passed}
                </div>
              </div>
              <div style={{ width: '1px', backgroundColor: '#e2e8f0' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
                  Attempted
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 800, color: '#2563eb' }}>
                  {progressSummary.attempted}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="recruiter-filter-toolbar" style={{ marginBottom: '2.5rem' }}>
        <div className="recruiter-search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="recruiter-input"
            placeholder="Search challenges by title, keywords..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="recruiter-filter-selects">
          <select
            className="recruiter-select"
            value={difficulty}
            onChange={(e) => {
              setDifficulty(e.target.value);
              setPage(1);
            }}
          >
            {DIFFICULTIES.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>

          <select
            className="recruiter-select"
            value={challengeType}
            onChange={(e) => {
              setChallengeType(e.target.value);
              setPage(1);
            }}
          >
            {CHALLENGE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>

          {(search || difficulty || challengeType) && (
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

      {/* Challenges Grid */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Loading challenge catalog..." />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', margin: '2rem 0' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.3rem', color: '#ef4444', marginBottom: '0.5rem' }}>Failed to Load Challenges</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
            Reset Filters
          </button>
        </div>
      ) : challenges.length === 0 ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🔍</span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.5rem' }}>No Challenges Found</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
            No engineering challenges match your search criteria. Try modifying your search or clearing filters.
          </p>
          <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
            Clear Filters
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.75rem' }}>
          {challenges.map((ch, idx) => {
            const prog = progressMap[ch.id];
            const isPassed = prog?.status === 'PASSED';
            const isAttempted = prog?.status === 'ATTEMPTED';

            return (
              <div
                key={ch.id}
                className={`card animate-fade-in-up stagger-${(idx % 6) + 1}`}
                style={{
                  padding: '1.75rem',
                  borderRadius: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '1.25rem',
                  border: isPassed ? '1px solid #a7f3d0' : '1px solid #e2e8f0',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                    <span className={`badge badge-${ch.challenge_type || 'API'}`}>
                      {ch.challenge_type ? ch.challenge_type.replace('_', ' ') : 'Challenge'}
                    </span>
                    <span className={`badge badge-${ch.difficulty || 'BEGINNER'}`}>
                      {ch.difficulty}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.6rem', lineHeight: 1.3 }}>
                    <Link to={`/challenges/${ch.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                      {ch.title}
                    </Link>
                  </h3>

                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5, margin: 0, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {ch.short_description || ch.description}
                  </p>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderTop: '1px solid #f1f5f9', borderBottom: '1px solid #f1f5f9', marginBottom: '1rem', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
                    <span>💻 {ch.language || 'Python'}</span>
                    <span>🏆 {ch.points || 100} pts</span>
                    {isPassed ? (
                      <span style={{ color: '#059669', fontWeight: 700 }}>✓ Solved</span>
                    ) : isAttempted ? (
                      <span style={{ color: '#d97706', fontWeight: 700 }}>● Attempted</span>
                    ) : (
                      <span>Unattempted</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <Link
                      to={`/challenges/${ch.id}`}
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '0.6rem', fontSize: '0.85rem' }}
                    >
                      Briefing
                    </Link>
                    <Link
                      to={`/workspace/${ch.id}`}
                      className="btn-saas btn-saas-primary"
                      style={{ flex: 1, padding: '0.6rem', fontSize: '0.85rem' }}
                    >
                      <span>Solve</span>
                      <span className="btn-arrow-icon">→</span>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginTop: '3.5rem' }}>
          <button
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
