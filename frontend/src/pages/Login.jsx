import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';
  const successMessage = location.state?.message;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide both username and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await login({ username, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container animate-fade-in-up" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 160px)' }}>
      <div className="card animate-scale-in" style={{ width: '100%', maxWidth: '440px', padding: '2.75rem 2.25rem', borderRadius: '24px', boxShadow: 'var(--shadow-xl)' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ width: 48, height: 48, margin: '0 auto 1.25rem', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.3rem', color: '#fff', boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)' }}>
            &gt;_
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: '0.4rem' }}>
            Welcome to CodeFoundry
          </h1>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
            Sign in to continue your software engineering practice
          </p>
        </div>

        {successMessage && (
          <div className="animate-fade-in-up" style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#059669', borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem', marginBottom: '1.25rem', fontSize: '0.88rem' }}>
            {successMessage}
          </div>
        )}

        {error && (
          <div className="animate-fade-in-up" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem', marginBottom: '1.25rem', fontSize: '0.88rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="login-username">
              Username
            </label>
            <input
              id="login-username"
              type="text"
              className="input-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. dev_alex"
              autoComplete="username"
              required
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className="input-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn-saas btn-saas-primary"
            disabled={loading}
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.85rem 1rem' }}
          >
            {loading ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="spinner-icon" style={{ borderTopColor: '#ffffff' }} />
                <span>Authenticating...</span>
              </span>
            ) : (
              <>
                <span>Sign In</span>
                <span className="btn-arrow-icon">→</span>
              </>
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Don&apos;t have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>
            Create one free →
          </Link>
        </div>
      </div>
    </div>
  );
}
