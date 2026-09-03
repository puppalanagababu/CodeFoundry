import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getChallenges, getChallengeProgress } from '../api/challenges';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';
import ScratchIntroOverlay from '../components/motion/ScratchIntroOverlay';

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

  // Scratch Me Entrance Experience State (Session-aware)
  const [showIntro, setShowIntro] = useState(() => {
    try {
      return !sessionStorage.getItem('devforge_challenges_intro_seen');
    } catch {
      return true;
    }
  });

  const handleIntroComplete = () => {
    try {
      sessionStorage.setItem('devforge_challenges_intro_seen', 'true');
    } catch {
      // Ignore
    }
    setShowIntro(false);
  };

  const handleReplayIntro = () => {
    try {
      sessionStorage.removeItem('devforge_challenges_intro_seen');
    } catch {
      // Ignore
    }
    setShowIntro(true);
  };

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
          (progressData.challenges || []).forEach((item) => {
            map[item.challenge_id] = item;
          });
          setProgressMap(map);
        }

        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load challenges.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [search, difficulty, challengeType, page]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleDifficultyChange = (e) => {
    setDifficulty(e.target.value);
    setPage(1);
  };

  const handleTypeChange = (e) => {
    setChallengeType(e.target.value);
    setPage(1);
  };

  const totalPages = Math.ceil(count / pageSize) || 1;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1200px' }}>
      {/* Interactive "Scratch Me" Overlay Entrance */}
      {showIntro && <ScratchIntroOverlay onComplete={handleIntroComplete} />}

      {/* Header Framed in Gency Style */}
      <div
        className="gency-frame animate-fade-in-up"
        style={{
          padding: '2rem 2.5rem',
          marginBottom: '2rem',
          background: 'linear-gradient(180deg, rgba(24, 34, 54, 0.75) 0%, rgba(14, 20, 32, 0.9) 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <h1 className="page-title" style={{ margin: 0, fontSize: '2rem' }}>Engineering Mission Catalog</h1>
          <p className="page-description" style={{ marginTop: '0.4rem', marginBottom: 0 }}>
            Choose an engineering scenario to practice debugging, API architecture, security hardening, or performance tuning.
          </p>
        </div>

        <div>
          <button
            type="button"
            onClick={handleReplayIntro}
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem', padding: '0.45rem 0.95rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
            title="Replay Scratch Discovery Experience"
          >
            <span>✨</span>
            <span>Replay Intro</span>
          </button>
        </div>
      </div>

      {/* Progress Overview Banner */}
      {progressSummary && progressSummary.total_challenges > 0 && (
        <div className="gency-frame animate-fade-in-up stagger-1" style={{ padding: '1.25rem 1.75rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.65rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', fontFamily: 'var(--font-display)' }}>
                Your Engineering Progress
              </span>
              <span className="status-pill status-passed">
                <span className="status-dot" />
                <span>
                  <AnimatedCounter value={progressSummary.completed_challenges} duration={700} /> / {progressSummary.total_challenges} Solved
                </span>
              </span>
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Overall Completion: <strong style={{ color: '#fff' }}><AnimatedCounter value={progressSummary.completion_percentage} suffix="%" duration={900} /></strong>
            </span>
          </div>

          <AnimatedProgress
            value={progressSummary.completion_percentage}
            max={100}
            height={8}
            color="var(--accent-primary)"
          />
        </div>
      )}

      {/* Filter & Search Bar */}
      <div
        className="gency-frame animate-fade-in-up stagger-2"
        style={{
          padding: '1.25rem 1.5rem',
          marginBottom: '2.25rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ flex: '1 1 280px', minWidth: '220px' }}>
          <input
            type="text"
            className="input-control"
            placeholder="🔍 Search challenges by title, keyword, or concept..."
            value={search}
            onChange={handleSearchChange}
            style={{ borderRadius: 'var(--radius-full)', padding: '0.6rem 1.25rem' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            className="select-control"
            value={difficulty}
            onChange={handleDifficultyChange}
            style={{ width: 'auto', minWidth: '155px', borderRadius: 'var(--radius-full)', padding: '0.6rem 1.25rem' }}
          >
            {DIFFICULTIES.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>

          <select
            className="select-control"
            value={challengeType}
            onChange={handleTypeChange}
            style={{ width: 'auto', minWidth: '160px', borderRadius: 'var(--radius-full)', padding: '0.6rem 1.25rem' }}
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
              onClick={() => {
                setSearch('');
                setDifficulty('');
                setChallengeType('');
                setPage(1);
              }}
              style={{ borderRadius: 'var(--radius-full)', padding: '0.55rem 1rem', fontSize: '0.85rem' }}
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Challenges Grid / Status */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Fetching engineering challenges..." />
        </div>
      ) : error ? (
        <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', color: '#f87171', borderRadius: 'var(--radius-md)', padding: '1.25rem', textAlign: 'center' }}>
          <p>{error}</p>
        </div>
      ) : challenges.length === 0 ? (
        <div className="gency-frame animate-scale-in" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔍</div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', color: '#fff', marginBottom: '0.5rem' }}>
            No challenges match your criteria
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '400px', margin: '0 auto 1.5rem' }}>
            Try clearing filters or searching with different engineering keywords.
          </p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setSearch('');
              setDifficulty('');
              setChallengeType('');
            }}
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <>
          <div className="challenges-grid">
            {challenges.map((c, idx) => {
              const prog = progressMap[c.id];
              const isCompleted = prog?.is_completed || prog?.status === 'PASSED';
              const hasAttempted = prog && prog.attempts_count > 0;

              return (
                <Link
                  key={c.id}
                  to={`/challenges/${c.id}`}
                  className={`challenge-card gency-frame animate-fade-in-up stagger-${(idx % 8) + 1}`}
                  style={{ textDecoration: 'none' }}
                >
                  <div className="challenge-card-header">
                    <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap', alignItems: 'center' }}>
                      <span className={`badge badge-${c.difficulty}`}>{c.difficulty}</span>
                      <span className={`badge badge-${c.challenge_type}`}>
                        {c.challenge_type?.replace('_', ' ')}
                      </span>
                    </div>

                    {isCompleted ? (
                      <span className="status-pill status-passed" title="Challenge Passed">
                        <span className="status-dot" />
                        <span>Solved</span>
                      </span>
                    ) : hasAttempted ? (
                      <span className="status-pill status-pending" title="In Progress">
                        <span className="status-dot" />
                        <span>Attempted</span>
                      </span>
                    ) : null}
                  </div>

                  <div>
                    <h3 className="challenge-title" style={{ marginBottom: '0.45rem' }}>
                      {c.title}
                    </h3>
                    <p className="challenge-description">
                      {c.description}
                    </p>
                  </div>

                  <div className="challenge-card-footer">
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <span className="badge badge-lang">{c.programming_language}</span>
                      {c.repository_structure && (
                        <span className="badge badge-type" style={{ fontSize: '0.68rem' }}>
                          Multi-File
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700, color: '#fff', fontFamily: 'var(--font-mono)' }}>
                      <span>{c.points} pts</span>
                      <span className="btn-arrow-icon" style={{ color: 'var(--accent-blue)', fontSize: '0.9rem' }}>↗</span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginTop: '2.5rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                style={{ padding: '0.45rem 1rem', fontSize: '0.85rem', borderRadius: 'var(--radius-full)' }}
              >
                &larr; Previous
              </button>
              <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                Page <strong style={{ color: '#fff' }}>{page}</strong> of <strong style={{ color: '#fff' }}>{totalPages}</strong>
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                style={{ padding: '0.45rem 1rem', fontSize: '0.85rem', borderRadius: 'var(--radius-full)' }}
              >
                Next &rarr;
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
