import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getChallenges } from '../api/challenges';
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

  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [challengeType, setChallengeType] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getChallenges({
      search,
      difficulty,
      challenge_type: challengeType,
      page,
      page_size: pageSize,
    })
      .then((data) => {
        if (!isMounted) return;
        if (data && data.results) {
          setChallenges(data.results);
          setCount(data.count || 0);
        } else if (Array.isArray(data)) {
          setChallenges(data);
          setCount(data.length);
        } else {
          setChallenges([]);
          setCount(0);
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
      <div className="page-header">
        <h1 className="page-title">Engineering Challenges</h1>
        <p className="page-subtitle">Select a coding challenge to begin practicing.</p>
      </div>

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
            {challenges.map((challenge) => (
              <Link
                key={challenge.id}
                to={`/challenges/${challenge.id}`}
                className="challenge-card"
              >
                <div className="challenge-card-header">
                  <span className="challenge-card-title">{challenge.title}</span>
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
                  <span>Score: {challenge.points} pts</span>
                  <span>View Details &rarr;</span>
                </div>
              </Link>
            ))}
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
