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
    <div className="leaderboard-page container" style={{ maxWidth: '1180px', margin: '0 auto', padding: '2rem 1.5rem 4rem' }}>
      {/* Hero Header */}
      <div className="leaderboard-hero" style={{ textAlign: 'center', marginBottom: '2.75rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <span className="badge badge-SECURITY" style={{ fontSize: '0.78rem', letterSpacing: '0.08em', padding: '0.3rem 0.85rem' }}>
            ⚡ GLOBAL STANDINGS
          </span>
          <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span className="status-dot" style={{ backgroundColor: '#10b981', width: 6, height: 6 }} />
            LIVE VERIFIED RANKINGS
          </span>
        </div>

        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(2.2rem, 5vw, 3.4rem)',
            fontWeight: 900,
            color: '#fff',
            letterSpacing: '-0.02em',
            margin: '0.25rem 0 0.75rem',
            lineHeight: 1.1,
          }}
        >
          DevForge Leaderboard
        </h1>

        <p
          style={{
            fontSize: '1.2rem',
            color: '#c7d2fe',
            fontWeight: 600,
            margin: '0 auto 0.5rem',
            fontStyle: 'italic',
          }}
        >
          "Compete. Improve. Prove Your Engineering Skills."
        </p>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.94rem', maxWidth: '640px', margin: '0 auto' }}>
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
            border: '1px solid rgba(239, 68, 68, 0.4)',
            background: 'rgba(239, 68, 68, 0.05)',
          }}
        >
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>⚠️</span>
          <h2 style={{ fontSize: '1.4rem', color: '#f87171', marginBottom: '0.5rem' }}>Leaderboard Unavailable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
            We could not load the global leaderboard standings right now. Please check your connection and try again.
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
            background: 'linear-gradient(180deg, rgba(22, 32, 52, 0.6) 0%, rgba(10, 15, 26, 0.8) 100%)',
          }}
        >
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🏆</span>
          <h2 style={{ fontSize: '1.5rem', color: '#fff', marginBottom: '0.5rem' }}>No Ranked Developers Yet</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.75rem', lineHeight: 1.6 }}>
            Rankings are computed dynamically when engineers complete evaluated challenges. Be the first developer on the board!
          </p>
          <Link to="/challenges" className="btn-gency btn-gency-primary" style={{ padding: '0.65rem 1.5rem', display: 'inline-flex' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      )}

      {/* Leaderboard Content */}
      {!loading && !error && leaderboardData.length > 0 && (
        <>
          {/* Top 3 Podium */}
          <div className="leaderboard-podium-section" style={{ marginBottom: '3.5rem' }}>
            <div className="leaderboard-podium-grid">
              {/* #2 Rank (Silver - Left) */}
              {top2 && (
                <div className={`podium-card podium-card-2 ${top2.is_current_user ? 'podium-current-user' : ''}`}>
                  <div className="podium-rank-badge podium-rank-2">🥈 #2</div>
                  <div className="podium-avatar">
                    {top2.username.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="podium-username">
                    <Link to={`/profile/${encodeURIComponent(top2.username)}`} style={{ color: 'inherit', textDecoration: 'none' }} className="leaderboard-user-link">
                      {top2.username}
                    </Link>
                    {top2.is_current_user && <span className="current-user-badge">YOU</span>}
                  </div>
                  <div className="podium-points">
                    <span className="podium-points-num"><AnimatedCounter value={top2.total_points} /></span>
                    <span className="podium-points-label">PTS</span>
                  </div>
                  <div className="podium-stats">
                    <div>
                      <span>{top2.challenges_completed}</span>
                      <small>Solved</small>
                    </div>
                    <div>
                      <span>{top2.average_score}</span>
                      <small>Avg Score</small>
                    </div>
                    <div>
                      <span>{top2.overall_skill_score ?? '—'}</span>
                      <small>Skill</small>
                    </div>
                  </div>
                </div>
              )}

              {/* #1 Rank (Gold - Dominant Center) */}
              {top1 && (
                <div className={`podium-card podium-card-1 ${top1.is_current_user ? 'podium-current-user' : ''}`}>
                  <div className="podium-crown-icon">👑</div>
                  <div className="podium-rank-badge podium-rank-1">🥇 #1 CHAMPION</div>
                  <div className="podium-avatar podium-avatar-gold">
                    {top1.username.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="podium-username podium-username-gold">
                    <Link to={`/profile/${encodeURIComponent(top1.username)}`} style={{ color: 'inherit', textDecoration: 'none' }} className="leaderboard-user-link">
                      {top1.username}
                    </Link>
                    {top1.is_current_user && <span className="current-user-badge">YOU</span>}
                  </div>
                  <div className="podium-points podium-points-gold">
                    <span className="podium-points-num"><AnimatedCounter value={top1.total_points} /></span>
                    <span className="podium-points-label">PTS</span>
                  </div>
                  <div className="podium-stats">
                    <div>
                      <span>{top1.challenges_completed}</span>
                      <small>Solved</small>
                    </div>
                    <div>
                      <span>{top1.average_score}</span>
                      <small>Avg Score</small>
                    </div>
                    <div>
                      <span>{top1.overall_skill_score ?? '—'}</span>
                      <small>Skill</small>
                    </div>
                  </div>
                </div>
              )}

              {/* #3 Rank (Bronze - Right) */}
              {top3 && (
                <div className={`podium-card podium-card-3 ${top3.is_current_user ? 'podium-current-user' : ''}`}>
                  <div className="podium-rank-badge podium-rank-3">🥉 #3</div>
                  <div className="podium-avatar">
                    {top3.username.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="podium-username">
                    <Link to={`/profile/${encodeURIComponent(top3.username)}`} style={{ color: 'inherit', textDecoration: 'none' }} className="leaderboard-user-link">
                      {top3.username}
                    </Link>
                    {top3.is_current_user && <span className="current-user-badge">YOU</span>}
                  </div>
                  <div className="podium-points">
                    <span className="podium-points-num"><AnimatedCounter value={top3.total_points} /></span>
                    <span className="podium-points-label">PTS</span>
                  </div>
                  <div className="podium-stats">
                    <div>
                      <span>{top3.challenges_completed}</span>
                      <small>Solved</small>
                    </div>
                    <div>
                      <span>{top3.average_score}</span>
                      <small>Avg Score</small>
                    </div>
                    <div>
                      <span>{top3.overall_skill_score ?? '—'}</span>
                      <small>Skill</small>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Full Rankings Table */}
          <div className="leaderboard-table-card">
            <div className="leaderboard-table-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.15rem' }}>📊</span>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                  Global Developer Standings ({leaderboardData.length})
                </h2>
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Sorted Deterministically
              </span>
            </div>

            <div className="leaderboard-table-wrapper">
              <table className="leaderboard-table">
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
                  {leaderboardData.map((row) => {
                    const isTop1 = row.rank === 1;
                    const isTop2 = row.rank === 2;
                    const isTop3 = row.rank === 3;

                    return (
                      <tr
                        key={row.user_id}
                        className={`leaderboard-row ${row.is_current_user ? 'leaderboard-row-current' : ''}`}
                      >
                        <td style={{ textAlign: 'center' }}>
                          <span
                            className={`rank-pill ${
                              isTop1
                                ? 'rank-pill-1'
                                : isTop2
                                ? 'rank-pill-2'
                                : isTop3
                                ? 'rank-pill-3'
                                : ''
                            }`}
                          >
                            {isTop1 ? '🥇 1' : isTop2 ? '🥈 2' : isTop3 ? '🥉 3' : `#${row.rank}`}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div className="table-avatar">
                              {row.username.substring(0, 2).toUpperCase()}
                            </div>
                            <Link
                              to={`/profile/${encodeURIComponent(row.username)}`}
                              className="leaderboard-user-link"
                              style={{
                                fontWeight: 700,
                                color: row.is_current_user ? '#38bdf8' : '#fff',
                                textDecoration: 'none',
                              }}
                            >
                              {row.username}
                            </Link>
                            {row.is_current_user && (
                              <span className="current-user-badge">YOU</span>
                            )}
                          </div>
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#38bdf8' }}>
                          {row.total_points}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <span className="badge badge-BUG_FIX" style={{ padding: '0.15rem 0.55rem', fontSize: '0.75rem' }}>
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
                                color: row.overall_skill_score >= 80 ? '#10b981' : row.overall_skill_score >= 50 ? '#38bdf8' : '#f59e0b',
                              }}
                            >
                              {row.overall_skill_score} / 100
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
