import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getChallenges, getChallengeProgress } from '../api/challenges';
import Loading from '../components/Loading';
import { Search, SearchX, AlertTriangle, Terminal, Award, CheckCircle2, Clock } from 'lucide-react';

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
      {/* 1. Header Banner in Soft Pastel Blue */}
      <div
        className="card panel-pastel-blue animate-fade-in-up"
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
              <span className="badge badge-API" style={{ fontSize: '0.76rem' }}>
                Engineering Sandbox
              </span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Production Scenarios
              </span>
            </div>
            <h1 className="page-title" style={{ margin: 0, fontSize: '2.2rem' }}>
              Engineering Challenges
            </h1>
            <p className="page-description" style={{ marginTop: '0.4rem', marginBottom: 0, maxWidth: '640px' }}>
              Solve real bugs, optimize quadratic algorithms, and remediate security vulnerabilities in authentic multi-file codebases.
            </p>
          </div>

          {progressSummary && (
            <div style={{ display: 'flex', gap: '1.5rem', background: '#ffffff', padding: '1rem 1.75rem', borderRadius: '18px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.04em' }}>
                  Passed
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', fontWeight: 800, color: 'var(--pastel-mint-text)' }}>
                  {progressSummary.passed}
                </div>
              </div>
              <div style={{ width: '1px', backgroundColor: 'var(--border-color)' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.04em' }}>
                  Attempted
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.6rem', fontWeight: 800, color: 'var(--pastel-blue-text)' }}>
                  {progressSummary.attempted}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. Filter Toolbar */}
      <div className="recruiter-filter-toolbar" style={{ marginBottom: '2.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div className="recruiter-search-box" style={{ flex: 1, minWidth: '280px', position: 'relative' }}>
          <span className="search-icon" style={{ position: 'absolute', left: '1.1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center' }}>
            <Search size={16} />
          </span>
          <input
            type="text"
            className="input-control"
            style={{ paddingLeft: '2.75rem', borderRadius: 'var(--radius-full)' }}
            placeholder="Search challenges by title, keywords..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="recruiter-filter-selects" style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <select
            className="select-control"
            style={{ borderRadius: 'var(--radius-full)', padding: '0.75rem 1.25rem', width: 'auto', cursor: 'pointer' }}
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
            className="select-control"
            style={{ borderRadius: 'var(--radius-full)', padding: '0.75rem 1.25rem', width: 'auto', cursor: 'pointer' }}
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
              style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* 3. Challenge Cards Grid */}
      {loading ? (
        <div style={{ padding: '4rem 1.5rem' }}>
          <Loading message="Scanning challenge repository catalog..." />
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', margin: '2rem 0', borderRadius: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <AlertTriangle size={48} color="#D93847" />
          </div>
          <h2 style={{ fontSize: '1.3rem', color: 'var(--accent-danger)', marginBottom: '0.5rem' }}>Failed to Load Challenges</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
            Reset Filters
          </button>
        </div>
      ) : challenges.length === 0 ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <SearchX size={48} color="var(--text-muted)" />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.5rem' }}>No Challenges Found</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
            No engineering challenges match your search criteria. Try modifying your search or clearing filters.
          </p>
          <button type="button" className="btn btn-primary" onClick={handleClearFilters}>
            Clear Filters
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.75rem' }}>
          {challenges.map((ch, idx) => {
            const prog = progressMap[ch.id];
            const isPassed = prog?.status === 'PASSED';
            const isAttempted = prog?.status === 'ATTEMPTED';

            return (
              <div
                key={ch.id}
                className={`card animate-fade-in-up stagger-${(idx % 6) + 1}`}
                style={{
                  padding: '2rem',
                  borderRadius: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '1.35rem',
                  border: isPassed ? '1px solid var(--pastel-mint-border)' : '1px solid var(--border-color)',
                  background: isPassed ? 'linear-gradient(180deg, #FFFFFF 0%, #FAFEFC 100%)' : '#FFFFFF',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <span className={`badge badge-${ch.challenge_type || 'API'}`}>
                      {ch.challenge_type ? ch.challenge_type.replace('_', ' ') : 'Challenge'}
                    </span>
                    <span className={`badge badge-${ch.difficulty || 'BEGINNER'}`}>
                      {ch.difficulty}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.65rem', lineHeight: 1.3 }}>
                    <Link to={`/challenges/${ch.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                      {ch.title}
                    </Link>
                  </h3>

                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.55, margin: 0, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {ch.short_description || ch.description}
                  </p>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.85rem 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                      <Terminal size={14} color="#3B82F6" /> {ch.language || 'Python'}
                    </span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                      <Award size={14} color="#C77A14" /> {ch.points || 100} pts
                    </span>
                    {isPassed ? (
                      <span style={{ color: 'var(--pastel-mint-text)', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle2 size={13} /> Solved
                      </span>
                    ) : isAttempted ? (
                      <span style={{ color: 'var(--pastel-peach-text)', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={13} /> Attempted
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Unattempted</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <Link
                      to={`/challenges/${ch.id}`}
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '0.65rem', fontSize: '0.88rem' }}
                    >
                      Briefing
                    </Link>
                    <Link
                      to={`/workspace/${ch.id}`}
                      className="btn-saas btn-saas-primary"
                      style={{ flex: 1, padding: '0.65rem', fontSize: '0.88rem' }}
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

      {/* 4. Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.85rem', marginTop: '3.5rem' }}>
          <button
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.88rem' }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 700, padding: '0.4rem 0.8rem', background: '#ffffff', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-color)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.88rem' }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
