import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';
import {
  TechLogo,
  getSkillIcon,
  getIncidentIcon,
  Bug,
  Globe,
  ShieldCheck,
  Activity,
  Layers,
  FlaskConical,
  Zap,
  Folder,
  FileCode2,
  Terminal,
  Award,
  CheckCircle2,
  BarChart3,
  Cpu,
} from '../components/RealisticIcons';

export default function Home() {
  const { isAuthenticated } = useAuth();

  const techStack = [
    { name: 'React', category: 'Frontend Architecture', logo: 'react', accent: '#3B82F6', bg: '#EFF6FF', border: '#DBEAFE' },
    { name: 'FastAPI', category: 'High-Performance Backend', logo: 'fastapi', accent: '#059669', bg: '#ECFDF5', border: '#A7F3D0' },
    { name: 'PostgreSQL', category: 'Relational Database', logo: 'postgresql', accent: '#2563EB', bg: '#EFF6FF', border: '#BFDBFE' },
    { name: 'Redis', category: 'In-Memory Cache & Queue', logo: 'redis', accent: '#DC2626', bg: '#FEF2F2', border: '#FECACA' },
    { name: 'Celery', category: 'Async Task Pipeline', logo: 'celery', accent: '#047857', bg: '#ECFDF5', border: '#A7F3D0' },
    { name: 'Docker', category: 'Isolated Sandbox Execution', logo: 'docker', accent: '#0284C7', bg: '#F0F9FF', border: '#BAE6FD' },
    { name: 'Monaco Editor', category: 'VS Code Editor Core', logo: 'monaco', accent: '#6D28D9', bg: '#F5F3FF', border: '#DDD6FE' },
  ];

  const steps = [
    {
      num: '01',
      title: 'Investigate',
      desc: 'Inspect real-world multi-file repositories with production defect alerts.',
      panelClass: 'panel-pastel-lavender',
      accent: 'var(--pastel-lavender-text)',
    },
    {
      num: '02',
      title: 'Diagnose',
      desc: 'Trace call graphs, test fixtures, and structural dependencies across modules.',
      panelClass: 'panel-pastel-blue',
      accent: 'var(--pastel-blue-text)',
    },
    {
      num: '03',
      title: 'Refactor',
      desc: 'Fix logic faults, remediate security vulnerabilities, and optimize bottlenecks inside Monaco.',
      panelClass: 'panel-pastel-mint',
      accent: 'var(--pastel-mint-text)',
    },
    {
      num: '04',
      title: 'Evaluate',
      desc: 'Isolated Docker sandboxes execute authoritative test suites against hidden workloads.',
      panelClass: 'panel-pastel-peach',
      accent: 'var(--pastel-peach-text)',
    },
    {
      num: '05',
      title: 'Benchmark',
      desc: 'Receive deterministic competency telemetry across 6 verified engineering dimensions.',
      panelClass: 'panel-pastel-yellow',
      accent: 'var(--pastel-yellow-text)',
    },
  ];

  const demoSkills = [
    { key: 'problem_solving', name: 'Problem Solving', score: 88, color: '#1D4ED8' },
    { key: 'debugging', name: 'Debugging', score: 92, color: '#DC2626' },
    { key: 'security', name: 'Security', score: 85, color: '#6D28D9' },
    { key: 'performance', name: 'Performance', score: 90, color: '#047857' },
    { key: 'code_quality', name: 'Code Quality', score: 84, color: '#D97706' },
    { key: 'testing', name: 'Testing', score: 87, color: '#0E7490' },
  ];

  return (
    <div className="home-page" style={{ width: '100%', overflowX: 'hidden' }}>
      {/* 1. HERO SECTION */}
      <section className="page-container" style={{ paddingTop: '4.5rem', paddingBottom: '4.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '3rem', alignItems: 'center' }}>
          {/* Left Column: Hero Content */}
          <div className="animate-fade-in-up">
            <div className="gency-hero-badge" style={{ marginBottom: '1.25rem' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--accent-primary)', display: 'inline-block' }} />
              <span>Practice Software Engineering. Not Just Coding.</span>
            </div>

            <h1 className="hero-title animate-fade-in-up stagger-1" style={{ marginBottom: '1.25rem' }}>
              Real Repositories.<br />
              <span className="accent-gradient">Real Engineering.</span><br />
              Zero Toy Puzzles.
            </h1>

            <p className="hero-subtitle animate-fade-in-up stagger-2" style={{ marginBottom: '1.75rem' }}>
              Immerse yourself in authentic multi-file codebases. Diagnose structural regressions, repair REST APIs, patch security exploits, and optimize bottlenecks inside hardened Docker sandboxes.
            </p>

            {/* CTAs */}
            <div className="animate-fade-in-up stagger-3" style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap', marginBottom: '1.85rem' }}>
              <Link
                to={isAuthenticated ? '/dashboard' : '/challenges'}
                className="btn-saas btn-saas-primary"
                style={{ padding: '0.85rem 2.2rem', fontSize: '1rem' }}
              >
                <span>Start Practicing</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
              <Link
                to="/challenges"
                className="btn-saas btn-saas-secondary"
                style={{ padding: '0.85rem 2rem', fontSize: '1rem' }}
              >
                View Challenges
              </Link>
            </div>

            {/* Floating Trust Pills */}
            <div className="animate-fade-in-up stagger-4" style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
              <span className="badge badge-API" style={{ padding: '0.35rem 0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <CheckCircle2 size={13} /> Multi-File Repositories
              </span>
              <span className="badge badge-SECURITY" style={{ padding: '0.35rem 0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <CheckCircle2 size={13} /> Docker Sandboxes
              </span>
              <span className="badge badge-PERFORMANCE" style={{ padding: '0.35rem 0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <CheckCircle2 size={13} /> Deterministic Scoring
              </span>
            </div>
          </div>

          {/* Right Column: Light Pastel Interactive Workspace Preview */}
          <div className="animate-scale-in stagger-3" style={{ position: 'relative' }}>
            <div
              className="card"
              style={{
                borderRadius: '24px',
                border: '1px solid var(--border-color)',
                background: '#ffffff',
                boxShadow: 'var(--shadow-xl)',
                overflow: 'hidden',
              }}
            >
              {/* Window Header */}
              <div style={{ background: '#FAF9FD', padding: '0.85rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '7px' }}>
                  <span style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#F87171' }} />
                  <span style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#FBBF24' }} />
                  <span style={{ width: 11, height: 11, borderRadius: '50%', backgroundColor: '#34D399' }} />
                </div>
                <div style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  codefoundry / services / report_generator.py
                </div>
                <div style={{ display: 'flex', gap: '0.45rem' }}>
                  <span className="badge badge-passed" style={{ fontSize: '0.7rem', padding: '0.2rem 0.55rem' }}>
                    ● Docker Live
                  </span>
                </div>
              </div>

              {/* Mockup Workspace Body */}
              <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', minHeight: '240px' }}>
                {/* File Tree Sidebar */}
                <div style={{ background: '#FAF9FD', borderRight: '1px solid var(--border-color)', padding: '0.85rem', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Repository
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.2rem 0', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Folder size={13} /> src/
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.2rem 0 0.2rem 0.6rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Folder size={13} /> models/
                  </div>
                  <div style={{ color: 'var(--pastel-lavender-text)', fontWeight: 700, padding: '0.2rem 0.5rem', background: 'var(--pastel-lavender)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <FileCode2 size={13} /> report_gen.py
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.2rem 0 0.2rem 0.6rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <FileCode2 size={13} /> queries.py
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.2rem 0', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Folder size={13} /> tests/
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.2rem 0 0.2rem 0.6rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <FileCode2 size={13} /> test_perf.py
                  </div>
                </div>

                {/* Editor Content Area */}
                <div style={{ padding: '1.15rem 1.35rem', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', lineHeight: '1.6', background: '#ffffff', color: '#25243A' }}>
                  <div><span style={{ color: '#6D45C5', fontWeight: 700 }}>def</span> <span style={{ color: '#1E5EA8', fontWeight: 600 }}>generate_aggregate_report</span>(dataset: <span style={{ color: '#0E7490' }}>QuerySet</span>):</div>
                  <div style={{ paddingLeft: '1rem', color: '#8E8D9E' }}># Refactored O(N) streaming hash map</div>
                  <div style={{ paddingLeft: '1rem' }}><span style={{ color: '#6D45C5', fontWeight: 700 }}>return</span> dataset.annotate(</div>
                  <div style={{ paddingLeft: '2rem' }}>total_volume=Sum(<span style={{ color: '#196F4B' }}>'amount'</span>),</div>
                  <div style={{ paddingLeft: '2rem' }}>avg_latency=Avg(<span style={{ color: '#196F4B' }}>'duration_ms'</span>)</div>
                  <div style={{ paddingLeft: '1rem' }}>).iterator(chunk_size=<span style={{ color: '#9E4A15' }}>500</span>)</div>
                </div>
              </div>

              {/* Evaluation Result Footer */}
              <div style={{ background: 'var(--pastel-mint-light)', borderTop: '1px solid var(--pastel-mint-border)', padding: '0.85rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <CheckCircle2 size={16} color="var(--pastel-mint-text)" />
                  <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--pastel-mint-text)' }}>
                    Sandbox Evaluator: 4/4 Tests Passed (Execution: 42ms · Memory: 28MB)
                  </span>
                </div>
                <span className="badge badge-PERFORMANCE" style={{ fontSize: '0.74rem' }}>
                  Score: 100/100
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. ALTERNATING PASTEL PANELS: 5-STEP ENGINEERING WORKFLOW */}
      <section id="features" style={{ backgroundColor: '#ffffff', padding: '4.5rem 0', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.75rem' }}>
            <span>Structured Progression</span>
          </div>
          <h2 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            The Engineering Simulation Workflow
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', maxWidth: '620px', margin: '0 auto 2.5rem' }}>
            From diagnosis to sandbox verification, practice the exact lifecycle of real production engineering work.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1.25rem' }}>
            {steps.map((step, idx) => (
              <div
                key={step.num}
                className={`card animate-fade-in-up ${step.panelClass}`}
                style={{
                  padding: '1.6rem 1.35rem',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.65rem',
                  animationDelay: `${idx * 60}ms`,
                  borderRadius: '20px',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: '12px',
                    background: '#ffffff',
                    color: step.accent,
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: 'var(--shadow-sm)',
                    border: '1px solid rgba(0,0,0,0.05)',
                  }}
                >
                  {step.num}
                </div>
                <h3 style={{ fontSize: '1.18rem', fontWeight: 800, margin: '0.2rem 0 0' }}>{step.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5, margin: 0 }}>
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. CORE CHALLENGE DOMAINS (ALTERNATING PASTEL CARDS) */}
      <section style={{ padding: '4.5rem 0' }}>
        <div className="page-container" style={{ padding: '0 1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '3rem', alignItems: 'center' }}>
            {/* Left Column: Description & Skill Pillars */}
            <div>
              <div className="gency-hero-badge" style={{ marginBottom: '0.75rem' }}>
                <span>Core Competencies</span>
              </div>
              <h2 style={{ fontSize: '2.25rem', fontWeight: 800, marginBottom: '0.85rem', lineHeight: 1.2 }}>
                Build verified abilities,<br />not memorized puzzles.
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', marginBottom: '1.65rem', lineHeight: 1.6 }}>
                Every challenge is mapped directly to the competencies evaluated by engineering teams and technical leads:
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem', marginBottom: '1.85rem' }}>
                {[
                  { title: 'Bug Fixing', icon: <Bug size={20} color="#DC2626" />, desc: 'Root cause isolation & patch', bg: 'var(--badge-bug-fix-bg)', border: 'var(--badge-bug-fix-border)' },
                  { title: 'REST APIs', icon: <Globe size={20} color="#1D4ED8" />, desc: 'Serialization & HTTP schemas', bg: 'var(--badge-api-bg)', border: 'var(--badge-api-border)' },
                  { title: 'Security', icon: <ShieldCheck size={20} color="#6D28D9" />, desc: 'Access control & RBAC policies', bg: 'var(--badge-security-bg)', border: 'var(--badge-security-border)' },
                  { title: 'Performance', icon: <Activity size={20} color="#047857" />, desc: 'Algorithmic O(N) optimization', bg: 'var(--badge-performance-bg)', border: 'var(--badge-performance-border)' },
                ].map((item) => (
                  <div key={item.title} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: item.bg, border: `1px solid ${item.border}`, padding: '0.85rem 1rem', borderRadius: '14px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center' }}>{item.icon}</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>{item.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>

              <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.85rem 2rem', fontSize: '0.98rem' }}>
                <span>Browse Challenge Catalog</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>

            {/* Right Column: Challenge Spotlight Card */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div
                className="card panel-pastel-blue animate-fade-in-up"
                style={{
                  padding: '2rem',
                  borderRadius: '24px',
                  boxShadow: 'var(--shadow-md)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div>
                    <span className="badge badge-SECURITY" style={{ marginBottom: '0.45rem', display: 'inline-block' }}>
                      Security Remediations
                    </span>
                    <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>
                      The Exposed Admin Endpoint
                    </h3>
                  </div>
                  <span className="badge badge-INTERMEDIATE">Intermediate</span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.94rem', marginBottom: '1.35rem', lineHeight: 1.55 }}>
                  Investigate a production API service exposing sensitive administrative actions. Remediate privilege escalation vulnerabilities, verify RBAC roles, and enforce JWT claims.
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.84rem', color: 'var(--text-muted)' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                      <Terminal size={14} color="#3B82F6" /> Python / FastAPI
                    </span>
                    <span>•</span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                      <Award size={14} color="#C77A14" /> 300 Points
                    </span>
                  </div>
                  <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}>
                    <span>Try Challenge</span>
                    <span className="btn-arrow-icon">→</span>
                  </Link>
                </div>
              </div>

              {/* Verified Telemetry Pill Card */}
              <div
                className="card panel-pastel-mint"
                style={{
                  padding: '1.15rem 1.5rem',
                  borderRadius: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div style={{ width: 38, height: 38, borderRadius: '50%', background: '#ffffff', color: 'var(--pastel-mint-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1rem', boxShadow: 'var(--shadow-sm)' }}>
                    <ShieldCheck size={22} color="var(--pastel-mint-text)" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Exploit Vector Neutralized</div>
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>Automated test suite confirmed 403 Forbidden on unprivileged access</div>
                  </div>
                </div>
                <span className="badge badge-passed">+50 pts</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. SKILL ANALYTICS SECTION */}
      <section style={{ backgroundColor: '#ffffff', padding: '4.5rem 0', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.75rem' }}>
            <span>Verified Evaluation</span>
          </div>
          <h2 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            Deterministic Skill Measurement
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', maxWidth: '640px', margin: '0 auto 2.5rem' }}>
            Every challenge submission produces verified engineering telemetry across six fundamental dimensions.
          </p>

          {/* Skill Dashboard Mockup Container */}
          <div
            className="card panel-pastel-lavender animate-fade-in-up"
            style={{
              maxWidth: '880px',
              margin: '0 auto',
              padding: '2.25rem 2.5rem',
              borderRadius: '24px',
              textAlign: 'left',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <div>
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Illustrative Engineering Readiness Profile
                </span>
                <h3 style={{ fontSize: '1.45rem', fontWeight: 800, margin: '0.2rem 0 0' }}>
                  Overall Skill Score
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.6rem', fontWeight: 900, color: 'var(--accent-primary)', lineHeight: 1 }}>
                  89
                </span>
                <span style={{ color: 'var(--text-muted)', fontWeight: 600, fontSize: '1rem' }}>/ 100</span>
              </div>
            </div>

            {/* 6 Skill Progress Bars */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
              {demoSkills.map((sk) => (
                <div key={sk.name} style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem' }}>
                    <span style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {getSkillIcon(sk.key, 16, sk.color)} {sk.name}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: sk.color }}>
                      {sk.score}%
                    </span>
                  </div>
                  <AnimatedProgress value={sk.score} color={sk.color} height={8} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 5. RECRUITER TALENT OVERVIEW */}
      <section style={{ padding: '4.5rem 0' }}>
        <div className="page-container" style={{ padding: '0 1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '3rem', alignItems: 'center' }}>
            {/* Left: Recruiter Matrix Card */}
            <div
              className="card panel-pastel-peach animate-fade-in-up"
              style={{
                borderRadius: '24px',
                padding: '1.75rem',
                boxShadow: 'var(--shadow-md)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                  <BarChart3 size={20} color="var(--accent-primary)" />
                  <span style={{ fontWeight: 800, fontSize: '0.98rem' }}>Candidate Evaluation Matrix</span>
                </div>
                <span className="badge badge-passed">Verified Data</span>
              </div>

              {/* Candidate Item 1 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#ffffff', borderRadius: '12px', marginBottom: '0.65rem', boxShadow: 'var(--shadow-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--pastel-lavender)', color: 'var(--pastel-lavender-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.82rem' }}>AL</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem' }}>@alex_dev</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>14 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-PERFORMANCE">Score: 92/100</span>
              </div>

              {/* Candidate Item 2 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#ffffff', borderRadius: '12px', marginBottom: '0.65rem', boxShadow: 'var(--shadow-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--pastel-blue)', color: 'var(--pastel-blue-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.82rem' }}>SA</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem' }}>@sarah_eng</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>18 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-SECURITY">Score: 95/100</span>
              </div>

              {/* Candidate Item 3 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#ffffff', borderRadius: '12px', boxShadow: 'var(--shadow-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--pastel-mint)', color: 'var(--pastel-mint-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.82rem' }}>MK</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.88rem' }}>@mike_code</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>11 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-API">Score: 88/100</span>
              </div>
            </div>

            {/* Right: Explanations */}
            <div>
              <div className="gency-hero-badge" style={{ marginBottom: '0.75rem' }}>
                <span>For Engineering Recruiters</span>
              </div>
              <h2 style={{ fontSize: '2.25rem', fontWeight: 800, marginBottom: '0.85rem', lineHeight: 1.2 }}>
                Hire based on verified code,<br />not resume claims.
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', marginBottom: '1.45rem', lineHeight: 1.6 }}>
                Recruiters and hiring managers review objective, reproducible candidate assessments generated by automated test runners.
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {[
                  'Reproducible test results evaluated inside hardened Linux containers',
                  'Granular skill breakdown across 6 core software engineering dimensions',
                  'Filter candidates by domain strength, points earned, and overall score',
                  'Direct side-by-side candidate comparison matrix',
                ].map((text) => (
                  <li key={text} style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', fontSize: '0.94rem', color: 'var(--text-secondary)' }}>
                    <CheckCircle2 size={16} color="var(--accent-primary)" />
                    <span>{text}</span>
                  </li>
                ))}
              </ul>

              <Link to="/recruiter" className="btn-saas btn-saas-primary" style={{ padding: '0.85rem 2rem', fontSize: '0.98rem' }}>
                <span>Explore Recruiter Hub</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 6. PLATFORM INFRASTRUCTURE PILLARS */}
      <section id="docs" style={{ backgroundColor: '#ffffff', padding: '4rem 0', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.75rem' }}>
            <span>Production Stack</span>
          </div>
          <h2 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '0.5rem' }}>
            Built With Modern Engineering Tools
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '600px', margin: '0 auto 2.25rem' }}>
            CodeFoundry leverages the same technologies that power high-scale production systems.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem' }}>
            {techStack.map((tech) => (
              <div
                key={tech.name}
                className="card"
                style={{
                  padding: '1.35rem 1rem',
                  borderRadius: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.55rem',
                  textAlign: 'center',
                  boxShadow: 'var(--shadow-sm)',
                  background: '#ffffff',
                  border: `1px solid ${tech.border}`,
                  transition: 'all var(--transition-spring)',
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '12px',
                    background: tech.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <TechLogo name={tech.logo} size={28} />
                </div>
                <span style={{ fontWeight: 800, fontSize: '0.98rem', color: 'var(--text-primary)' }}>{tech.name}</span>
                <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{tech.category}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 7. FINAL CALL TO ACTION (PASTEL GRADIENT) */}
      <section className="page-container" style={{ padding: '3rem 1.5rem 5rem' }}>
        <div
          className="card panel-pastel-lavender animate-fade-in-up"
          style={{
            padding: '3.5rem 2.5rem',
            textAlign: 'center',
            borderRadius: '28px',
            boxShadow: 'var(--shadow-lg)',
          }}
        >
          <h2 style={{ fontSize: 'clamp(1.9rem, 3.8vw, 2.5rem)', fontWeight: 800, marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            Start Practicing Software Engineering Today
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '580px', margin: '0 auto 2rem' }}>
            Real codebases. Real bugs. Real engineering practice.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link
              to={isAuthenticated ? '/dashboard' : '/register'}
              className="btn-saas btn-saas-primary"
              style={{ padding: '0.85rem 2.25rem', fontSize: '1.02rem' }}
            >
              <span>Get Started</span>
              <span className="btn-arrow-icon">→</span>
            </Link>
            <Link
              to="/challenges"
              className="btn-saas btn-saas-secondary"
              style={{ padding: '0.85rem 2.1rem', fontSize: '1.02rem' }}
            >
              Explore Catalog
            </Link>
          </div>
        </div>
      </section>

      {/* 8. FOOTER */}
      <footer style={{ borderTop: '1px solid var(--border-color)', background: '#ffffff', padding: '2.5rem 0 2rem' }}>
        <div className="page-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', padding: '0 1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="logo-icon" style={{ width: 28, height: 28, fontSize: '0.8rem' }}>&gt;_</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.15rem' }}>CodeFoundry</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', margin: 0 }}>
              Practice Software Engineering. Not Just Coding.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1.75rem', flexWrap: 'wrap', fontSize: '0.9rem' }}>
            <Link to="/challenges" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600 }}>
              Challenges
            </Link>
            <Link to="/leaderboard" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600 }}>
              Leaderboard
            </Link>
            <Link to="/recruiter" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600 }}>
              Recruiters
            </Link>
            <a href="#features" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600 }}>
              Workflow
            </a>
          </div>
        </div>
        <div style={{ textAlign: 'center', marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-light)', fontSize: '0.82rem' }}>
          © {new Date().getFullYear()} CodeFoundry. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
