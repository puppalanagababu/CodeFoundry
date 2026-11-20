import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { getChallengeSubmissions } from '../api/submissions';
import Loading from '../components/Loading';
import {
  getIncidentIcon,
  FileCode2,
  File,
  Lock,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Terminal,
} from '../components/RealisticIcons';

const INCIDENT_TYPE_CONFIG = {
  BUG_FIX: {
    badge: 'P1 Production Defect Alert',
    headline: 'CRITICAL RUNTIME REGRESSION DETECTED',
    lead: 'A critical production module is throwing runtime exceptions and returning corrupted state under live workloads.',
    color: '#DC2626',
    panelClass: 'panel-pastel-peach',
    diagnostics: [
      'Scanning repository modules and dependency callgraphs...',
      'Tracing runtime exception callstacks in sandbox...',
      'Analyzing regression test failure vectors...',
      'Root cause isolated in service routine logic!',
    ],
  },
  DEBUGGING: {
    badge: 'Fault Localization Alert · Subsystem Anomaly',
    headline: 'UNEXPECTED BEHAVIOR IN SERVICE ROUTINE',
    lead: 'Runtime tracing detected invalid control flow branches and state corruption during execution.',
    color: '#DC2626',
    panelClass: 'panel-pastel-peach',
    diagnostics: [
      'Scanning repository modules and callgraphs...',
      'Tracing runtime exception callstacks...',
      'Analyzing regression test failure vectors...',
      'Root cause isolated in service routines!',
    ],
  },
  API: {
    badge: 'REST API Schema Contract Violation',
    headline: 'API SERIALIZATION & PAYLOAD ANOMALY',
    lead: 'An HTTP service endpoint is returning invalid JSON structures and breaking client contract specifications.',
    color: '#1D4ED8',
    panelClass: 'panel-pastel-blue',
    diagnostics: [
      'Interrogating REST endpoint route handlers...',
      'Validating JSON response serialization...',
      'Testing status codes against API contract specifications...',
      'Payload schema mismatch detected!',
    ],
  },
  SECURITY: {
    badge: 'CVE / Privilege Escalation Vulnerability',
    headline: 'UNAUTHORIZED PRIVILEGE ESCALATION',
    lead: 'Sensitive endpoints lack role-based access control (RBAC) validation, permitting unauthorized state mutations.',
    color: '#6D28D9',
    panelClass: 'panel-pastel-lavender',
    diagnostics: [
      'Auditing authentication layers and JWT headers...',
      'Testing endpoints against privilege escalation payloads...',
      'Verifying role-based access control policies...',
      'Security bypass vector isolated!',
    ],
  },
  PERFORMANCE: {
    badge: 'Resource Ceiling Saturation Alert',
    headline: 'QUADRATIC COMPLEXITY & MEMORY BREACH',
    lead: 'Algorithmic complexity O(N²) breaches the 128MB container memory limit and triggers execution timeouts.',
    color: '#047857',
    panelClass: 'panel-pastel-mint',
    diagnostics: [
      'Profiling CPU cycles and memory allocations...',
      'Analyzing nested loops and duplicate operations...',
      'Measuring latency against strict execution limits...',
      'O(N²) quadratic bottleneck detected!',
    ],
  },
  DATABASE: {
    badge: 'Data Persistence & Integrity Alert',
    headline: 'TRANSACTION CORRUPTION & RELATIONAL INCONSISTENCY',
    lead: 'Relational queries or transactional rollbacks fail to maintain data consistency across entities.',
    color: '#9A3412',
    panelClass: 'panel-pastel-peach',
    diagnostics: [
      'Inspecting relational queries and transactional blocks...',
      'Verifying foreign key constraints and dataset states...',
      'Auditing index lookups against query telemetry...',
      'Data corruption pattern isolated!',
    ],
  },
  TESTING: {
    badge: 'Regression Suite Coverage Gap',
    headline: 'UNVERIFIED EDGE CASES & ASSERTION DEFICIT',
    lead: 'Missing test assertions and unverified boundary invariants leave production workflows exposed.',
    color: '#0E7490',
    panelClass: 'panel-pastel-blue',
    diagnostics: [
      'Auditing unit and integration test coverage...',
      'Checking test fixtures and assertions against edge cases...',
      'Measuring mutation test survival rates...',
      'Critical untested pathway discovered!',
    ],
  },
};

const DEFAULT_INCIDENT_CONFIG = {
  badge: 'Engineering Implementation Required',
  headline: 'PRODUCTION SPECIFICATION INCOMPLETE',
  lead: 'A core repository service requires implementation and verification against system specifications.',
  color: '#6D45C5',
  panelClass: 'panel-pastel-lavender',
  diagnostics: [
    'Scanning codebase structure and dependencies...',
    'Inspecting interface contracts and requirements...',
    'Checking runtime behavior in Docker sandbox...',
    'Engineering scenario confirmed!',
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
        <div style={{ background: 'var(--accent-danger-light)', border: '1px solid var(--accent-danger-border)', color: 'var(--accent-danger)', borderRadius: 'var(--radius-md)', padding: '1.5rem', textAlign: 'center' }}>
          <p style={{ marginBottom: '1rem', fontSize: '1.05rem', fontWeight: 600 }}>{error || 'Challenge not found.'}</p>
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
          className={`card ${incidentConfig.panelClass} animate-scale-in`}
          style={{
            textAlign: 'center',
            marginBottom: '2.5rem',
            padding: '3.5rem 2rem',
            borderRadius: '24px',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#ffffff',
              border: `1px solid ${incidentConfig.color}40`,
              color: incidentConfig.color,
              fontSize: '0.85rem',
              fontWeight: 800,
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-full)',
              marginBottom: '1.25rem',
              boxShadow: 'var(--shadow-sm)',
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
            style={{ margin: '0 auto 2rem', maxWidth: '620px', fontSize: '1.05rem', color: 'var(--text-secondary)' }}
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
            <span className={`badge badge-${challenge.difficulty}`}>
              {challenge.difficulty}
            </span>
            <span className={`badge badge-${challenge.challenge_type}`}>
              {challenge.challenge_type?.replace('_', ' ')}
            </span>
            <span className="badge badge-API">
              {challenge.points} PTS
            </span>
            <span className="badge badge-BEGINNER">
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
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.65rem',
              }}
              aria-label="Investigate engineering incident"
            >
              <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                {getIncidentIcon(challenge.challenge_type, 18, '#ffffff')}
              </span>
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
                fontWeight: 600,
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
          className="card panel-pastel-lavender animate-fade-in-up"
          style={{ textAlign: 'center', marginBottom: '2.5rem', padding: '3rem 2rem', borderRadius: '24px' }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#ffffff',
              border: '1px solid var(--pastel-lavender-border)',
              color: 'var(--pastel-lavender-text)',
              fontSize: '0.82rem',
              fontWeight: 800,
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-full)',
              marginBottom: '1rem',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <span className="spinner-icon" style={{ width: 10, height: 10, borderWidth: 1.5 }} />
            <span>RUNNING SYSTEM DIAGNOSTIC</span>
          </div>

          <h2 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Investigating Codebase Telemetry...
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', marginBottom: '1.75rem' }}>
            Inspecting isolated Docker sandbox, file callgraphs, and failing assertions.
          </p>

          <div
            style={{
              maxWidth: '680px',
              margin: '0 auto',
              background: '#1F1E2E',
              borderRadius: '16px',
              padding: '1.5rem',
              textAlign: 'left',
              color: '#F0EFF6',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #36344B', paddingBottom: '0.6rem', marginBottom: '0.85rem', fontSize: '0.78rem', color: '#B4B3C2' }}>
              <span>$ codefoundry diagnose --sandbox container-01</span>
              <button
                type="button"
                onClick={handleQuickReveal}
                style={{ background: 'transparent', border: 'none', color: '#D7C3F8', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700 }}
              >
                Skip [Instant]
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: '#8E8D9E' }}>
                [0.00s] Initializing diagnostic telemetry in isolated Docker sandbox...
              </div>
              {diagnosticStep >= 1 && (
                <div className="animate-fade-in-up" style={{ color: '#DCEBFF' }}>
                  [0.30s] {incidentConfig.diagnostics[0]}
                </div>
              )}
              {diagnosticStep >= 2 && (
                <div className="animate-fade-in-up" style={{ color: '#FEF3D6' }}>
                  [0.65s] {incidentConfig.diagnostics[1]}
                </div>
              )}
              {diagnosticStep >= 3 && (
                <div className="animate-fade-in-up" style={{ color: '#FCE7D8' }}>
                  [1.00s] {incidentConfig.diagnostics[2]}
                </div>
              )}
              {diagnosticStep >= 4 && (
                <div className="animate-fade-in-up" style={{ color: '#D8F5E5', fontWeight: 700 }}>
                  [1.35s] [ROOT CAUSE IDENTIFIED] {incidentConfig.diagnostics[3]}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2.5 BURST STATE */}
      {revealState === 'burst' && (
        <div
          className="card panel-pastel-mint animate-fade-in-up"
          style={{
            textAlign: 'center',
            marginBottom: '2.5rem',
            padding: '4rem 2rem',
            borderRadius: '24px',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.65rem',
              background: '#ffffff',
              border: '1px solid var(--pastel-mint-border)',
              color: 'var(--pastel-mint-text)',
              fontSize: '0.94rem',
              fontWeight: 800,
              padding: '0.5rem 1.4rem',
              borderRadius: 'var(--radius-full)',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <CheckCircle2 size={16} />
            <span>ROOT CAUSE ISOLATED IN REPOSITORY</span>
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '1.25rem' }}>
            Preparing Multi-File Repository Environment...
          </h2>
        </div>
      )}

      {/* 3. REVEALED STATE: HERO BRIEFING & ENTER CODEBASE */}
      {revealState === 'revealed' && (
        <div
          className="card panel-pastel-blue animate-fade-in-up"
          style={{ padding: '2.5rem', marginBottom: '2.5rem', borderRadius: '24px', boxShadow: 'var(--shadow-sm)' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.75rem' }}>
            <div style={{ flex: '1 1 500px' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                <span className="badge" style={{ backgroundColor: '#ffffff', color: incidentConfig.color, border: `1px solid ${incidentConfig.color}40`, display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <AlertTriangle size={12} color={incidentConfig.color} /> DEFECT IDENTIFIED
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
                  <span className="badge badge-API">New Challenge</span>
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
                  padding: '0.9rem 2.25rem',
                  fontSize: '1rem',
                }}
              >
                <span>ENTER WORKSPACE</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.35rem' }}>
            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 700 }}>Language</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.programming_language}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 700 }}>Points</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.points} pts</span>
            </div>
            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 700 }}>Time Limit</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.time_limit}s</span>
            </div>
            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem', fontWeight: 700 }}>Memory Limit</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{challenge.memory_limit} MB</span>
            </div>
          </div>
        </div>
      )}

      {/* Challenge Information & Briefing Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        {/* Description & Requirements */}
        <div className="card animate-fade-in-up stagger-1" style={{ padding: '2.5rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '1.25rem' }}>
            Mission Briefing &amp; Requirements
          </h2>
          <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.96rem', lineHeight: '1.65' }}>
            {challenge.description}
          </div>
        </div>

        {/* Multi-file Repository Structure */}
        {challenge.repository_structure && challenge.repository_structure.files && (
          <div className="card animate-fade-in-up stagger-2" style={{ padding: '2.5rem', borderRadius: '24px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.65rem' }}>
              Repository File Architecture
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '1.35rem' }}>
              This challenge includes a multi-file repository structure with isolated services, helper utilities, and test suites.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.85rem' }}>
              {challenge.repository_structure.files.map((file) => (
                <div
                  key={file.path}
                  style={{ padding: '0.85rem 1.15rem', display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.65rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: '14px', boxShadow: 'var(--shadow-sm)' }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                    {file.path.endsWith('.py') ? (
                      <FileCode2 size={16} color="#3B82F6" />
                    ) : (
                      <File size={16} color="#64748B" />
                    )}
                  </span>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {file.path}
                    </span>
                  </div>
                  {file.is_readonly && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', color: '#EF4444' }} title="Read-only protected file">
                      <Lock size={12} />
                    </span>
                  )}
                  {file.is_test && (
                    <span className="badge badge-SECURITY" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                      <CheckCircle2 size={10} /> test
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Previous Evaluation Attempts */}
        {hasAttempts && (
          <div className="card animate-fade-in-up stagger-3" style={{ padding: '2.5rem', borderRadius: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                Your Recent Submissions for this Mission
              </h2>
              <Link to="/submissions" style={{ fontSize: '0.9rem', color: 'var(--accent-primary)', fontWeight: 700, textDecoration: 'none' }}>
                View All Submissions &rarr;
              </Link>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {attemptsData.results.map((item) => (
                <div
                  key={item.id}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.95rem 1.35rem', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: '14px', boxShadow: 'var(--shadow-sm)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.1rem' }}>
                    <span className={`status-pill ${item.status === 'PASSED' ? 'status-passed' : item.status === 'FAILED' ? 'status-failed' : 'status-pending'}`}>
                      <span className="status-dot" />
                      <span>{item.status}</span>
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.92rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                      Score: {item.score ?? 0}/100
                    </span>
                  </div>
                  <span style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
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
