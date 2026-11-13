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
      {/* 1. Header Banner */}
      <div
        className="card panel-pastel-lavender animate-fade-in-up"
        style={{
          padding: '2.5rem',
          marginBottom: '2.5rem',
          borderRadius: '24px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
          <span className="badge badge-SECURITY">Audit Trail</span>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Docker Sandbox Telemetry</span>
        </div>
        <h1 className="page-title" style={{ margin: 0, fontSize: '2.2rem' }}>Submission Archives</h1>
        <p className="page-description" style={{ marginTop: '0.45rem', marginBottom: 0, maxWidth: '640px' }}>
          Audit and review your automated Docker sandbox evaluation logs, test metrics, and scoring history.
        </p>
      </div>

      {/* 2. Filter Bar */}
      <div
        className="card animate-fade-in-up stagger-1"
        style={{
          padding: '1.25rem 1.75rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderRadius: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 700 }}>Filter by Status:</label>
          <select
            className="select-control"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            style={{ width: 'auto', minWidth: '150px', borderRadius: 'var(--radius-full)', padding: '0.6rem 1.25rem', cursor: 'pointer' }}
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          <strong style={{ color: 'var(--text-primary)' }}>{count}</strong> {count === 1 ? 'submission' : 'submissions'} recorded
        </div>
      </div>

      {/* 3. Content Area */}
      {loading ? (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Loading submission archive..." />
        </div>
      ) : error ? (
        <div style={{ background: 'var(--accent-danger-light)', border: '1px solid var(--accent-danger-border)', color: 'var(--accent-danger)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
          <p>{error}</p>
        </div>
      ) : submissions.length === 0 ? (
        <div className="card animate-scale-in" style={{ padding: '4rem 2rem', textAlign: 'center', borderRadius: '24px' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>📂</span>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', marginBottom: '1.5rem' }}>
            No submissions recorded under the selected filter criteria.
          </p>
          <Link to="/challenges" className="btn-saas btn-saas-primary">
            <span>Browse Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      ) : (
        <div className="card animate-fade-in-up stagger-2" style={{ overflow: 'hidden', borderRadius: '24px', padding: 0 }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {submissions.map((sub, idx) => (
              <div
                key={sub.id}
                className={`animate-fade-in-up stagger-${(idx % 8) + 1}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1.35rem 1.75rem',
                  borderBottom: idx < submissions.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  background: idx % 2 === 0 ? '#ffffff' : '#FAF9FD',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                    <Link
                      to={`/challenges/${sub.challenge_id || sub.challenge?.id || sub.challenge}`}
                      style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '1.05rem', textDecoration: 'none' }}
                    >
                      {sub.challenge_title || sub.challenge?.title || `Challenge #${sub.challenge}`}
                    </Link>
                    <span className="badge badge-API">{sub.language || 'Python'}</span>
                  </div>

                  <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
                    Submission #{sub.id} · {formatTimestamp(sub.created_at || sub.submitted_at)}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                      {sub.score != null ? (
                        <>
                          <AnimatedCounter value={sub.score} duration={800} /> pts
                        </>
                      ) : (
                        '—'
                      )}
                    </div>
                  </div>

                  <span className={`badge ${sub.status === 'PASSED' ? 'badge-passed' : sub.status === 'FAILED' ? 'badge-failed' : 'badge-pending'}`}>
                    {sub.status}
                  </span>

                  <Link
                    to={`/workspace/${sub.challenge_id || sub.challenge?.id || sub.challenge}`}
                    className="btn btn-secondary"
                    style={{ padding: '0.45rem 1rem', fontSize: '0.84rem' }}
                  >
                    Open Workspace →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.85rem', marginTop: '3rem' }}>
          <button
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.86rem' }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 700, padding: '0.4rem 0.85rem', background: '#ffffff', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-color)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.86rem' }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
