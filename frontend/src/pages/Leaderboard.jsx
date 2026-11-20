import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getLeaderboard } from '../api/leaderboard';
import Loading from '../components/Loading';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import { Trophy, Medal, Award, Crown, Zap, AlertTriangle, RotateCcw } from 'lucide-react';

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
      {/* 1. Hero Header Banner */}
      <div
        className="card panel-pastel-blue animate-fade-in-up"
        style={{
          textAlign: 'center',
          marginBottom: '2.5rem',
          padding: '2.75rem 2rem',
          borderRadius: '24px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.85rem' }}>
          <span className="badge badge-SECURITY" style={{ fontSize: '0.78rem', padding: '0.35rem 0.95rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Zap size={13} /> GLOBAL STANDINGS
          </span>
          <span style={{ fontSize: '0.82rem', color: 'var(--pastel-mint-text)', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span className="status-dot" style={{ backgroundColor: 'var(--pastel-mint-text)', width: 7, height: 7 }} />
            VERIFIED BENCHMARKS
          </span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(2.2rem, 4vw, 3rem)',
            fontWeight: 800,
            color: 'var(--text-primary)',
            margin: '0.35rem 0 0.5rem',
          }}
        >
          CodeFoundry Leaderboard
        </h1>

        <p
          style={{
            fontSize: '1.05rem',
            color: 'var(--accent-primary)',
            fontWeight: 700,
            margin: '0 auto 0.65rem',
          }}
        >
          &quot;Practice Software Engineering. Not Just Coding.&quot;
        </p>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', maxWidth: '640px', margin: '0 auto' }}>
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
            border: '1px solid var(--accent-danger-border)',
            background: 'var(--accent-danger-light)',
            borderRadius: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <AlertTriangle size={48} color="var(--accent-danger)" />
          </div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent-danger)', marginBottom: '0.5rem' }}>Leaderboard Unavailable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
            {error}
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={fetchLeaderboard}
            style={{ padding: '0.65rem 1.6rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <RotateCcw size={14} /> Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && leaderboardData.length === 0 && (
        <div
          className="card panel-pastel-lavender"
          style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            maxWidth: '620px',
            margin: '0 auto',
            borderRadius: '24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Trophy size={48} color="var(--pastel-yellow-text)" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No Ranked Developers Yet</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.75rem', lineHeight: 1.6 }}>
            Rankings are computed dynamically when engineers complete evaluated challenges. Be the first developer on the board!
          </p>
          <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.8rem 2rem' }}>
            <span>Explore Challenges</span>
            <span className="btn-arrow-icon">→</span>
          </Link>
        </div>
      )}

      {/* 2. Leaderboard Content */}
      {!loading && !error && leaderboardData.length > 0 && (
        <>
          {/* Top 3 Podium Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', alignItems: 'flex-end', marginBottom: '3rem' }}>
            {/* #2 Rank: Silver (Pastel Blue Card) */}
            {top2 && (
              <div
                className="card panel-pastel-blue animate-fade-in-up"
                style={{
                  padding: '2rem 1.5rem',
                  textAlign: 'center',
                  borderRadius: '24px',
                  border: top2.is_current_user ? '2px solid var(--accent-primary)' : '1px solid var(--pastel-blue-border)',
                  order: 1,
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--pastel-blue-text)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                  <Medal size={16} /> #2 SILVER CONTENDER
                </div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'var(--pastel-blue)', color: 'var(--pastel-blue-text)', border: '2px solid var(--pastel-blue-border)' }}>
                  {top2.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top2.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top2.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.85rem', fontWeight: 800, color: 'var(--pastel-blue-text)', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top2.total_points} /> <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.84rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
                  <span>{top2.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top2.overall_skill_score ?? '—'}</span>
                </div>
              </div>
            )}

            {/* #1 Rank: Champion (Pastel Yellow Card) */}
            {top1 && (
              <div
                className="card panel-pastel-yellow animate-fade-in-up"
                style={{
                  padding: '2.75rem 1.75rem',
                  textAlign: 'center',
                  borderRadius: '28px',
                  border: top1.is_current_user ? '2px solid var(--accent-primary)' : '2px solid var(--pastel-yellow-border)',
                  boxShadow: 'var(--shadow-lg)',
                  order: 0,
                  transform: 'scale(1.03)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.35rem' }}>
                  <Crown size={30} color="#D97706" />
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 900, color: 'var(--pastel-yellow-text)', marginBottom: '0.75rem', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                  <Trophy size={16} /> #1 GLOBAL CHAMPION
                </div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'var(--pastel-yellow)', color: 'var(--pastel-yellow-text)', border: '2px solid var(--pastel-yellow-border)', boxShadow: '0 4px 16px rgba(199, 122, 20, 0.2)' }}>
                  {top1.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 900, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top1.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top1.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.25rem', fontWeight: 900, color: 'var(--pastel-yellow-text)', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top1.total_points} /> <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.88rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--pastel-yellow-border)', paddingTop: '0.85rem', marginTop: '0.85rem' }}>
                  <span>{top1.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top1.overall_skill_score ?? '—'}/100</span>
                </div>
              </div>
            )}

            {/* #3 Rank: Bronze (Pastel Peach Card) */}
            {top3 && (
              <div
                className="card panel-pastel-peach animate-fade-in-up"
                style={{
                  padding: '2rem 1.5rem',
                  textAlign: 'center',
                  borderRadius: '24px',
                  border: top3.is_current_user ? '2px solid var(--accent-primary)' : '1px solid var(--pastel-peach-border)',
                  order: 2,
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--pastel-peach-text)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                  <Award size={16} /> #3 BRONZE CONTENDER
                </div>
                <div className="candidate-avatar-large" style={{ margin: '0 auto 0.75rem', background: 'var(--pastel-peach)', color: 'var(--pastel-peach-text)', border: '2px solid var(--pastel-peach-border)' }}>
                  {top3.username.substring(0, 2).toUpperCase()}
                </div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                  <Link to={`/profile/${encodeURIComponent(top3.username)}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {top3.username}
                  </Link>
                </h3>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.85rem', fontWeight: 800, color: 'var(--pastel-peach-text)', margin: '0.4rem 0' }}>
                  <AnimatedCounter value={top3.total_points} /> <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>PTS</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.84rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
                  <span>{top3.challenges_completed} Solved</span>
                  <span>•</span>
                  <span>Score: {top3.overall_skill_score ?? '—'}</span>
                </div>
              </div>
            )}
          </div>

          {/* 3. Global Ranking Table */}
          <div className="card animate-fade-in-up stagger-2" style={{ padding: '2rem 2.25rem', borderRadius: '24px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
              Developer Standings
            </h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '80px', textAlign: 'center' }}>Rank</th>
                    <th>Developer</th>
                    <th>Solved</th>
                    <th>Attempts</th>
                    <th>Score</th>
                    <th style={{ textAlign: 'right' }}>Total Points</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboardData.map((dev, idx) => {
                    const rank = idx + 1;
                    const isMe = dev.is_current_user || (user && user.username === dev.username);

                    return (
                      <tr
                        key={dev.username}
                        style={{
                          background: isMe ? 'var(--pastel-lavender-light)' : 'transparent',
                          fontWeight: isMe ? 700 : 500,
                        }}
                      >
                        <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.92rem' }}>
                          {rank === 1 ? (
                            <span style={{ color: '#D97706', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Crown size={14} /> 1</span>
                          ) : rank === 2 ? (
                            <span style={{ color: '#4B5563', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Medal size={14} /> 2</span>
                          ) : rank === 3 ? (
                            <span style={{ color: '#B45309', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Award size={14} /> 3</span>
                          ) : (
                            `#${rank}`
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div className="candidate-avatar" style={{ width: 34, height: 34, fontSize: '0.82rem', background: 'var(--pastel-lavender)', color: 'var(--pastel-lavender-text)' }}>
                              {dev.username.substring(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <Link
                                to={`/profile/${encodeURIComponent(dev.username)}`}
                                style={{
                                  fontWeight: 800,
                                  color: 'var(--text-primary)',
                                  textDecoration: 'none',
                                  fontSize: '0.94rem',
                                }}
                              >
                                {dev.username}
                              </Link>
                              {isMe && (
                                <span className="badge badge-API" style={{ marginLeft: '0.5rem', fontSize: '0.65rem' }}>
                                  You
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td>{dev.challenges_completed}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{dev.total_submissions}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                          {dev.overall_skill_score != null ? `${dev.overall_skill_score}/100` : '—'}
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-primary)', fontSize: '1rem' }}>
                          <AnimatedCounter value={dev.total_points} /> pts
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
