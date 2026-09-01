import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="logo-icon">&gt;_</span>
        <span>CodeFoundry</span>
      </Link>
      <nav className="navbar-nav">
        <NavLink
          to="/"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          end
        >
          Home
        </NavLink>

        {isAuthenticated && (
          <>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/challenges"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Challenges
            </NavLink>
            <NavLink
              to="/submissions"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              My Submissions
            </NavLink>
          </>
        )}



        {!isAuthenticated ? (
          <>
            <NavLink
              to="/login"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Login
            </NavLink>
            <NavLink
              to="/register"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Register
            </NavLink>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <span
              style={{
                fontSize: '0.82rem',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'var(--bg-primary)',
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
              }}
            >
              {user?.username} <strong style={{ color: '#58a6ff' }}>· {user?.role}</strong>
            </span>
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem' }}
            >
              Logout
            </button>
          </div>
        )}
      </nav>
    </header>
  );
}

