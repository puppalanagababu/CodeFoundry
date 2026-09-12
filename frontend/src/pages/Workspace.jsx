import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { runCode } from '../api/execution';
import { createSubmission, getSubmission } from '../api/submissions';
import Loading from '../components/Loading';
import CodeEditor from '../components/CodeEditor';
import RepositoryTree from '../components/RepositoryTree';
import AnimatedCounter from '../components/motion/AnimatedCounter';
import AnimatedProgress from '../components/motion/AnimatedProgress';

const MAX_POLL_ATTEMPTS = 60;
const ACTIVE_SUBMISSION_STORAGE_KEY = 'codefoundry_active_submission_id';

const SKILL_DIMENSION_NAMES = {
  problem_solving: 'Problem Solving',
  debugging: 'Debugging',
  security: 'Security',
  performance: 'Performance',
  code_quality: 'Code Quality',
  testing: 'Testing',
};

export default function Workspace() {
  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [code, setCode] = useState('');
  const [stdin, setStdin] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Multi-file repository state
  const [filesState, setFilesState] = useState({});
  const [activeFilePath, setActiveFilePath] = useState('');

  // Active bottom panel tab: 'execution' | 'submission'
  const [activeTab, setActiveTab] = useState('execution');

  // Execution states (Run Code)
  const [isRunning, setIsRunning] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState(null);

  // Submission states (Submit Solution)
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [submissionId, setSubmissionId] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [submissionError, setSubmissionError] = useState(null);

  const pollingTimerRef = useRef(null);

  const startPolling = (subId) => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
    }

    let attempts = 0;

    pollingTimerRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const data = await getSubmission(subId);
        const evalData = data.evaluation;

        const isTerminal =
          data.status === 'PASSED' ||
          data.status === 'FAILED' ||
          data.status === 'ERROR' ||
          (evalData && (evalData.status === 'COMPLETED' || evalData.status === 'FAILED'));

        if (isTerminal) {
          clearInterval(pollingTimerRef.current);
          pollingTimerRef.current = null;
          setSubmissionResult(data);
          setIsEvaluating(false);
          sessionStorage.removeItem(ACTIVE_SUBMISSION_STORAGE_KEY);
        } else if (attempts >= MAX_POLL_ATTEMPTS) {
          clearInterval(pollingTimerRef.current);
          pollingTimerRef.current = null;
          setIsEvaluating(false);
          setSubmissionError('Evaluation is taking longer than expected. You can check your submissions later.');
        }
      } catch (err) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
        setIsEvaluating(false);
        setSubmissionError(err.message || 'Failed to poll evaluation status.');
      }
    }, 1000);
  };

  useEffect(() => {
    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getChallenge(id)
      .then(async (data) => {
        if (!isMounted) return;
        setChallenge(data);

        const repoFiles = data.repository?.files;
        if (repoFiles && repoFiles.length > 0) {
          const initialMap = {};
          repoFiles.forEach((f) => {
            initialMap[f.path] = f.content || '';
          });
          setFilesState(initialMap);

          const defaultFile =
            repoFiles.find((f) => data.entrypoint && f.path === data.entrypoint) ||
            repoFiles.find((f) => !f.is_readonly && !f.is_test && f.path.endsWith('.py')) ||
            repoFiles.find((f) => !f.is_test) ||
            repoFiles[0];

          const defaultPath = defaultFile ? defaultFile.path : repoFiles[0].path;
          setActiveFilePath(defaultPath);
          setCode(initialMap[defaultPath] || '');
        } else {
          setFilesState({});
          setActiveFilePath('');
          setCode(data.starter_code || '');
        }

        const savedSubId = sessionStorage.getItem(ACTIVE_SUBMISSION_STORAGE_KEY);
        if (savedSubId) {
          try {
            const subData = await getSubmission(savedSubId);
            if (!isMounted) return;

            if (subData && Number(subData.challenge) === Number(id)) {
              const evalData = subData.evaluation;
              const isTerminal =
                subData.status === 'PASSED' ||
                subData.status === 'FAILED' ||
                subData.status === 'ERROR' ||
                (evalData && (evalData.status === 'COMPLETED' || evalData.status === 'FAILED'));

              setSubmissionId(Number(savedSubId));
              setActiveTab('submission');

              if (isTerminal) {
                setSubmissionResult(subData);
                setIsEvaluating(false);
                sessionStorage.removeItem(ACTIVE_SUBMISSION_STORAGE_KEY);
              } else {
                setIsEvaluating(true);
                startPolling(Number(savedSubId));
              }
            } else {
              sessionStorage.removeItem(ACTIVE_SUBMISSION_STORAGE_KEY);
            }
          } catch {
            if (isMounted) {
              sessionStorage.removeItem(ACTIVE_SUBMISSION_STORAGE_KEY);
            }
          }
        }

        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load workspace.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  const repoFiles = challenge?.repository?.files || [];
  const isRepoChallenge = repoFiles.length > 0;
  const activeFileObj = isRepoChallenge
    ? repoFiles.find((f) => f.path === activeFilePath)
    : null;

  const currentEditorContent = isRepoChallenge
    ? filesState[activeFilePath] ?? ''
    : code;

  const isCurrentFileReadOnly = activeFileObj
    ? activeFileObj.is_readonly || activeFileObj.is_test
    : false;

  const handleFileSelect = (filePath) => {
    setActiveFilePath(filePath);
  };

  const handleEditorContentChange = (newVal) => {
    if (isRepoChallenge) {
      setFilesState((prev) => ({
        ...prev,
        [activeFilePath]: newVal,
      }));
      setCode(newVal);
    } else {
      setCode(newVal);
    }
  };

  const handleResetCode = () => {
    if (!challenge) return;
    const confirmed = window.confirm(
      'Reset all code to the starter version? Your current unsaved changes will be lost.'
    );
    if (!confirmed) return;

    if (isRepoChallenge) {
      const initialMap = {};
      repoFiles.forEach((f) => {
        initialMap[f.path] = f.content || '';
      });
      setFilesState(initialMap);

      const defaultFile =
        repoFiles.find((f) => challenge.entrypoint && f.path === challenge.entrypoint) ||
        repoFiles.find((f) => !f.is_readonly && !f.is_test && f.path.endsWith('.py')) ||
        repoFiles.find((f) => !f.is_test) ||
        repoFiles[0];

      const defaultPath = defaultFile ? defaultFile.path : (repoFiles[0]?.path || '');
      setActiveFilePath(defaultPath);
      setCode(initialMap[defaultPath] || '');
    } else {
      setCode(challenge.starter_code || '');
    }

    setExecutionResult(null);
    setExecutionError(null);
  };

  const getPrimaryCode = () => {
    if (isRepoChallenge) {
      if (challenge.entrypoint && filesState[challenge.entrypoint] !== undefined) {
        return filesState[challenge.entrypoint];
      }
      const pyFile =
        repoFiles.find((f) => !f.is_readonly && !f.is_test && f.path.endsWith('.py')) ||
        repoFiles.find((f) => f.path.endsWith('.py'));
      if (pyFile && filesState[pyFile.path] !== undefined) {
        return filesState[pyFile.path];
      }
      return filesState[activeFilePath] || code;
    }
    return code;
  };

  const handleRunCode = async () => {
    if (isRunning) return;

    const filteredFiles = {};
    if (isRepoChallenge) {
      Object.entries(filesState).forEach(([path, content]) => {
        if (!path.startsWith('tests/') && !path.includes('test_')) {
          filteredFiles[path] = content;
        }
      });
      if (Object.keys(filteredFiles).length === 0) return;
    } else {
      if (!code.trim()) return;
    }

    setIsRunning(true);
    setExecutionResult(null);
    setExecutionError(null);
    setActiveTab('execution');

    try {
      const payload = isRepoChallenge
        ? {
            files: filteredFiles,
            entrypoint: challenge.entrypoint || 'app/calculator.py',
            language: challenge.programming_language || 'Python',
            stdin,
            timeout: challenge.time_limit || 5,
          }
        : {
            code,
            language: challenge.programming_language || 'Python',
            stdin,
            timeout: challenge.time_limit || 5,
          };

      const res = await runCode(payload);
      setExecutionResult(res);
    } catch (err) {
      setExecutionError(err.message || 'Execution request failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitSolution = async () => {
    if (isSubmitting || isEvaluating) return;

    const filteredFiles = {};
    if (isRepoChallenge) {
      Object.entries(filesState).forEach(([path, content]) => {
        if (!path.startsWith('tests/') && !path.includes('test_')) {
          filteredFiles[path] = content;
        }
      });
      if (Object.keys(filteredFiles).length === 0) return;
    } else {
      if (!code.trim()) return;
    }

    setIsSubmitting(true);
    setSubmissionError(null);
    setSubmissionResult(null);
    setActiveTab('submission');

    try {
      const payload = isRepoChallenge
        ? {
            challenge: challenge.id,
            files: filteredFiles,
            code: getPrimaryCode(),
            language: challenge.programming_language || 'Python',
          }
        : {
            challenge: challenge.id,
            code,
            language: challenge.programming_language || 'Python',
          };

      const res = await createSubmission(payload);
      setIsSubmitting(false);
      setIsEvaluating(true);
      setSubmissionId(res.submission_id);
      sessionStorage.setItem(ACTIVE_SUBMISSION_STORAGE_KEY, String(res.submission_id));
      startPolling(res.submission_id);
    } catch (err) {
      setIsSubmitting(false);
      setIsEvaluating(false);
      setSubmissionError(err.message || 'Submission creation failed.');
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ padding: '4rem 1.5rem' }}>
        <Loading message="Loading workspace environment..." />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="page-container">
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: 'var(--radius-md)', padding: '1.5rem', textAlign: 'center' }}>
          <p>{error || 'Challenge not found.'}</p>
          <div style={{ marginTop: '1rem' }}>
            <Link to="/challenges" className="btn btn-secondary">
              &larr; Back to Challenges
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const evaluation = submissionResult?.evaluation;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 70px)', background: '#ffffff', overflow: 'hidden' }}>
      {/* Top Workspace Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.65rem 1.25rem', borderBottom: '1px solid #e2e8f0', background: '#ffffff', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Link to={`/challenges/${challenge.id}`} style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span>←</span> Overview
          </Link>
          <span style={{ color: '#cbd5e1' }}>|</span>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            {challenge.title}
          </h2>
          <span className={`badge badge-${challenge.difficulty}`} style={{ fontSize: '0.72rem' }}>
            {challenge.difficulty}
          </span>
          <span className={`badge badge-${challenge.challenge_type}`} style={{ fontSize: '0.72rem' }}>
            {challenge.challenge_type?.replace('_', ' ')}
          </span>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button
            type="button"
            onClick={handleResetCode}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem' }}
            title="Reset code to starter version"
          >
            ↺ Reset
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleRunCode}
            disabled={isRunning || isSubmitting || isEvaluating || !getPrimaryCode().trim()}
            style={{ fontSize: '0.82rem', padding: '0.45rem 1.1rem' }}
          >
            {isRunning ? (
              <>
                <span className="spinner-icon" />
                <span>Running...</span>
              </>
            ) : (
              <span>▶ Run Tests</span>
            )}
          </button>
          <button
            className="btn-saas btn-saas-primary"
            onClick={handleSubmitSolution}
            disabled={isSubmitting || isEvaluating || isRunning || !getPrimaryCode().trim()}
            style={{
              padding: '0.45rem 1.35rem',
              fontSize: '0.85rem',
            }}
          >
            {isSubmitting ? (
              <>
                <span className="spinner-icon" />
                <span>Submitting...</span>
              </>
            ) : isEvaluating ? (
              <>
                <span className="spinner-icon" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <span>Submit Solution</span>
                <span className="btn-arrow-icon">→</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Workspace Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar: Mission Info & Files */}
        <div style={{ background: '#f8fafc', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          {/* Challenge Meta */}
          <div style={{ padding: '1.25rem', borderBottom: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Mission Briefing
            </h3>
            <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.55 }}>
              {challenge.description}
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.85rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              <span>Limit: <strong>{challenge.time_limit}s</strong></span>
              <span>•</span>
              <span>Memory: <strong>{challenge.memory_limit}MB</strong></span>
              <span>•</span>
              <span>Points: <strong>{challenge.points}</strong></span>
            </div>
          </div>

          {/* Repository File Tree */}
          {isRepoChallenge && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1rem' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
                Repository Files
              </div>
              <RepositoryTree
                files={repoFiles}
                activeFile={activeFilePath}
                onSelectFile={handleFileSelect}
              />
            </div>
          )}

          {/* Stdin Area */}
          <div style={{ padding: '1rem', borderTop: '1px solid #e2e8f0', background: '#f1f5f9' }}>
            <label htmlFor="workspace-stdin" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.3rem' }}>
              Standard Input (stdin)
            </label>
            <textarea
              id="workspace-stdin"
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              placeholder="Optional standard input..."
              spellCheck="false"
              style={{
                width: '100%',
                height: '50px',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                padding: '0.4rem 0.6rem',
                resize: 'none',
                outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Right Area: Stable Monaco Editor & Bottom Result Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          {/* Editor Header Tab Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '0.5rem 1rem', borderBottom: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                {isRepoChallenge ? activeFilePath || 'repository' : 'solution.py'}
              </span>
              {isCurrentFileReadOnly && (
                <span className="badge" style={{ fontSize: '0.65rem', background: '#e2e8f0', color: 'var(--text-secondary)' }}>
                  🔒 READ-ONLY
                </span>
              )}
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {challenge.programming_language}
            </span>
          </div>

          {/* Stable Code Editor Wrapper (NO CSS transforms, transitions or scale applied) */}
          <div style={{ flex: 1, minHeight: '280px', position: 'relative' }}>
            {activeFileObj?.is_test && !currentEditorContent ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.88rem',
                  textAlign: 'center',
                  padding: '2rem',
                  background: '#ffffff',
                }}
              >
                🔒 Test suite implementation is protected and executed securely on the evaluation worker.
              </div>
            ) : (
              <CodeEditor
                value={currentEditorContent}
                onChange={handleEditorContentChange}
                language={challenge.programming_language}
                filePath={activeFilePath}
                readOnly={isCurrentFileReadOnly}
                theme="vs-dark"
              />
            )}
          </div>

          {/* Bottom Results Panel */}
          <div style={{ height: '260px', borderTop: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', flexDirection: 'column' }}>
            {/* Panel Tabs */}
            <div style={{ display: 'flex', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', padding: '0 0.5rem' }}>
              <button
                onClick={() => setActiveTab('execution')}
                style={{
                  padding: '0.55rem 1rem',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'execution' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                  background: 'transparent',
                  color: activeTab === 'execution' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                }}
              >
                Execution Output
              </button>
              <button
                onClick={() => setActiveTab('submission')}
                style={{
                  padding: '0.55rem 1rem',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'submission' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                  background: 'transparent',
                  color: activeTab === 'submission' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <span>Submission Evaluation</span>
                {isEvaluating && <span style={{ color: '#d97706', fontSize: '0.72rem' }}>(Grading...)</span>}
                {submissionResult && (
                  <span className={`badge ${submissionResult.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.65rem' }}>
                    {submissionResult.status}
                  </span>
                )}
              </button>
            </div>

            {/* Tab 1: Terminal Output */}
            {activeTab === 'execution' && (
              <div style={{ flex: 1, padding: '0.85rem 1.25rem', overflowY: 'auto', background: '#0f172a', color: '#f8fafc', fontFamily: 'var(--font-mono)', fontSize: '0.84rem' }}>
                {isRunning && (
                  <div style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="spinner-icon" />
                    <span>Executing code in Docker sandbox...</span>
                  </div>
                )}
                {executionError && <div style={{ color: '#f87171' }}>{executionError}</div>}
                {!isRunning && !executionError && !executionResult && (
                  <div style={{ color: '#64748b' }}>
                    Click &quot;Run Tests&quot; to execute your solution in the sandbox environment.
                  </div>
                )}
                {!isRunning && executionResult && (
                  <div>
                    {executionResult.stdout && <div style={{ whiteSpace: 'pre-wrap', color: '#e2e8f0' }}>{executionResult.stdout}</div>}
                    {executionResult.stderr && <div style={{ whiteSpace: 'pre-wrap', color: '#f87171' }}>{executionResult.stderr}</div>}
                    <div style={{ borderTop: '1px solid #334155', marginTop: '0.5rem', paddingTop: '0.4rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                      Status: {executionResult.status} • Time: {executionResult.execution_time?.toFixed(3)}s • Exit Code: {executionResult.exit_code}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Submission Result */}
            {activeTab === 'submission' && (
              <div style={{ flex: 1, padding: '1rem 1.25rem', overflowY: 'auto', background: '#ffffff' }}>
                {isSubmitting && <div>Queueing submission...</div>}
                {isEvaluating && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-primary)' }}>
                    <span className="spinner-icon" />
                    <span>Evaluating in Docker sandbox... (Submission #{submissionId})</span>
                  </div>
                )}
                {submissionError && <div style={{ color: '#dc2626' }}>{submissionError}</div>}
                {!isSubmitting && !isEvaluating && !submissionResult && !submissionError && (
                  <div style={{ color: 'var(--text-muted)' }}>
                    Click &quot;Submit Solution&quot; to grade your solution against all challenge test cases.
                  </div>
                )}
                {!isSubmitting && !isEvaluating && submissionResult && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Summary Row */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '0.85rem 1.25rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status</div>
                        <span className={`badge ${submissionResult.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`}>
                          {submissionResult.status}
                        </span>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Score</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>
                          <AnimatedCounter value={submissionResult.score || 0} duration={800} /> / {challenge.points} pts
                        </div>
                      </div>
                      {evaluation && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tests</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: evaluation.tests_passed === evaluation.tests_total ? '#059669' : '#dc2626' }}>
                            {evaluation.tests_passed}/{evaluation.tests_total}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Test Results Breakdown */}
                    {evaluation?.test_results && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          Test Results Breakdown
                        </div>
                        {evaluation.test_results.map((tc, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: '0.65rem 0.85rem',
                              borderRadius: '8px',
                              border: `1px solid ${tc.passed ? '#a7f3d0' : '#fecaca'}`,
                              background: tc.passed ? '#f0fdf4' : '#fef2f2',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: tc.passed ? '#065f46' : '#991b1b' }}>
                              {tc.name || `Test Case #${idx + 1}`} {tc.is_hidden && '(Hidden)'}
                            </span>
                            <span className={`status-pill ${tc.passed ? 'status-passed' : 'status-failed'}`} style={{ fontSize: '0.7rem' }}>
                              {tc.passed ? 'Passed ✓' : 'Failed ✕'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
