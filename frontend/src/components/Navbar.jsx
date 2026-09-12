import React, { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const isRecruiterOrAdmin = user?.role === 'RECRUITER' || user?.role === 'ADMIN' || user?.is_staff;

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <Link to="/" className="navbar-brand" aria-label="CodeFoundry Home">
        <span className="logo-icon">&gt;_</span>
        <span style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.025em', fontSize: '1.28rem', fontWeight: 800 }}>
          CodeFoundry
        </span>
      </Link>

      {/* Mobile Menu Toggle */}
      <button
        type="button"
        className="mobile-nav-toggle"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        aria-label="Toggle navigation menu"
        aria-expanded={mobileMenuOpen}
      >
        {mobileMenuOpen ? '✕' : '☰'}
      </button>

      <nav className={`navbar-nav ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <NavLink
          to="/"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          end
        >
          Home
        </NavLink>

        <NavLink
          to="/challenges"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Challenges
        </NavLink>

        <NavLink
          to="/leaderboard"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Leaderboard
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
              to="/submissions"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Submissions
            </NavLink>
            {isRecruiterOrAdmin && (
              <NavLink
                to="/recruiter"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                Recruiter Hub
              </NavLink>
            )}
          </>
        )}

        {!isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginLeft: '0.5rem' }}>
            <NavLink
              to="/login"
              className="nav-link"
              style={{ fontWeight: 600 }}
            >
              Sign In
            </NavLink>
            <Link
              to="/register"
              className="btn-saas btn-saas-primary"
              style={{ padding: '0.55rem 1.25rem', fontSize: '0.88rem' }}
            >
              <span>Get Started</span>
              <span className="btn-arrow-icon">→</span>
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: '0.5rem' }}>
            <Link
              to={`/profile/${encodeURIComponent(user?.username || '')}`}
              className="user-pill"
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{user?.username}</span>
              <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>· {user?.role || 'Developer'}</span>
            </Link>
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ padding: '0.4rem 0.95rem', fontSize: '0.82rem' }}
              title="Sign out of your session"
            >
              Logout
            </button>
          </div>
        )}
      </nav>
    </header>
  );
}
