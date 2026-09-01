import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSubmissions } from '../api/submissions';
import Loading from '../components/Loading';

const STATUS_FILTERS = [
  { label: 'All Statuses', value: '' },
  { label: 'Passed', value: 'PASSED' },
  { label: 'Failed', value: 'FAILED' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Error', value: 'ERROR' },
];

export default function SubmissionHistory() {
  const [submissions, setSubmissions] = useState([]);
  const [count, setCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const pageSize = 10;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getSubmissions({
      status: statusFilter,
      page,
      page_size: pageSize,
    })
      .then((data) => {
        if (!isMounted) return;
        setSubmissions(data.results || []);
        setCount(data.count || 0);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load submission history.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [statusFilter, page]);

  const totalPages = Math.ceil(count / pageSize);

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Submission History</h1>
          <p className="page-description">
            Track and review all your coding challenge evaluation attempts and scores.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Status:</label>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div className="results-count">
          {count} {count === 1 ? 'submission' : 'submissions'} found
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <Loading message="Loading submission history..." />
      ) : error ? (
        <div className="error-box">
          <p>{error}</p>
        </div>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">&lt;/&gt;</div>
          <h3>No submissions yet</h3>
          <p>You have not submitted any solutions under this filter criteria.</p>
          <div style={{ marginTop: '1.25rem' }}>
            <Link to="/challenges" className="btn btn-primary">
              Explore Challenges
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {submissions.map((sub) => {
              const evalSummary = sub.evaluation;
              return (
                <div
                  key={sub.id}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <Link
                        to={`/challenges/${sub.challenge}`}
                        style={{
                          fontSize: '1.1rem',
                          fontWeight: '700',
                          color: 'var(--text-primary)',
                        }}
                      >
                        {sub.challenge_title || `Challenge #${sub.challenge}`}
                      </Link>
                      <span className={`badge badge-${sub.status}`}>{sub.status}</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span
                        style={{
                          fontSize: '1rem',
                          fontWeight: '700',
                          color: sub.status === 'PASSED' ? '#3fb950' : 'var(--text-primary)',
                        }}
                      >
                        Score: {sub.score} pts
                      </span>
                      <Link
                        to={`/workspace/${sub.challenge}`}
                        className="btn btn-secondary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                      >
                        Open Workspace &rarr;
                      </Link>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '1.5rem',
                      fontSize: '0.82rem',
                      color: 'var(--text-muted)',
                      borderTop: '1px solid var(--border-color)',
                      paddingTop: '0.6rem',
                    }}
                  >
                    <span>
                      Language: <strong style={{ color: 'var(--text-secondary)' }}>{sub.language}</strong>
                    </span>
                    {evalSummary && (
                      <>
                        <span>
                          Tests:{' '}
                          <strong
                            style={{
                              color:
                                evalSummary.tests_passed === evalSummary.tests_total
                                  ? '#3fb950'
                                  : '#f85149',
                            }}
                          >
                            {evalSummary.tests_passed} / {evalSummary.tests_total} passed
                          </strong>
                        </span>
                        <span>
                          Execution Time:{' '}
                          <strong style={{ color: 'var(--text-secondary)' }}>
                            {evalSummary.execution_time ? `${evalSummary.execution_time.toFixed(3)}s` : '0.000s'}
                          </strong>
                        </span>
                      </>
                    )}
                    <span>
                      Submitted: <strong style={{ color: 'var(--text-secondary)' }}>{formatTimestamp(sub.created_at)}</strong>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                &larr; Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
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
