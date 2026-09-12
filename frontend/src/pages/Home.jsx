import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';

export default function Home() {
  const { isAuthenticated } = useAuth();

  const techStack = [
    { name: 'React', category: 'Frontend Architecture', icon: '⚛️' },
    { name: 'Django', category: 'Backend Framework', icon: '🎯' },
    { name: 'PostgreSQL', category: 'Relational Database', icon: '🐘' },
    { name: 'Redis', category: 'In-Memory Cache & Queue', icon: '⚡' },
    { name: 'Celery', category: 'Async Task Pipeline', icon: '🌿' },
    { name: 'Docker', category: 'Isolated Sandbox Execution', icon: '🐳' },
    { name: 'Monaco Editor', category: 'VS Code Editor Core', icon: '💻' },
  ];

  const steps = [
    {
      num: '01',
      title: 'Choose',
      desc: 'Pick a real-world challenge matching your learning goals.',
      color: '#6366f1',
    },
    {
      num: '02',
      title: 'Code',
      desc: 'Work inside a complete multi-file repository with realistic architectures.',
      color: '#3b82f6',
    },
    {
      num: '03',
      title: 'Submit',
      desc: 'Run your tests iteratively and submit your complete solution.',
      color: '#06b6d4',
    },
    {
      num: '04',
      title: 'Evaluate',
      desc: 'Automated test harnesses evaluate edge cases inside hardened Docker containers.',
      color: '#10b981',
    },
    {
      num: '05',
      title: 'Grow',
      desc: 'Track verified engineering skills and competency growth over time.',
      color: '#8b5cf6',
    },
  ];

  const demoSkills = [
    { name: 'Problem Solving', score: 88, color: '#3b82f6', icon: '⚡' },
    { name: 'Debugging', score: 92, color: '#f59e0b', icon: '🐛' },
    { name: 'Security', score: 85, color: '#8b5cf6', icon: '🛡️' },
    { name: 'Performance', score: 90, color: '#10b981', icon: '🚀' },
    { name: 'Code Quality', score: 84, color: '#64748b', icon: '📦' },
    { name: 'Testing', score: 87, color: '#06b6d4', icon: '🧪' },
  ];

  return (
    <div className="home-page" style={{ width: '100%', overflowX: 'hidden' }}>
      {/* 1. HERO SECTION */}
      <section className="page-container" style={{ paddingTop: '4.75rem', paddingBottom: '4.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2.5rem', alignItems: 'center' }}>
          {/* Left Column: Hero Content */}
          <div className="animate-fade-in-up">
            <div className="gency-hero-badge" style={{ marginBottom: '0.85rem' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#6366f1', display: 'inline-block' }} />
              <span>Realistic Engineering Practice Platform</span>
            </div>

            <h1 className="hero-title animate-fade-in-up stagger-1" style={{ marginBottom: '1rem', lineHeight: '1.12' }}>
              Practice Software<br />
              <span className="accent-gradient">Engineering.</span><br />
              Not Just Coding.
            </h1>

            <p className="hero-subtitle animate-fade-in-up stagger-2" style={{ marginBottom: '1.5rem', fontSize: '1.05rem', lineHeight: 1.55 }}>
              Real-world, repository-based challenges to build practical software engineering skills.
            </p>

            {/* CTAs */}
            <div className="animate-fade-in-up stagger-3" style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap', marginBottom: '1.75rem' }}>
              <Link
                to={isAuthenticated ? '/dashboard' : '/challenges'}
                className="btn-saas btn-saas-primary"
                style={{ padding: '0.8rem 2rem', fontSize: '1rem' }}
              >
                <span>Start Practicing</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
              <Link
                to="/challenges"
                className="btn-saas btn-saas-secondary"
                style={{ padding: '0.8rem 1.85rem', fontSize: '1rem' }}
              >
                View Challenges
              </Link>
            </div>

            {/* Floating Tags */}
            <div className="animate-fade-in-up stagger-4" style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
              <span className="badge badge-API" style={{ padding: '0.35rem 0.8rem', fontSize: '0.74rem' }}>
                ✓ Real Repositories
              </span>
              <span className="badge badge-SECURITY" style={{ padding: '0.35rem 0.8rem', fontSize: '0.74rem' }}>
                ✓ Real Problems
              </span>
              <span className="badge badge-PERFORMANCE" style={{ padding: '0.35rem 0.8rem', fontSize: '0.74rem' }}>
                ✓ Real Skills
              </span>
            </div>
          </div>

          {/* Right Column: Polished Product Mockup */}
          <div className="animate-scale-in stagger-3 floating-mockup" style={{ position: 'relative' }}>
            <div
              className="card"
              style={{
                borderRadius: '18px',
                border: '1px solid #e2e8f0',
                background: '#ffffff',
                boxShadow: '0 20px 40px -10px rgba(15, 23, 42, 0.1), 0 6px 20px -4px rgba(99, 102, 241, 0.06)',
                overflow: 'hidden',
              }}
            >
              {/* Mockup Window Header */}
              <div style={{ background: '#f8fafc', padding: '0.75rem 1.15rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ef4444' }} />
                  <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#f59e0b' }} />
                  <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#10b981' }} />
                </div>
                <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  codefoundry / services / report_generator.py
                </div>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <button className="btn" style={{ padding: '0.22rem 0.65rem', fontSize: '0.74rem', background: '#ffffff', border: '1px solid #cbd5e1' }}>
                    ▶ Run Tests
                  </button>
                  <button className="btn-saas btn-saas-primary" style={{ padding: '0.22rem 0.65rem', fontSize: '0.74rem' }}>
                    Submit ✓
                  </button>
                </div>
              </div>

              {/* Mockup Workspace Body */}
              <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', minHeight: '230px' }}>
                {/* File Tree Sidebar */}
                <div style={{ background: '#f8fafc', borderRight: '1px solid #e2e8f0', padding: '0.85rem', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', fontSize: '0.7rem', textTransform: 'uppercase' }}>
                    Repository
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.15rem 0' }}>📁 src/</div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.15rem 0 0.15rem 0.7rem' }}>📁 models/</div>
                  <div style={{ color: 'var(--accent-primary)', fontWeight: 600, padding: '0.15rem 0 0.15rem 0.7rem', background: 'rgba(99, 102, 241, 0.08)', borderRadius: '4px' }}>
                    📄 report_gen.py
                  </div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.15rem 0 0.15rem 0.7rem' }}>📄 queries.py</div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.15rem 0' }}>📁 tests/</div>
                  <div style={{ color: 'var(--text-secondary)', padding: '0.15rem 0 0.15rem 0.7rem' }}>📄 test_perf.py</div>
                </div>

                {/* Editor Content Area */}
                <div style={{ padding: '1rem 1.15rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', lineHeight: '1.55', background: '#ffffff', color: '#1e293b' }}>
                  <div><span style={{ color: '#8b5cf6' }}>def</span> <span style={{ color: '#2563eb' }}>generate_aggregate_report</span>(dataset: <span style={{ color: '#0891b2' }}>QuerySet</span>):</div>
                  <div style={{ paddingLeft: '1rem', color: '#64748b' }}># Optimized batch aggregation pipeline</div>
                  <div style={{ paddingLeft: '1rem' }}><span style={{ color: '#8b5cf6' }}>return</span> dataset.annotate(</div>
                  <div style={{ paddingLeft: '2rem' }}>total_volume=Sum(<span style={{ color: '#059669' }}>'amount'</span>),</div>
                  <div style={{ paddingLeft: '2rem' }}>avg_latency=Avg(<span style={{ color: '#059669' }}>'duration_ms'</span>)</div>
                  <div style={{ paddingLeft: '1rem' }}>).iterator(chunk_size=<span style={{ color: '#d97706' }}>500</span>)</div>
                </div>
              </div>

              {/* Mockup Evaluation Result Footer */}
              <div style={{ background: '#ecfdf5', borderTop: '1px solid #a7f3d0', padding: '0.75rem 1.15rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#059669', fontWeight: 800, fontSize: '0.95rem' }}>✓</span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#065f46' }}>
                    Evaluation Passed: 4/4 Test Assertions Verified (Latency: 42ms)
                  </span>
                </div>
                <span className="badge badge-PERFORMANCE" style={{ fontSize: '0.7rem', padding: '0.2rem 0.6rem' }}>
                  Score: 100/100
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SIMPLE 5-STEP FLOW */}
      <section id="features" style={{ backgroundColor: '#f8fafc', padding: '3.75rem 0', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.5rem' }}>
            <span>Workflow</span>
          </div>
          <h2 style={{ fontSize: '2.1rem', fontWeight: 800, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
            It&apos;s that simple.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '560px', margin: '0 auto 2rem' }}>
            A streamlined workflow designed to simulate real engineering environments from day one.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '1rem' }}>
            {steps.map((step, idx) => (
              <div
                key={step.num}
                className="card animate-fade-in-up"
                style={{
                  padding: '1.35rem 1.15rem',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  animationDelay: `${idx * 60}ms`,
                  borderRadius: '16px',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: '10px',
                    background: `${step.color}15`,
                    color: step.color,
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.98rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: `1px solid ${step.color}30`,
                  }}
                >
                  {step.num}
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0.15rem 0 0' }}>{step.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, margin: 0 }}>
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. DEVELOPER SECTION */}
      <section style={{ padding: '3.75rem 0' }}>
        <div className="page-container" style={{ padding: '0 1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2.5rem', alignItems: 'center' }}>
            {/* Left side: Explanations & List */}
            <div>
              <div className="gency-hero-badge" style={{ marginBottom: '0.5rem' }}>
                <span>Developer Mastery</span>
              </div>
              <h2 style={{ fontSize: '2.1rem', fontWeight: 800, marginBottom: '0.75rem', lineHeight: 1.2 }}>
                Build real skills<br />for real opportunities.
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '1.35rem', lineHeight: 1.55 }}>
                Master the practical engineering competencies that high-performance engineering teams look for:
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.65rem', marginBottom: '1.65rem' }}>
                {[
                  { title: 'Debugging', icon: '🐛', desc: 'Root cause isolation' },
                  { title: 'APIs', icon: '⚡', desc: 'Contracts & protocols' },
                  { title: 'Databases', icon: '🗄️', desc: 'Query & index tuning' },
                  { title: 'Security', icon: '🛡️', desc: 'Vulnerability audits' },
                  { title: 'Performance', icon: '🚀', desc: 'Latency & memory' },
                  { title: 'Testing', icon: '🧪', desc: 'Edge cases & mocks' },
                ].map((item) => (
                  <div key={item.title} style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', background: '#f8fafc', padding: '0.65rem 0.85rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '1.15rem' }}>{item.icon}</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{item.title}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>

              <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.75rem 1.85rem', fontSize: '0.96rem' }}>
                <span>Explore All Challenges</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>

            {/* Right side: Floating Challenge Card & Analytics Card */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Challenge Card Example */}
              <div
                className="card animate-fade-in-up"
                style={{
                  padding: '1.5rem',
                  borderRadius: '16px',
                  border: '1px solid #e2e8f0',
                  boxShadow: 'var(--shadow-md)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <span className="badge badge-PERFORMANCE" style={{ marginBottom: '0.35rem', display: 'inline-block', fontSize: '0.72rem' }}>
                      Performance
                    </span>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
                      The Slow Report Generator
                    </h3>
                  </div>
                  <span className="badge badge-INTERMEDIATE" style={{ fontSize: '0.72rem' }}>Intermediate</span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1.15rem', lineHeight: 1.45 }}>
                  Optimize report generation for large datasets. Refactor an O(N²) calculation into an efficient streaming aggregation pipeline.
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.85rem', borderTop: '1px solid #f1f5f9' }}>
                  <div style={{ display: 'flex', gap: '0.65rem', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    <span>🐍 Python</span>
                    <span>•</span>
                    <span>🏆 250 Points</span>
                  </div>
                  <Link to="/challenges" className="btn-saas btn-saas-primary" style={{ padding: '0.45rem 1.15rem', fontSize: '0.82rem' }}>
                    <span>Start Challenge</span>
                    <span className="btn-arrow-icon">→</span>
                  </Link>
                </div>
              </div>

              {/* Floating Analytics Card */}
              <div
                className="card"
                style={{
                  padding: '1rem 1.35rem',
                  borderRadius: '14px',
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(59, 130, 246, 0.04) 100%)',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.9rem' }}>
                    ⚡
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.86rem' }}>Performance Gain Verified</div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Docker Sandbox: Execution time dropped 92%</div>
                  </div>
                </div>
                <span className="badge badge-passed" style={{ fontSize: '0.72rem' }}>+35 pts</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. SKILL ANALYTICS SECTION */}
      <section style={{ backgroundColor: '#f8fafc', padding: '3.75rem 0', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.5rem' }}>
            <span>Verified Profiling</span>
          </div>
          <h2 style={{ fontSize: '2.1rem', fontWeight: 800, marginBottom: '0.4rem', color: 'var(--text-primary)' }}>
            Turn practice into measurable skills.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '600px', margin: '0 auto 2rem' }}>
            Every challenge submission generates deterministic competency data across six fundamental engineering dimensions.
          </p>

          {/* Skill Dashboard Mockup Container */}
          <div
            className="card animate-fade-in-up"
            style={{
              maxWidth: '860px',
              margin: '0 auto',
              padding: '1.75rem 2rem',
              borderRadius: '20px',
              textAlign: 'left',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.35rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' }}>
              <div>
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Illustrative Engineering Readiness
                </span>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '0.15rem 0 0' }}>
                  Overall Skill Score
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.35rem', fontWeight: 900, color: 'var(--accent-primary)', lineHeight: 1 }}>
                  89
                </span>
                <span style={{ color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.95rem' }}>/ 100</span>
              </div>
            </div>

            {/* 6 Skill Progress Bars */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.15rem' }}>
              {demoSkills.map((sk) => (
                <div key={sk.name} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.86rem' }}>
                    <span style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span>{sk.icon}</span> {sk.name}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: sk.color }}>
                      {sk.score}%
                    </span>
                  </div>
                  <AnimatedProgress value={sk.score} color={sk.color} height={7} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 5. RECRUITER SECTION */}
      <section style={{ padding: '3.75rem 0' }}>
        <div className="page-container" style={{ padding: '0 1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2.5rem', alignItems: 'center' }}>
            {/* Left: Recruiter Mockup */}
            <div
              className="card animate-fade-in-up"
              style={{
                borderRadius: '18px',
                padding: '1.35rem',
                boxShadow: 'var(--shadow-md)',
                border: '1px solid #e2e8f0',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.1rem' }}>📊</span>
                  <span style={{ fontWeight: 800, fontSize: '0.92rem' }}>Candidate Evaluation Matrix</span>
                </div>
                <span className="badge badge-passed" style={{ fontSize: '0.72rem' }}>Verified Data</span>
              </div>

              {/* Mini Candidate Row 1 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 0.85rem', background: '#f8fafc', borderRadius: '10px', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <div className="candidate-avatar" style={{ width: 30, height: 30, fontSize: '0.76rem' }}>AL</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.84rem' }}>@alex_dev</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>14 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-PERFORMANCE" style={{ fontSize: '0.72rem' }}>Score: 92/100</span>
              </div>

              {/* Mini Candidate Row 2 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 0.85rem', background: '#f8fafc', borderRadius: '10px', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <div className="candidate-avatar" style={{ width: 30, height: 30, fontSize: '0.76rem', background: 'linear-gradient(135deg, #3b82f6, #06b6d4)' }}>SA</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.84rem' }}>@sarah_eng</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>18 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-SECURITY" style={{ fontSize: '0.72rem' }}>Score: 95/100</span>
              </div>

              {/* Mini Candidate Row 3 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 0.85rem', background: '#f8fafc', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <div className="candidate-avatar" style={{ width: 30, height: 30, fontSize: '0.76rem', background: 'linear-gradient(135deg, #10b981, #3b82f6)' }}>MK</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.84rem' }}>@mike_code</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>11 Challenges Solved</div>
                  </div>
                </div>
                <span className="badge badge-API" style={{ fontSize: '0.72rem' }}>Score: 88/100</span>
              </div>
            </div>

            {/* Right: Explanations */}
            <div>
              <div className="gency-hero-badge" style={{ marginBottom: '0.5rem' }}>
                <span>For Engineering Recruiters</span>
              </div>
              <h2 style={{ fontSize: '2.1rem', fontWeight: 800, marginBottom: '0.75rem', lineHeight: 1.2 }}>
                Find job-ready developers.
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '1.25rem', lineHeight: 1.55 }}>
                Make hiring decisions based on verified engineering evidence rather than resume buzzwords.
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {[
                  'Verified assessment data from multi-file sandbox evaluations',
                  'Granular engineering skill dimensions across 6 competencies',
                  'Candidate filtering by score threshold and challenge domain',
                  'Side-by-side candidate comparison matrix',
                  'Auditable challenge evidence and test execution logs',
                ].map((text) => (
                  <li key={text} style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <span style={{ color: '#6366f1', fontWeight: 800 }}>✓</span>
                    <span>{text}</span>
                  </li>
                ))}
              </ul>

              <Link to="/recruiter" className="btn-saas btn-saas-primary" style={{ padding: '0.75rem 1.85rem', fontSize: '0.96rem' }}>
                <span>Explore Recruiter Dashboard</span>
                <span className="btn-arrow-icon">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 6. STATS SECTION */}
      <section style={{ backgroundColor: '#f8fafc', padding: '2.75rem 0', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0' }}>
        <div className="page-container" style={{ padding: '0 1.5rem' }}>
          <div className="gency-stats-grid" style={{ marginTop: 0, gap: '1rem' }}>
            <div className="gency-stat-tile" style={{ padding: '1.25rem 1.5rem', borderRadius: '16px' }}>
              <span className="gency-stat-label" style={{ fontSize: '0.78rem' }}>Repository Challenges</span>
              <span className="gency-stat-number" style={{ color: '#2563eb', fontSize: '1.95rem' }}>
                <AnimatedCounter value={12} duration={800} />+
              </span>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Multi-file real codebases</span>
            </div>

            <div className="gency-stat-tile" style={{ padding: '1.25rem 1.5rem', borderRadius: '16px' }}>
              <span className="gency-stat-label" style={{ fontSize: '0.78rem' }}>Engineering Skills</span>
              <span className="gency-stat-number" style={{ color: '#7c3aed', fontSize: '1.95rem' }}>
                <AnimatedCounter value={6} duration={600} />
              </span>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Core competency dimensions</span>
            </div>

            <div className="gency-stat-tile" style={{ padding: '1.25rem 1.5rem', borderRadius: '16px' }}>
              <span className="gency-stat-label" style={{ fontSize: '0.78rem' }}>Evaluation Tests</span>
              <span className="gency-stat-number" style={{ color: '#059669', fontSize: '1.95rem' }}>
                <AnimatedCounter value={100} suffix="%" duration={900} />
              </span>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Deterministic test assertions</span>
            </div>

            <div className="gency-stat-tile" style={{ padding: '1.25rem 1.5rem', borderRadius: '16px' }}>
              <span className="gency-stat-label" style={{ fontSize: '0.78rem' }}>Challenge Types</span>
              <span className="gency-stat-number" style={{ color: '#d97706', fontSize: '1.95rem' }}>
                <AnimatedCounter value={6} duration={700} />
              </span>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Bug fix, API, Security & more</span>
            </div>
          </div>
        </div>
      </section>

      {/* 7. TRUST / TECHNOLOGY SECTION */}
      <section id="docs" style={{ padding: '3.5rem 0' }}>
        <div className="page-container" style={{ textAlign: 'center', padding: '0 1.5rem' }}>
          <div className="gency-hero-badge" style={{ marginBottom: '0.5rem' }}>
            <span>Architecture</span>
          </div>
          <h2 style={{ fontSize: '2.1rem', fontWeight: 800, marginBottom: '0.4rem' }}>
            Built with modern engineering tools.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '560px', margin: '0 auto 1.75rem' }}>
            Powered by the same industry-standard technologies used in modern production infrastructure.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.85rem' }}>
            {techStack.map((tech) => (
              <div
                key={tech.name}
                className="card"
                style={{
                  padding: '1.15rem 0.85rem',
                  borderRadius: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.35rem',
                  textAlign: 'center',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <span style={{ fontSize: '1.65rem' }}>{tech.icon}</span>
                <span style={{ fontWeight: 800, fontSize: '0.98rem', color: 'var(--text-primary)' }}>{tech.name}</span>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{tech.category}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 8. FINAL CTA */}
      <section className="page-container" style={{ padding: '1rem 1.5rem 3.5rem' }}>
        <div
          className="card animate-fade-in-up"
          style={{
            padding: '2.75rem 2rem',
            textAlign: 'center',
            borderRadius: '20px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(59, 130, 246, 0.08) 50%, rgba(16, 185, 129, 0.06) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
          }}
        >
          <h2 style={{ fontSize: 'clamp(1.75rem, 3.5vw, 2.35rem)', fontWeight: 800, marginBottom: '0.6rem', color: 'var(--text-primary)' }}>
            Start your engineering journey with CodeFoundry.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', maxWidth: '560px', margin: '0 auto 1.75rem' }}>
            Real challenges. Real skills. Real engineering practice.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
            <Link
              to={isAuthenticated ? '/dashboard' : '/register'}
              className="btn-saas btn-saas-primary"
              style={{ padding: '0.8rem 2.2rem', fontSize: '1rem' }}
            >
              <span>Get Started</span>
              <span className="btn-arrow-icon">→</span>
            </Link>
            <Link
              to="/challenges"
              className="btn-saas btn-saas-secondary"
              style={{ padding: '0.8rem 2rem', fontSize: '1rem' }}
            >
              View Challenges
            </Link>
          </div>
        </div>
      </section>

      {/* 9. FOOTER */}
      <footer style={{ borderTop: '1px solid #e2e8f0', background: '#ffffff', padding: '2.25rem 0 1.75rem' }}>
        <div className="page-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', padding: '0 1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', marginBottom: '0.25rem' }}>
              <span className="logo-icon" style={{ width: 26, height: 26, fontSize: '0.75rem' }}>&gt;_</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.08rem' }}>CodeFoundry</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', margin: 0 }}>
              Practice Software Engineering. Not Just Coding.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1.75rem', flexWrap: 'wrap', fontSize: '0.88rem' }}>
            <Link to="/challenges" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>
              Challenges
            </Link>
            <Link to="/leaderboard" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>
              Leaderboard
            </Link>
            <Link to="/recruiter" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>
              Recruiters
            </Link>
            <a href="#docs" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 500 }}>
              Documentation
            </a>
          </div>
        </div>
        <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #f1f5f9', color: 'var(--text-light)', fontSize: '0.78rem' }}>
          © {new Date().getFullYear()} CodeFoundry. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
