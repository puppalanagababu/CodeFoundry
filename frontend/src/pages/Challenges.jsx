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
  { label: 'All Types', value: '' },
  { label: 'Bug Fix', value: 'BUG_FIX' },
  { label: 'Feature', value: 'FEATURE' },
  { label: 'API Integration', value: 'API' },
  { label: 'Database', value: 'DATABASE' },
  { label: 'Performance', value: 'PERFORMANCE' },
  { label: 'Security', value: 'SECURITY' },
  { label: 'Testing', value: 'TESTING' },
  { label: 'Code Review', value: 'CODE_REVIEW' },
  { label: 'Debugging', value: 'DEBUGGING' },
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
  const pageSize = 10;

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
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h1 className="page-title">Engineering Challenges</h1>
          <p className="page-subtitle">Select a coding challenge to begin practicing in the Docker sandbox.</p>
        </div>
      </div>

      {/* Progress Overview Banner */}
      {progressSummary && progressSummary.total_challenges > 0 && (
        <div
          style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1.1rem 1.4rem',
            marginBottom: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Your Challenge Progress
              </span>
              <span
                style={{
                  fontSize: '0.8rem',
                  padding: '0.15rem 0.55rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(63, 185, 80, 0.15)',
                  color: '#3fb950',
                  fontWeight: '600',
                }}
              >
                {progressSummary.completed_challenges} / {progressSummary.total_challenges} Challenges Solved
              </span>
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
              {progressSummary.completion_percentage}% Complete
            </span>
          </div>

          <div
            style={{
              height: '6px',
              backgroundColor: 'var(--bg-tertiary)',
              borderRadius: '3px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${Math.min(100, Math.max(0, progressSummary.completion_percentage))}%`,
                backgroundColor: '#3fb950',
                borderRadius: '3px',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>
      )}

      <div className="filter-bar">
        <input
          type="text"
          className="input-control filter-search"
          placeholder="Search by title, description, or slug..."
          value={search}
          onChange={handleSearchChange}
        />

        <select
          className="select-control"
          value={difficulty}
          onChange={handleDifficultyChange}
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
        >
          {CHALLENGE_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <Loading message="Loading challenges..." />}

      {error && (
        <div className="error-box">
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && challenges.length === 0 && (
        <div className="empty-box">
          <p>No active challenges match your filter criteria.</p>
        </div>
      )}

      {!loading && !error && challenges.length > 0 && (
        <>
          <div className="challenge-list">
            {challenges.map((challenge) => {
              const itemProgress = progressMap[challenge.id];
              const statusStr = itemProgress ? itemProgress.status : 'NOT_ATTEMPTED';
              const hasPassed = statusStr === 'PASSED';
              const hasFailed = statusStr === 'FAILED';
              const bestScore = itemProgress?.best_score;
              const attemptsCount = itemProgress?.attempts_count || 0;

              return (
                <Link
                  key={challenge.id}
                  to={`/challenges/${challenge.id}`}
                  className="challenge-card"
                >
                  <div className="challenge-card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                      <span className="challenge-card-title">{challenge.title}</span>
                      {hasPassed ? (
                        <span className="badge badge-PASSED" style={{ fontSize: '0.7rem' }}>
                          Completed
                        </span>
                      ) : hasFailed ? (
                        <span className="badge badge-FAILED" style={{ fontSize: '0.7rem' }}>
                          Attempted
                        </span>
                      ) : (
                        <span
                          className="badge"
                          style={{
                            fontSize: '0.7rem',
                            backgroundColor: 'var(--bg-tertiary)',
                            color: 'var(--text-muted)',
                          }}
                        >
                          Not Attempted
                        </span>
                      )}
                    </div>

                    <div className="challenge-card-badges">
                      <span className={`badge badge-${challenge.difficulty}`}>
                        {challenge.difficulty}
                      </span>
                      <span className="badge badge-type">
                        {challenge.challenge_type.replace('_', ' ')}
                      </span>
                      <span className="badge badge-lang">
                        {challenge.programming_language}
                      </span>
                    </div>
                  </div>

                  <p className="challenge-card-desc">{challenge.description}</p>

                  <div className="challenge-card-footer">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem' }}>
                      {bestScore !== null && bestScore !== undefined ? (
                        <span style={{ color: hasPassed ? '#3fb950' : 'var(--text-primary)', fontWeight: '600' }}>
                          Best Score: {bestScore} / {challenge.points} pts
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Score: {challenge.points} pts</span>
                      )}

                      {attemptsCount > 0 && (
                        <span style={{ color: 'var(--text-muted)' }}>
                          {attemptsCount} {attemptsCount === 1 ? 'attempt' : 'attempts'}
                        </span>
                      )}
                    </div>

                    <span>View Details &rarr;</span>
                  </div>
                </Link>
              );
            })}
          </div>

          {totalPages > 1 && (
            <div className="pagination-controls">
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                &larr; Previous
              </button>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Page {page} of {totalPages} ({count} challenges)
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
