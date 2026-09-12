import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { getChallengeSubmissions } from '../api/submissions';
import Loading from '../components/Loading';

const BURST_TRAJECTORIES = [
  { dx: '-240px', dy: '-140px', rot: '-14deg', scale: 0.95, delay: '0ms' },
  { dx: '-90px', dy: '-185px', rot: '-6deg', scale: 1.05, delay: '40ms' },
  { dx: '90px', dy: '-180px', rot: '8deg', scale: 1.0, delay: '20ms' },
  { dx: '240px', dy: '-135px', rot: '15deg', scale: 0.95, delay: '60ms' },
  { dx: '-270px', dy: '10px', rot: '-9deg', scale: 1.0, delay: '30ms' },
  { dx: '275px', dy: '15px', rot: '11deg', scale: 1.02, delay: '50ms' },
  { dx: '-220px', dy: '140px', rot: '-12deg', scale: 0.92, delay: '40ms' },
  { dx: '-80px', dy: '175px', rot: '-5deg', scale: 1.05, delay: '20ms' },
  { dx: '80px', dy: '170px', rot: '7deg', scale: 0.98, delay: '50ms' },
  { dx: '230px', dy: '140px', rot: '14deg', scale: 0.94, delay: '10ms' },
];

const INCIDENT_TYPE_CONFIG = {
  BUG_FIX: {
    badge: 'Production Defect Alert',
    headline: 'SOMETHING IS BROKEN.',
    lead: 'A critical production codebase is throwing runtime exceptions and returning faulty results.',
    icon: '🐛',
    color: '#ef4444',
    diagnostics: [
      'Scanning repository modules and callgraphs...',
      'Tracing runtime exception callstacks...',
      'Analyzing regression test failure vectors...',
      'Root cause isolated in service routines!',
    ],
    signals: [
      'BUG DETECTED',
      'REGRESSION',
      'FAILING TEST',
      'STACK TRACE',
      'RUNTIME ERROR',
      'ASSERTION FAILED',
      'NULL POINTER',
      'DEFECT ISOLATED',
      'EXCEPTION THROWN',
      'FAULT LOCALIZED',
    ],
  },
  DEBUGGING: {
    badge: 'Fault Localization Alert',
    headline: 'SOMETHING IS BROKEN.',
    lead: 'Unexpected program behavior detected during production execution.',
    icon: '🐛',
    color: '#ef4444',
    diagnostics: [
      'Scanning repository modules and callgraphs...',
      'Tracing runtime exception callstacks...',
      'Analyzing regression test failure vectors...',
      'Root cause isolated in service routines!',
    ],
    signals: [
      'BUG DETECTED',
      'REGRESSION',
      'FAILING TEST',
      'STACK TRACE',
      'RUNTIME ERROR',
      'ASSERTION FAILED',
      'NULL POINTER',
      'DEFECT ISOLATED',
      'EXCEPTION THROWN',
      'FAULT LOCALIZED',
    ],
  },
  API: {
    badge: 'Protocol Anomaly Alert',
    headline: "SOMETHING ISN'T RETURNING CORRECTLY.",
    lead: 'An HTTP service endpoint is returning invalid payloads or breaking client contracts.',
    icon: '⚡',
    color: '#3b82f6',
    diagnostics: [
      'Interrogating REST endpoint route handlers...',
      'Validating JSON response serialization...',
      'Testing status codes against API contract specifications...',
      'Payload schema mismatch detected!',
    ],
    signals: [
      '500 RESPONSE',
      'INVALID PAYLOAD',
      'API FAILURE',
      'SCHEMA ERROR',
      'REQUEST FAILED',
      'HEADER MISMATCH',
      'UNEXPECTED JSON',
      'STATUS 502',
      'ENDPOINT ERROR',
      'PARSE ERROR',
    ],
  },
  SECURITY: {
    badge: 'Security Vulnerability Alert',
    headline: 'SOMETHING IS EXPOSED.',
    lead: 'Sensitive endpoints or parameter validation mechanisms have critical security flaws.',
    icon: '🛡️',
    color: '#8b5cf6',
    diagnostics: [
      'Scanning authorization guards and middleware...',
      'Auditing input sanitization and parameter handling...',
      'Simulating unauthorized privilege escalation vectors...',
      'Unrestricted vulnerability vector confirmed!',
    ],
    signals: [
      'AUTH FAILURE',
      'ACCESS BYPASS',
      'EXPOSED ENDPOINT',
      'VULNERABILITY',
      'SECURITY ALERT',
      'TOKEN EXPIRED',
      'PRIVILEGE ESCALATION',
      'DATA LEAK',
      'INJECTION VECTOR',
      'UNAUTHORIZED',
    ],
  },
  PERFORMANCE: {
    badge: 'Resource Bottleneck Alert',
    headline: 'SOMETHING IS TOO SLOW.',
    lead: 'High algorithmic complexity and excessive memory consumption exceed container constraints.',
    icon: '🚀',
    color: '#10b981',
    diagnostics: [
      'Profiling CPU cycles and memory allocations...',
      'Analyzing nested loops and duplicate operations...',
      'Measuring latency against strict execution limits...',
      'O(N²) quadratic bottleneck detected!',
    ],
    signals: [
      'TIMEOUT',
      'SLOW QUERY',
      'HIGH CPU',
      'HOT PATH',
      'PERFORMANCE ALERT',
      'MEMORY SPIKE',
      'O(N²) DETECTED',
      'LATENCY SPIKE',
      'THREAD CONTENTION',
      'BOTTLENECK',
    ],
  },
  DATABASE: {
    badge: 'Data Integrity Alert',
    headline: 'SOMETHING IS WRONG WITH THE DATA.',
    lead: 'Data persistence layers or relational queries are corrupting record consistency.',
    icon: '🗄️',
    color: '#f59e0b',
    diagnostics: [
      'Inspecting relational queries and transactional blocks...',
      'Verifying foreign key constraints and dataset states...',
      'Auditing index lookups against query telemetry...',
      'Data corruption pattern isolated!',
    ],
    signals: [
      'DATA MISMATCH',
      'QUERY FAILURE',
      'TRANSACTION ERROR',
      'RECORD CORRUPTED',
      'FOREIGN KEY ERROR',
      'INDEX MISS',
      'DEADLOCK DETECTED',
      'STALE DATA',
      'SCHEMA CONFLICT',
      'INTEGRITY ERROR',
    ],
  },
  TESTING: {
    badge: 'Test Coverage Gap',
    headline: "SOMETHING ISN'T BEING VERIFIED.",
    lead: 'Missing assertion suites and unverified edge cases leave production systems unprotected.',
    icon: '🧪',
    color: '#06b6d4',
    diagnostics: [
      'Auditing unit and integration test coverage...',
      'Checking test fixtures and assertions against edge cases...',
      'Measuring mutation test survival rates...',
      'Critical untested pathway discovered!',
    ],
    signals: [
      'FAILING ASSERTION',
      'EDGE CASE',
      'TEST GAP',
      'REGRESSION',
      'COVERAGE DROP',
      'UNTESTED BRANCH',
      'FIXTURE ERROR',
      'MOCK FAILURE',
      'ASSERTION TIMEOUT',
      'SUITE ERROR',
    ],
  },
};

const DEFAULT_INCIDENT_CONFIG = {
  badge: 'Engineering Incident Alert',
  headline: 'SOMETHING IS MISSING.',
  lead: 'A production service requires implementation and verification against system specifications.',
  icon: '📦',
  color: '#6366f1',
  diagnostics: [
    'Scanning codebase structure and dependencies...',
    'Inspecting interface contracts and requirements...',
    'Checking runtime behavior in Docker sandbox...',
    'Engineering scenario confirmed!',
  ],
  signals: [
    'MISSING FEATURE',
    'SPEC GAP',
    'IMPLEMENTATION',
    'REQUIREMENT',
    'UNIMPLEMENTED',
    'SYSTEM CONTRACT',
    'API ENDPOINT',
    'SERVICE LOGIC',
    'INTEGRATION GAP',
    'FEATURE NEEDED',
  ],
};

export default function ChallengeDetails() {
  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [attemptsData, setAttemptsData] = useState({ results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Interactive Problem Reveal state: 'idle' | 'investigating' | 'burst' | 'revealed'
  const [revealState, setRevealState] = useState('idle');
  const [diagnosticStep, setDiagnosticStep] = useState(0);
  const timersRef = useRef([]);

  const clearAllTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    setRevealState('idle');

    Promise.all([
      getChallenge(id),
      getChallengeSubmissions(id, { page_size: 5 }).catch(() => ({ results: [], count: 0 })),
    ])
      .then(([challengeRes, attemptsRes]) => {
        if (!isMounted) return;
        setChallenge(challengeRes);
        setAttemptsData(attemptsRes || { results: [], count: 0 });
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load challenge details.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
      clearAllTimers();
    };
  }, [id]);

  const handleStartInvestigation = () => {
    clearAllTimers();

    const prefersReducedMotion =
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      setRevealState('revealed');
      return;
    }

    setRevealState('investigating');
    setDiagnosticStep(0);

    const stepTimings = [300, 650, 1000, 1350];

    stepTimings.forEach((timing, index) => {
      const t = setTimeout(() => {
        setDiagnosticStep(index + 1);
        if (index === stepTimings.length - 1) {
          const burstTimer = setTimeout(() => {
            setRevealState('burst');
            const revealTimer = setTimeout(() => {
              setRevealState('revealed');
            }, 850);
            timersRef.current.push(revealTimer);
          }, 250);
          timersRef.current.push(burstTimer);
        }
      }, timing);
      timersRef.current.push(t);
    });
  };

  const handleQuickReveal = () => {
    clearAllTimers();
    setRevealState('revealed');
  };

  if (loading) {
    return (
      <div className="page-container" style={{ padding: '4rem 1.5rem' }}>
        <Loading message="Loading challenge briefing & requirements..." />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="page-container">
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 'var(--radius-md)', padding: '1.5rem', textAlign: 'center' }}>
          <p style={{ marginBottom: '1rem', fontSize: '1.05rem' }}>{error || 'Challenge not found.'}</p>
          <Link to="/challenges" className="btn btn-secondary">
            &larr; Back to Challenges
          </Link>
        </div>
      </div>
    );
  }

  const hasAttempts = attemptsData.count > 0;
  const hasPassed = attemptsData.results.some((item) => item.status === 'PASSED');
  const bestScore = hasAttempts
    ? Math.max(...attemptsData.results.map((item) => (typeof item.score === 'number' ? item.score : 0)))
    : null;

  const incidentConfig = INCIDENT_TYPE_CONFIG[challenge.challenge_type] || DEFAULT_INCIDENT_CONFIG;

  return (
    <div className="page-container animate-fade-in-up" style={{ maxWidth: '1100px' }}>
      <Link
        to="/challenges"
        style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, textDecoration: 'none' }}
      >
        &larr; Back to Challenges
      </Link>

      {/* 1. INITIAL STATE: INCIDENT ALERT (Interactive Problem Discovery) */}
      {revealState === 'idle' && (
        <div
          className="card animate-scale-in"
          style={{
            textAlign: 'center',
            marginBottom: '2.5rem',
            padding: '3.5rem 2rem',
            borderRadius: '24px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(59, 130, 246, 0.04) 100%)',
            border: '1px solid #e2e8f0',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: `${incidentConfig.color}15`,
              border: `1px solid ${incidentConfig.color}35`,
              color: incidentConfig.color,
              fontSize: '0.85rem',
              fontWeight: 700,
              padding: '0.35rem 0.95rem',
              borderRadius: 'var(--radius-full)',
              marginBottom: '1.25rem',
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: incidentConfig.color }} />
            <span>{incidentConfig.badge}</span>
          </div>

          <h1
            className="hero-title animate-fade-in-up stagger-1"
            style={{ fontSize: '2.6rem', marginBottom: '0.85rem', letterSpacing: '-0.03em' }}
          >
            {incidentConfig.headline}
          </h1>

          <p
            className="hero-subtitle animate-fade-in-up stagger-2"
            style={{ margin: '0 auto 2rem', maxWidth: '620px', fontSize: '1.05rem' }}
          >
            {incidentConfig.lead}
          </p>

          <div
            className="animate-fade-in-up stagger-3"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem',
              flexWrap: 'wrap',
              marginBottom: '2.5rem',
            }}
          >
            <span className={`badge badge-${challenge.difficulty}`} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>
              {challenge.difficulty}
            </span>
            <span className={`badge badge-${challenge.challenge_type}`} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>
              {challenge.challenge_type?.replace('_', ' ')}
            </span>
            <span className="badge badge-API" style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>
              {challenge.points} PTS
            </span>
            <span className="badge badge-BEGINNER" style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>
              {challenge.programming_language}
            </span>
          </div>

          <div
            className="animate-fade-in-up stagger-4"
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.85rem' }}
          >
            <button
              type="button"
              onClick={handleStartInvestigation}
              className="btn-saas btn-saas-primary"
              style={{
                padding: '0.95rem 2.8rem',
                fontSize: '1.05rem',
              }}
              aria-label="Investigate engineering incident"
            >
              <span style={{ fontSize: '1.15rem' }}>{incidentConfig.icon}</span>
              <span>INVESTIGATE INCIDENT</span>
              <span className="btn-arrow-icon">→</span>
            </button>

            <button
              type="button"
              onClick={handleQuickReveal}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                cursor: 'pointer',
                textDecoration: 'underline',
                padding: '0.35rem',
              }}
            >
              Skip diagnostic &amp; view challenge details
            </button>
          </div>
        </div>
      )}

      {/* 2. INVESTIGATION STATE: DIAGNOSTIC SCANNER */}
      {revealState === 'investigating' && (
        <div
          className="card animate-fade-in-up"
          style={{ textAlign: 'center', marginBottom: '2.5rem', padding: '3rem 2rem', borderRadius: '24px' }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              color: 'var(--accent-primary)',
              fontSize: '0.82rem',
              fontWeight: 700,
              padding: '0.35rem 0.95rem',
              borderRadius: 'var(--radius-full)',
              marginBottom: '1rem',
            }}
          >
            <span className="spinner-icon" style={{ width: 10, height: 10, borderWidth: 1.5 }} />
            <span>RUNNING SYSTEM DIAGNOSTIC</span>
          </div>

          <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Investigating Codebase Telemetry...
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', marginBottom: '1.75rem' }}>
            Inspecting sandbox environment, source files, and unit test assertions.
          </p>

          <div
            style={{
              maxWidth: '680px',
              margin: '0 auto',
              background: '#0f172a',
              borderRadius: '16px',
              padding: '1.5rem',
              textAlign: 'left',
              color: '#f8fafc',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #334155', paddingBottom: '0.6rem', marginBottom: '0.85rem', fontSize: '0.78rem', color: '#94a3b8' }}>
              <span>$ codefoundry diagnose --sandbox container-01</span>
              <button
                type="button"
                onClick={handleQuickReveal}
                style={{ background: 'transparent', border: 'none', color: '#818cf8', cursor: 'pointer', fontSize: '0.78rem' }}
              >
                Skip [Instant]
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: '#94a3b8' }}>
                [0.00s] Initializing diagnostic telemetry in isolated Docker sandbox...
              </div>
              {diagnosticStep >= 1 && (
                <div className="animate-fade-in-up" style={{ color: '#38bdf8' }}>
                  [0.30s] {incidentConfig.diagnostics[0]}
                </div>
              )}
              {diagnosticStep >= 2 && (
                <div className="animate-fade-in-up" style={{ color: '#fbbf24' }}>
                  [0.65s] {incidentConfig.diagnostics[1]}
                </div>
              )}
              {diagnosticStep >= 3 && (
                <div className="animate-fade-in-up" style={{ color: '#f87171' }}>
                  [1.00s] {incidentConfig.diagnostics[2]}
                </div>
              )}
              {diagnosticStep >= 4 && (
                <div className="animate-fade-in-up" style={{ color: '#34d399', fontWeight: 700 }}>
                  [1.35s] ⚡ {incidentConfig.diagnostics[3]}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2.5 BURST STATE */}
      {revealState === 'burst' && (
        <div
          className="card"
          style={{
            textAlign: 'center',
            marginBottom: '2.5rem',
            padding: '4rem 2rem',
            borderRadius: '24px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%)',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              color: '#059669',
              fontSize: '0.92rem',
              fontWeight: 800,
              padding: '0.5rem 1.4rem',
              borderRadius: 'var(--radius-full)',
            }}
          >
            <span>⚡ ISSUE DETECTED &amp; ISOLATED</span>
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '1rem' }}>
            Decompiling Target Environment...
          </h2>
        </div>
      )}

      {/* 3. REVEALED STATE: HERO BRIEFING & ENTER CODEBASE */}
      {revealState === 'revealed' && (
        <div
          className="card animate-fade-in-up"
          style={{ padding: '2.5rem', marginBottom: '2rem', borderRadius: '24px', border: '1px solid #e2e8f0' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.75rem' }}>
            <div style={{ flex: '1 1 500px' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                <span className="badge" style={{ backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca' }}>
                  ⚠ ISSUE DETECTED
                </span>
                <span className={`badge badge-${challenge.difficulty}`}>
                  {challenge.difficulty}
                </span>
                <span className={`badge badge-${challenge.challenge_type}`}>
                  {challenge.challenge_type?.replace('_', ' ')}
                </span>
                {hasPassed ? (
                  <span className="status-pill status-passed">
                    <span className="status-dot" />
                    <span>Solved ({bestScore}/{challenge.points} pts)</span>
                  </span>
                ) : hasAttempts ? (
                  <span className="status-pill status-pending">
                    <span className="status-dot" />
                    <span>Attempted ({bestScore}/{challenge.points} pts)</span>
                  </span>
                ) : (
                  <span className="badge badge-API">New Mission</span>
                )}
              </div>

              <h1 className="page-title" style={{ margin: 0, fontSize: '2.25rem' }}>
                {challenge.title}
              </h1>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <Link
                to={`/workspace/${challenge.id}`}
                className="btn-saas btn-saas-primary"
                style={{
                  padding: '0.85rem 2.25rem',
                  fontSize: '1rem',
                }}
              >
                <span>ENTER CODEBASE</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.25rem' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 600 }}>Language</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.programming_language}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 600 }}>Points</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.points} pts</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 600 }}>Time Limit</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.time_limit}s</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 600 }}>Memory Limit</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.memory_limit} MB</span>
            </div>
          </div>
        </div>
      )}

      {/* Challenge Information & Briefing */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        {/* Description & Requirements */}
        <div className="card animate-fade-in-up stagger-1" style={{ padding: '2.25rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '1rem' }}>
            Mission Briefing &amp; Requirements
          </h2>
          <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.96rem', lineHeight: '1.65' }}>
            {challenge.description}
          </div>
        </div>

        {/* Multi-file Repository Structure if present */}
        {challenge.repository_structure && challenge.repository_structure.files && (
          <div className="card animate-fade-in-up stagger-2" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
              Repository File Architecture
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
              This challenge includes a multi-file repository structure with isolated services, helper utilities, and test suites.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {challenge.repository_structure.files.map((file) => (
                <div
                  key={file.path}
                  style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.6rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}
                >
                  <span style={{ fontSize: '1rem' }}>{file.path.endsWith('.py') ? '🐍' : '📄'}</span>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {file.path}
                    </span>
                  </div>
                  {file.is_readonly && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }} title="Read-only file">
                      🔒
                    </span>
                  )}
                  {file.is_test && (
                    <span className="badge badge-SECURITY" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                      test
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Previous Evaluation Attempts */}
        {hasAttempts && (
          <div className="card animate-fade-in-up stagger-3" style={{ padding: '2.25rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                Your Recent Submissions for this Mission
              </h2>
              <Link to="/submissions" style={{ fontSize: '0.88rem', color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>
                View All Submissions &rarr;
              </Link>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {attemptsData.results.map((item) => (
                <div
                  key={item.id}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.85rem 1.25rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={`status-pill ${item.status === 'PASSED' ? 'status-passed' : item.status === 'FAILED' ? 'status-failed' : 'status-pending'}`}>
                      <span className="status-dot" />
                      <span>{item.status}</span>
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                      Score: {item.score ?? 0}/100
                    </span>
                  </div>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {new Date(item.submitted_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
