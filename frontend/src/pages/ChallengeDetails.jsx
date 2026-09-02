import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { getChallengeSubmissions } from '../api/submissions';
import Loading from '../components/Loading';

export default function ChallengeDetails() {
  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [attemptsData, setAttemptsData] = useState({ results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getChallenge(id),
      getChallengeSubmissions(id, { page_size: 5 }).catch(() => ({ results: [], count: 0 })),
    ])
      .then(([challengeRes, attemptsRes]) => {
        if (!isMounted) return;
        setChallenge(challengeRes);
        setAttemptsData(attemptsRes || { results: [], count: 0 });
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load challenge details.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="detail-container">
        <Loading message="Loading challenge details..." />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="detail-container">
        <div className="error-box">
          <p>{error || 'Challenge not found.'}</p>
          <div style={{ marginTop: '1rem' }}>
            <Link to="/challenges" className="btn btn-secondary">
              &larr; Back to Challenges
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const hasAttempts = attemptsData.count > 0;
  const hasPassed = attemptsData.results.some((item) => item.status === 'PASSED');
  const bestScore = hasAttempts
    ? Math.max(...attemptsData.results.map((item) => (typeof item.score === 'number' ? item.score : 0)))
    : null;

  return (
    <div className="detail-container">
      <div className="detail-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <Link to="/challenges" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'inline-block' }}>
            &larr; All Challenges
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h1 className="page-title" style={{ margin: 0 }}>{challenge.title}</h1>
            {hasPassed ? (
              <span className="badge badge-PASSED" style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}>
                Solved · Best Score: {bestScore}/{challenge.points} · {attemptsData.count} {attemptsData.count === 1 ? 'attempt' : 'attempts'}
              </span>
            ) : hasAttempts ? (
              <span className="badge badge-FAILED" style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}>
                Attempted · Best Score: {bestScore}/{challenge.points} · {attemptsData.count} {attemptsData.count === 1 ? 'attempt' : 'attempts'}
              </span>
            ) : (
              <span
                className="badge"
                style={{
                  fontSize: '0.8rem',
                  padding: '0.2rem 0.6rem',
                  backgroundColor: 'var(--bg-tertiary)',
                  color: 'var(--text-muted)',
                }}
              >
                Not Attempted
              </span>
            )}
          </div>
        </div>

        <Link to={`/workspace/${challenge.id}`} className="btn btn-primary" style={{ padding: '0.65rem 1.4rem' }}>
          Open Workspace &rarr;
        </Link>
      </div>

      <div className="detail-meta-grid">
        <div>
          <div className="meta-item-label">Difficulty</div>
          <span className={`badge badge-${challenge.difficulty}`}>
            {challenge.difficulty}
          </span>
        </div>
        <div>
          <div className="meta-item-label">Challenge Type</div>
          <span className="badge badge-type">
            {challenge.challenge_type.replace('_', ' ')}
          </span>
        </div>
        <div>
          <div className="meta-item-label">Language</div>
          <span className="meta-item-value">{challenge.programming_language}</span>
        </div>
        <div>
          <div className="meta-item-label">Points</div>
          <span className="meta-item-value">{challenge.points} pts</span>
        </div>
        <div>
          <div className="meta-item-label">Time Limit</div>
          <span className="meta-item-value">{challenge.time_limit}s</span>
        </div>
        <div>
          <div className="meta-item-label">Memory Limit</div>
          <span className="meta-item-value">{challenge.memory_limit} MB</span>
        </div>
      </div>

      {/* Your Attempts Summary */}
      <div className="detail-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h2 style={{ margin: 0 }}>Your Attempts</h2>
          {attemptsData.count > 0 && (
            <Link to="/submissions" style={{ fontSize: '0.82rem', color: 'var(--accent-blue)' }}>
              View all in Submission History &rarr;
            </Link>
          )}
        </div>

        {attemptsData.count === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
            You have not attempted this challenge yet. Open the workspace to start coding!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
              <span>
                Total Attempts: <strong style={{ color: 'var(--text-primary)' }}>{attemptsData.count}</strong>
              </span>
              <span>
                Best Score:{' '}
                <strong style={{ color: bestScore === challenge.points ? '#3fb950' : 'var(--text-primary)' }}>
                  {bestScore} / {challenge.points} pts
                </strong>
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {attemptsData.results.map((item, idx) => (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.5rem 0.75rem',
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.82rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ color: 'var(--text-muted)', minWidth: '70px' }}>
                      #{attemptsData.count - idx}
                    </span>
                    <span className={`badge badge-${item.status}`} style={{ fontSize: '0.68rem', padding: '0.1rem 0.4rem' }}>
                      {item.status}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                      {item.score} / {challenge.points} pts
                    </span>
                    <span style={{ color: 'var(--text-muted)' }}>
                      {item.submitted_at || item.created_at
                        ? new Date(item.submitted_at || item.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Challenge Description */}
      <div className="detail-section">
        <h2>Description</h2>
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
          {challenge.description}
        </div>
      </div>

      {/* Starter Code Preview */}
      {challenge.starter_code && (
        <div className="detail-section">
          <h2>Starter Code Preview</h2>
          <pre
            style={{
              backgroundColor: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              overflowX: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              color: '#58a6ff',
            }}
          >
            {challenge.starter_code}
          </pre>
        </div>
      )}

      {/* Public Test Cases */}
      {challenge.test_cases && challenge.test_cases.length > 0 && (
        <div className="detail-section">
          <h2>Sample Test Cases</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {challenge.test_cases.map((tc, index) => (
              <div
                key={tc.id || index}
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.75rem 1rem',
                }}
              >
                <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>
                  Test Case #{index + 1}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Input:</span>
                    <pre style={{ margin: '0.2rem 0', padding: '0.4rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px' }}>
                      {tc.input_data || '(empty)'}
                    </pre>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Expected Output:</span>
                    <pre style={{ margin: '0.2rem 0', padding: '0.4rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px' }}>
                      {tc.expected_output || '(empty)'}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
