import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSubmissions } from '../api/submissions';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';

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

  const totalPages = Math.ceil(count / pageSize) || 1;

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
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1100px' }}>
      <div className="gency-frame animate-fade-in-up" style={{ padding: '2rem 2.5rem', marginBottom: '2rem', background: 'linear-gradient(180deg, rgba(24, 34, 54, 0.75) 0%, rgba(14, 20, 32, 0.9) 100%)' }}>
        <h1 className="page-title" style={{ margin: 0, fontSize: '2rem' }}>Submission Archives</h1>
        <p className="page-description" style={{ marginTop: '0.4rem', marginBottom: 0 }}>
          Audit and review your automated Docker sandbox evaluation logs, test metrics, and scoring history.
        </p>
      </div>

      {/* Filter Bar */}
      <div
        className="gency-frame animate-fade-in-up stagger-1"
        style={{
          padding: '1.1rem 1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <label style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Filter by Status:</label>
          <select
            className="select-control"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            style={{ width: 'auto', minWidth: '150px', borderRadius: 'var(--radius-full)', padding: '0.55rem 1.25rem' }}
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <strong style={{ color: '#fff' }}>{count}</strong> {count === 1 ? 'submission' : 'submissions'} recorded
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <Loading message="Loading submission archive..." />
      ) : error ? (
        <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', color: '#f87171', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
          <p>{error}</p>
        </div>
      ) : submissions.length === 0 ? (
        <div className="gency-frame animate-scale-in" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', marginBottom: '1.25rem' }}>
            No submissions recorded under the selected filter criteria.
          </p>
          <Link to="/challenges" className="btn-gency btn-gency-primary">
            <span>Browse Mission Catalog</span>
            <span className="btn-arrow-icon">↗</span>
          </Link>
        </div>
      ) : (
        <div className="gency-frame animate-fade-in-up stagger-2" style={{ overflow: 'hidden' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {submissions.map((sub, idx) => (
              <div
                key={sub.id}
                className={`animate-fade-in-up stagger-${(idx % 8) + 1}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1.25rem 1.75rem',
                  borderBottom: idx < submissions.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.015)',
                  transition: 'background var(--transition-fast)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                    <Link
                      to={`/challenges/${sub.challenge_id || sub.challenge?.id || sub.challenge}`}
                      style={{ fontWeight: 600, color: '#fff', fontSize: '1.05rem', fontFamily: 'var(--font-display)' }}
                    >
                      {sub.challenge_title || sub.challenge?.title || `Challenge #${sub.challenge}`}
                    </Link>
                    <span className="badge badge-lang" style={{ borderRadius: 'var(--radius-full)' }}>{sub.language || 'Python'}</span>
                  </div>

                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Submission #{sub.id} · {formatTimestamp(sub.submitted_at)}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                  <span className={`status-pill ${sub.status === 'PASSED' ? 'status-passed' : sub.status === 'FAILED' ? 'status-failed' : 'status-pending'}`}>
                    <span className="status-dot" />
                    <span>{sub.status}</span>
                  </span>

                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.1rem', color: sub.score >= 80 ? '#10b981' : '#f59e0b', minWidth: '70px', textAlign: 'right' }}>
                    <AnimatedCounter value={sub.score || 0} duration={600} />/100
                  </span>

                  <Link
                    to={`/workspace/${sub.challenge_id || sub.challenge?.id || sub.challenge}`}
                    className="btn btn-secondary"
                    style={{ padding: '0.4rem 0.9rem', fontSize: '0.82rem', borderRadius: 'var(--radius-full)' }}
                  >
                    Open in Workspace
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '1.25rem',
                borderTop: '1px solid var(--border-color)',
                background: 'var(--bg-secondary)',
              }}
            >
              <button
                className="btn-gency btn-gency-secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem' }}
              >
                &larr; Previous
              </button>
              <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                Page <strong style={{ color: '#fff' }}>{page}</strong> of <strong style={{ color: '#fff' }}>{totalPages}</strong>
              </span>
              <button
                className="btn-gency btn-gency-secondary"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem' }}
              >
                Next &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
