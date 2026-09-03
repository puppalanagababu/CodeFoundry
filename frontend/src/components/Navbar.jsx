import React, { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <Link to="/" className="navbar-brand" aria-label="DevForge Home">
        <span className="logo-icon">&gt;_</span>
        <span style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.02em', fontSize: '1.25rem' }}>
          DevForge
        </span>
      </Link>

      {/* Mobile Menu Toggle Button */}
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
              to="/leaderboard"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Leaderboard
            </NavLink>
            {(user?.role === 'RECRUITER' || user?.role === 'ADMIN') && (
              <NavLink
                to="/recruiter"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                Recruiter
              </NavLink>
            )}
            <NavLink
              to="/submissions"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              My Submissions
            </NavLink>
          </>
        )}

        {!isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginLeft: '0.5rem' }}>
            <NavLink
              to="/login"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Sign In
            </NavLink>
            <Link
              to="/register"
              className="btn-gency btn-gency-primary"
              style={{ padding: '0.45rem 1.15rem', fontSize: '0.86rem' }}
            >
              <span>Get Started</span>
              <span className="btn-arrow-icon">↗</span>
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: '0.5rem' }}>
            <span className="user-pill">
              <span style={{ fontWeight: 600, color: '#fff' }}>{user?.username}</span>
              <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>· {user?.role || 'Developer'}</span>
            </span>
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ padding: '0.4rem 0.9rem', fontSize: '0.82rem', borderRadius: 'var(--radius-full)' }}
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
