import React, { useState } from 'react';

const VIEWPORT_BURST_TRAJECTORIES = [
  { dx: '-36vw', dy: '-36vh', rot: '-18deg', scale: 1.2, delay: '0ms' },   // Top-Left Far
  { dx: '0vw',   dy: '-40vh', rot: '4deg',   scale: 1.25, delay: '40ms' },  // Top-Center High
  { dx: '36vw',  dy: '-34vh', rot: '16deg',  scale: 1.2, delay: '20ms' },   // Top-Right Far
  { dx: '-42vw', dy: '-4vh',  rot: '-12deg', scale: 1.3, delay: '60ms' },   // Center-Left Far
  { dx: '42vw',  dy: '6vh',   rot: '14deg',  scale: 1.3, delay: '30ms' },   // Center-Right Far
  { dx: '-35vw', dy: '36vh',  rot: '-15deg', scale: 1.15, delay: '50ms' },  // Bottom-Left Low
  { dx: '-2vw',  dy: '40vh',  rot: '-6deg',  scale: 1.25, delay: '40ms' },  // Bottom-Center
  { dx: '36vw',  dy: '35vh',  rot: '18deg',  scale: 1.15, delay: '20ms' },  // Bottom-Right Low
  { dx: '-20vw', dy: '-18vh', rot: '-8deg',  scale: 1.1, delay: '50ms' },   // Inner Top-Left
  { dx: '22vw',  dy: '-16vh', rot: '10deg',  scale: 1.1, delay: '10ms' },   // Inner Top-Right
  { dx: '-18vw', dy: '18vh',  rot: '6deg',   scale: 1.05, delay: '30ms' },  // Inner Bottom-Left
  { dx: '20vw',  dy: '20vh',  rot: '-9deg',  scale: 1.05, delay: '50ms' },  // Inner Bottom-Right
];

const SIGNALS = [
  { icon: '🐛', label: 'BUG FIX MATRIX', desc: 'Fault Isolation & Logic Errors', color: '#ef4444' },
  { icon: '🔐', label: 'SECURITY AUDIT', desc: 'Auth, Injection & Access Guards', color: '#a855f7' },
  { icon: '⚡', label: 'PERFORMANCE TUNING', desc: 'Latency, CPU & Memory Optimization', color: '#10b981' },
  { icon: '🔵', label: 'API ARCHITECTURE', desc: 'REST, Schemas & Payload Contracts', color: '#3b82f6' },
  { icon: '💾', label: 'DATABASE ENGINES', desc: 'Transactions, Queries & Indexes', color: '#f59e0b' },
  { icon: '🧪', label: 'TEST AUTOMATION', desc: 'Edge Cases, Assertions & Mocks', color: '#06b6d4' },
];

export default function ScratchIntroOverlay({ onComplete }) {
  const [stage, setStage] = useState('idle'); // 'idle' | 'burst' | 'done'

  const handleTriggerBurst = () => {
    if (stage === 'burst') return;

    const prefersReducedMotion =
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      onComplete?.();
      return;
    }

    setStage('burst');
    setTimeout(() => {
      onComplete?.();
    }, 1050);
  };

  const handleSkip = (e) => {
    e?.stopPropagation();
    onComplete?.();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleTriggerBurst();
    } else if (e.key === 'Escape') {
      handleSkip();
    }
  };

  return (
    <>
      <div
        className="discovery-overlay-backdrop"
        role="dialog"
        aria-modal="true"
        aria-label="Click-to-Burst Entrance Experience"
        tabIndex={0}
        onKeyDown={handleKeyDown}
      >
        <div className="discovery-card-wrapper">
          {/* Header */}
          <div className="discovery-card-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="status-dot" style={{ backgroundColor: '#818cf8', width: 8, height: 8 }} />
              <strong style={{ color: '#fff', letterSpacing: '0.04em' }}>DEVFORGE // CLASSIFIED ACTIVE MISSIONS</strong>
            </span>
            <button
              type="button"
              onClick={handleSkip}
              style={{
                background: 'rgba(99, 102, 241, 0.12)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                color: '#a5b4fc',
                fontSize: '0.82rem',
                cursor: 'pointer',
                fontWeight: 600,
                padding: '0.35rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
              }}
              aria-label="Skip discovery intro"
            >
              Skip Intro →
            </button>
          </div>

          {/* Interactive Hero Surface Area */}
          <div className="discovery-surface-area" onClick={handleTriggerBurst}>
            <div style={{ textAlign: 'center', marginBottom: '0.5rem' }}>
              <span
                className="badge badge-SECURITY"
                style={{
                  fontSize: '0.8rem',
                  letterSpacing: '0.08em',
                  padding: '0.35rem 0.95rem',
                  background: 'rgba(99, 102, 241, 0.2)',
                  borderColor: 'rgba(99, 102, 241, 0.5)',
                  color: '#c7d2fe',
                }}
              >
                ⚡ MISSION DISCOVERY ENGINE
              </span>
            </div>

            {/* Giant Glowing "CLICK ME" Trigger CTA */}
            <div
              className="discovery-click-trigger"
              role="button"
              tabIndex={0}
              aria-label="Click to ignite problem burst"
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  color: '#38bdf8',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                }}
              >
                <span>💥 [ PRIMARY TRIGGER ]</span>
              </div>

              <div className="discovery-trigger-title">
                CLICK ME
              </div>

              <div style={{ color: '#cbd5e1', fontSize: '0.98rem', fontWeight: 500, maxWidth: '440px' }}>
                Touch or click anywhere to ignite &amp; unlock the active engineering scenario matrix
              </div>

              <div
                style={{
                  marginTop: '0.5rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.45rem 1.25rem',
                  background: 'linear-gradient(90deg, #4f46e5, #06b6d4)',
                  borderRadius: 'var(--radius-full)',
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: '0.86rem',
                  boxShadow: '0 0 20px rgba(79, 70, 229, 0.6)',
                }}
              >
                <span>IGNITE BURST</span>
                <span>⚡</span>
              </div>
            </div>

            {/* 6 Dimension Category Tiles Matrix */}
            <div className="discovery-grid-signals">
              {SIGNALS.map((sig) => (
                <div key={sig.label} className="discovery-signal-tile" style={{ borderColor: `${sig.color}45` }}>
                  <span style={{ fontSize: '1.45rem' }}>{sig.icon}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', fontWeight: 800, color: sig.color }}>
                    {sig.label}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.2 }}>
                    {sig.desc}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* FULL-VIEWPORT 12-CARD BURST EXPLOSION (Screen-Spanning) */}
      {stage === 'burst' && (
        <div className="scratch-fullscreen-burst-layer">
          <div className="burst-flash-layer" />
          <div
            className="burst-shockwave-ring"
            style={{ width: 140, height: 140, borderColor: '#818cf8', boxShadow: '0 0 60px #818cf8' }}
          />

          {/* 12 Viewport-Occupying Category Cards */}
          {SIGNALS.concat(SIGNALS).map((sig, index) => {
            const traj = VIEWPORT_BURST_TRAJECTORIES[index] || VIEWPORT_BURST_TRAJECTORIES[0];
            return (
              <div
                key={index}
                className="viewport-burst-card"
                style={{
                  '--dx': traj.dx,
                  '--dy': traj.dy,
                  '--rot': traj.rot,
                  '--scale': traj.scale,
                  animationDelay: traj.delay,
                  borderColor: `${sig.color}90`,
                  boxShadow: `0 16px 45px -8px rgba(0,0,0,0.9), 0 0 28px ${sig.color}60`,
                }}
              >
                <span style={{ fontSize: '1.35rem' }}>{sig.icon}</span>
                <span style={{ color: sig.color }}>{sig.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
