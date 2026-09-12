import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getLeaderboard } from '../api/leaderboard';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';

export default function Leaderboard() {
  const { user } = useAuth();
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLeaderboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLeaderboard();
      setLeaderboardData(data?.results || []);
    } catch (err) {
      setError('Leaderboard unavailable. Failed to fetch developer rankings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const top1 = leaderboardData.length > 0 ? leaderboardData[0] : null;
  const top2 = leaderboardData.length > 1 ? leaderboardData[1] : null;
  const top3 = leaderboardData.length > 2 ? leaderboardData[2] : null;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1180px' }}>
      {/* Hero Header */}
      <div
        className="card animate-fade-in-up"
        style={{
          textAlign: 'center',
          marginBottom: '2.5rem',
          padding: '2.5rem 2rem',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)',
          borderRadius: '24px',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <span className="badge badge-SECURITY" style={{ fontSize: '0.78rem', padding: '0.3rem 0.85rem' }}>
            ⚡ GLOBAL STANDINGS
          </span>
          <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span className="status-dot" style={{ backgroundColor: '#059669', width: 7, height: 7 }} />
            LIVE VERIFIED RANKINGS
          </span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(2.2rem, 4vw, 3rem)',
            fontWeight: 800,
            color: 'var(--text-primary)',
            margin: '0.25rem 0 0.5rem',
          }}
        >
          CodeFoundry Leaderboard
        </h1>

        <p
          style={{
            fontSize: '1.05rem',
            color: 'var(--accent-primary)',
            fontWeight: 600,
            margin: '0 auto 0.5rem',
          }}
        >
          &quot;Practice Software Engineering. Not Just Coding.&quot;
        </p>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '620px', margin: '0 auto' }}>
          Deterministic rankings calculated from completed, evaluated engineering challenges across multiple competency domains.
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ padding: '4rem 0' }}>
          <Loading message="Calculating developer rankings and evaluating submissions..." />
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div
          className="card"
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            maxWidth: '560px',
            margin: '0 auto',
            border: '1px solid #fecaca',
            background: '#fef2f2',
            borderRadius: '20px',
          }}
        >
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.4rem', color: '#dc2626', marginBottom: '0.5rem' }}>Leaderboard Unavailable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
            {error}
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={fetchLeaderboard}
            style={{ padding: '0.6rem 1.5rem', fontWeight: 600 }}
          >
            ↻ Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && leaderboardData.length === 0 && (
        <div
          className="card"
          style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            maxWidth: '620px',
            margin: '0 auto',
            borderRadius: '24px',
          }}
        >
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🏆</span>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No Ranked Developers Yet</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.75rem', lineHeight: 1.6 }}>
            Rankings are computed dynamically when engineers complete evaluated challenges. Be the first developer on the board!
          </p>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.75rem 1.75rem' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      )}

      {/* Leaderboard Content */}
      {!loading && !error && leaderboardData.length > 0 && (
        <>
          {/* Top 3 Podium Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', alignItems: 'flex-end', marginBottom: '3rem' }}>
            {/* #2 Rank */}
            {top2 && (
              <div
                className="card animate-fade-in-up"
                style={{
                  padding: '2rem 1.5rem',
                  textAlign: 'center',
                  borderRadius: '20px',
                  background: top2.is_current_user ? 'rgba(99, 102, 241, 0.04)' : '#ffffff',
                  border: top2.is_current_user ? '2px solid var(--accent-primary)' : '1px solid #e2e8f0',
                  order: 1,
                }}
              >
                <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#64748b', marginBottom: '0.75rem' }}>🥈 #2 SILVER</div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'linear-gradient(135deg, #94a3b8, #64748b)' }}>
                  {top2.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top2.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top2.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 800, color: '#2563eb', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top2.total_points} /> <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', borderTop: '1px solid #f1f5f9', paddingTop: '0.6rem', marginTop: '0.6rem' }}>
                  <span>{top2.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top2.overall_skill_score ?? '—'}</span>
                </div>
              </div>
            )}

            {/* #1 Rank (Center Podium) */}
            {top1 && (
              <div
                className="card animate-fade-in-up"
                style={{
                  padding: '2.5rem 1.75rem',
                  textAlign: 'center',
                  borderRadius: '24px',
                  background: top1.is_current_user ? 'rgba(99, 102, 241, 0.06)' : 'linear-gradient(180deg, #ffffff 0%, #fefce8 100%)',
                  border: '2px solid #fbbf24',
                  boxShadow: 'var(--shadow-lg)',
                  order: 0,
                  transform: 'scale(1.02)',
                }}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>👑</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 900, color: '#d97706', marginBottom: '0.75rem' }}>🥇 #1 CHAMPION</div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)' }}>
                  {top1.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 900, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top1.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top1.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.1rem', fontWeight: 900, color: '#d97706', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top1.total_points} /> <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)', borderTop: '1px solid #fef08a', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
                  <span>{top1.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top1.overall_skill_score ?? '—'}/100</span>
                </div>
              </div>
            )}

            {/* #3 Rank */}
            {top3 && (
              <div
                className="card animate-fade-in-up"
                style={{
                  padding: '2rem 1.5rem',
                  textAlign: 'center',
                  borderRadius: '20px',
                  background: top3.is_current_user ? 'rgba(99, 102, 241, 0.04)' : '#ffffff',
                  border: top3.is_current_user ? '2px solid var(--accent-primary)' : '1px solid #e2e8f0',
                  order: 2,
                }}
              >
                <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#ea580c', marginBottom: '0.75rem' }}>🥉 #3 BRONZE</div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'linear-gradient(135deg, #fdba74, #ea580c)' }}>
                  {top3.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top3.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top3.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 800, color: '#2563eb', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top3.total_points} /> <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', borderTop: '1px solid #f1f5f9', paddingTop: '0.6rem', marginTop: '0.6rem' }}>
                  <span>{top3.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top3.overall_skill_score ?? '—'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Full Rankings Table */}
          <div className="card" style={{ padding: '2rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>📊</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>
                  Developer Standings ({leaderboardData.length})
                </h2>
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Sorted by Total Points &amp; Evaluations
              </span>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '80px', textAlign: 'center' }}>Rank</th>
                    <th>Developer</th>
                    <th style={{ textAlign: 'right' }}>Total Points</th>
                    <th style={{ textAlign: 'center' }}>Solved</th>
                    <th style={{ textAlign: 'right' }}>Avg Score</th>
                    <th style={{ textAlign: 'center' }}>Skill Score</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboardData.map((row) => (
                    <tr
                      key={row.user_id}
                      style={{
                        background: row.is_current_user ? 'rgba(99, 102, 241, 0.05)' : 'inherit',
                      }}
                    >
                      <td style={{ textAlign: 'center', fontWeight: 800 }}>
                        {row.rank === 1 ? '🥇 1' : row.rank === 2 ? '🥈 2' : row.rank === 3 ? '🥉 3' : `#${row.rank}`}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div className="candidate-avatar">
                            {row.username.substring(0, 2).toUpperCase()}
                          </div>
                          <Link
                            to={`/profile/${encodeURIComponent(row.username)}`}
                            style={{ fontWeight: 700, color: 'var(--text-primary)', textDecoration: 'none' }}
                          >
                            {row.username}
                          </Link>
                          {row.is_current_user && (
                            <span className="badge badge-API" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                              YOU
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#2563eb' }}>
                        {row.total_points}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className="badge badge-BUG_FIX" style={{ fontSize: '0.75rem', padding: '0.15rem 0.55rem' }}>
                          {row.challenges_completed}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {row.average_score}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {row.overall_skill_score !== null && row.overall_skill_score !== undefined ? (
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontWeight: 700,
                              color: row.overall_skill_score >= 80 ? '#059669' : row.overall_skill_score >= 50 ? '#2563eb' : '#d97706',
                            }}
                          >
                            {row.overall_skill_score} / 100
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
