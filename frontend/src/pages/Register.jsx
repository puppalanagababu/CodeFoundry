import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password !== password2) {
      setError('Passwords do not match.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
        password2,
      });
      navigate('/login', {
        state: { message: 'Registration successful! Please sign in with your credentials.' },
      });
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container animate-fade-in-up" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 160px)' }}>
      <div className="card animate-scale-in" style={{ width: '100%', maxWidth: '460px', padding: '2.75rem 2.25rem', borderRadius: '24px', boxShadow: 'var(--shadow-xl)' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ width: 48, height: 48, margin: '0 auto 1.25rem', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.3rem', color: '#fff', boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)' }}>
            &gt;_
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: '0.4rem' }}>
            Join CodeFoundry
          </h1>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
            Start building verified software engineering competencies
          </p>
        </div>

        {error && (
          <div className="animate-fade-in-up" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 'var(--radius-md)', padding: '0.75rem 1rem', marginBottom: '1.25rem', fontSize: '0.88rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="register-username">
              Username *
            </label>
            <input
              id="register-username"
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
            <label className="form-label" htmlFor="register-email">
              Email (optional)
            </label>
            <input
              id="register-email"
              type="email"
              className="input-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@example.com"
              autoComplete="email"
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="register-password">
              Password *
            </label>
            <input
              id="register-password"
              type="password"
              className="input-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              autoComplete="new-password"
              required
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="register-password-confirm">
              Confirm Password *
            </label>
            <input
              id="register-password-confirm"
              type="password"
              className="input-control"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              placeholder="••••••••••••"
              autoComplete="new-password"
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
                <span>Creating Account...</span>
              </span>
            ) : (
              <>
                <span>Create Free Account</span>
                <span className="btn-arrow-icon">→</span>
              </>
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>
            Sign In →
          </Link>
        </div>
      </div>
    </div>
  );
}
