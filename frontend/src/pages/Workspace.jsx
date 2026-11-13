import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { runCode } from '../api/execution';
import { createSubmission, getSubmission } from '../api/submissions';
import Loading from '../components/Loading';
import CodeEditor from '../components/CodeEditor';
import RepositoryTree from '../components/RepositoryTree';
import AnimatedCounter from '../components/motion/AnimatedCounter';

const MAX_POLL_ATTEMPTS = 60;
const ACTIVE_SUBMISSION_STORAGE_KEY = 'codefoundry_active_submission_id';

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
    if (!isRepoChallenge) return code;
    if (challenge.entrypoint && filesState[challenge.entrypoint] !== undefined) {
      return filesState[challenge.entrypoint];
    }
    const pyFiles = Object.keys(filesState).filter(
      (p) => !p.includes('test_') && !p.startsWith('tests/') && p.endsWith('.py')
    );
    if (pyFiles.length > 0) {
      return filesState[pyFiles[0]];
    }
    return filesState[activeFilePath] || Object.values(filesState)[0] || '';
  };

  const handleRunCode = async () => {
    setIsRunning(true);
    setExecutionResult(null);
    setExecutionError(null);
    setActiveTab('execution');

    try {
      const payload = isRepoChallenge
        ? {
            files: filesState,
            entrypoint: challenge.entrypoint || activeFilePath || undefined,
            stdin: stdin || undefined,
            language: challenge.programming_language,
          }
        : {
            code,
            stdin: stdin || undefined,
            language: challenge.programming_language,
          };

      const result = await runCode(payload);
      setExecutionResult(result);
    } catch (err) {
      setExecutionError(err.message || 'Sandbox execution request failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitSolution = async () => {
    setIsSubmitting(true);
    setSubmissionError(null);
    setSubmissionResult(null);
    setActiveTab('submission');

    try {
      const primaryCode = getPrimaryCode();
      const payload = {
        challenge: challenge.id,
        code: primaryCode,
        language: challenge.programming_language,
        ...(isRepoChallenge ? { files: filesState } : {}),
      };

      const sub = await createSubmission(payload);
      setSubmissionId(sub.id);
      setIsSubmitting(false);
      setIsEvaluating(true);

      sessionStorage.setItem(ACTIVE_SUBMISSION_STORAGE_KEY, String(sub.id));
      startPolling(sub.id);
    } catch (err) {
      setIsSubmitting(false);
      setIsEvaluating(false);
      setSubmissionError(err.message || 'Failed to dispatch submission.');
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ padding: '4rem 1.5rem' }}>
        <Loading message="Spinning up isolated engineering workspace..." />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="page-container">
        <div style={{ background: 'var(--accent-danger-light)', border: '1px solid var(--accent-danger-border)', color: 'var(--accent-danger)', borderRadius: 'var(--radius-md)', padding: '1.5rem', textAlign: 'center' }}>
          <p style={{ marginBottom: '1rem', fontWeight: 600 }}>{error || 'Challenge workspace unavailable.'}</p>
          <Link to="/challenges" className="btn btn-secondary">
            &larr; Back to Challenges
          </Link>
        </div>
      </div>
    );
  }

  const evaluation = submissionResult?.evaluation;

  return (
    <div className="workspace-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 72px)', background: '#F7F7FB', overflow: 'hidden' }}>
      {/* 1. Top Workspace Toolbar */}
      <div
        className="workspace-toolbar"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.65rem 1.5rem',
          background: '#ffffff',
          borderBottom: '1px solid var(--border-color)',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Link
            to={`/challenges/${challenge.id}`}
            className="btn btn-secondary"
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
          >
            &larr; Briefing
          </Link>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            {challenge.title}
          </h2>
          <span className={`badge badge-${challenge.difficulty}`} style={{ fontSize: '0.72rem' }}>
            {challenge.difficulty}
          </span>
          <span className={`badge badge-${challenge.challenge_type}`} style={{ fontSize: '0.72rem' }}>
            {challenge.challenge_type?.replace('_', ' ')}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button
            onClick={handleResetCode}
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem', padding: '0.45rem 0.95rem' }}
            title="Reset code to starter version"
          >
            ↺ Reset
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleRunCode}
            disabled={isRunning || isSubmitting || isEvaluating || !getPrimaryCode().trim()}
            style={{ fontSize: '0.82rem', padding: '0.45rem 1.15rem' }}
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
              padding: '0.48rem 1.45rem',
              fontSize: '0.88rem',
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

      {/* 2. Main Workspace Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar: Mission Info & Repository Explorer */}
        <div style={{ background: '#FAF9FD', borderRight: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          {/* Mission Info Box */}
          <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.45rem' }}>
              Mission Briefing
            </h3>
            <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.55 }}>
              {challenge.description}
            </div>
            <div style={{ display: 'flex', gap: '0.65rem', marginTop: '0.85rem', fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              <span>Limit: <strong>{challenge.time_limit}s</strong></span>
              <span>•</span>
              <span>Mem: <strong>{challenge.memory_limit}MB</strong></span>
              <span>•</span>
              <span>Points: <strong>{challenge.points}</strong></span>
            </div>
          </div>

          {/* Repository File Tree */}
          {isRepoChallenge && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0.75rem 0.5rem' }}>
              <RepositoryTree
                files={repoFiles}
                activeFile={activeFilePath}
                onSelectFile={handleFileSelect}
              />
            </div>
          )}

          {/* Standard Input (stdin) Panel */}
          <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', background: '#F4F3F9' }}>
            <label htmlFor="workspace-stdin" style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem', letterSpacing: '0.04em' }}>
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
                height: '52px',
                background: '#ffffff',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                padding: '0.45rem 0.65rem',
                resize: 'none',
                outline: 'none',
              }}
            />
          </div>
        </div>

        {/* Right Area: Stable Monaco Editor & Bottom Results Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          {/* Editor Header Tab Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff', padding: '0.55rem 1.15rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-primary)' }}>
                {isRepoChallenge ? activeFilePath || 'repository' : 'solution.py'}
              </span>
              {isCurrentFileReadOnly && (
                <span className="badge" style={{ fontSize: '0.65rem', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
                  🔒 READ-ONLY
                </span>
              )}
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              {challenge.programming_language}
            </span>
          </div>

          {/* Stable Code Editor Wrapper (Monaco 'vs-dark' framed cleanly) */}
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
          <div style={{ height: '270px', borderTop: '1px solid var(--border-color)', background: '#ffffff', display: 'flex', flexDirection: 'column' }}>
            {/* Panel Tabs */}
            <div style={{ display: 'flex', background: '#FAF9FD', borderBottom: '1px solid var(--border-color)', padding: '0 0.75rem' }}>
              <button
                onClick={() => setActiveTab('execution')}
                style={{
                  padding: '0.6rem 1.15rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  borderBottom: activeTab === 'execution' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                  background: activeTab === 'execution' ? '#ffffff' : 'transparent',
                  color: activeTab === 'execution' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  borderRadius: '6px 6px 0 0',
                }}
              >
                Execution Output
              </button>
              <button
                onClick={() => setActiveTab('submission')}
                style={{
                  padding: '0.6rem 1.15rem',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  border: 'none',
                  borderBottom: activeTab === 'submission' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                  background: activeTab === 'submission' ? '#ffffff' : 'transparent',
                  color: activeTab === 'submission' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  borderRadius: '6px 6px 0 0',
                }}
              >
                <span>Submission Evaluation</span>
                {isEvaluating && <span style={{ color: 'var(--pastel-peach-text)', fontSize: '0.74rem' }}>(Grading...)</span>}
                {submissionResult && (
                  <span className={`badge ${submissionResult.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`} style={{ fontSize: '0.65rem' }}>
                    {submissionResult.status}
                  </span>
                )}
              </button>
            </div>

            {/* Tab 1: Terminal Output */}
            {activeTab === 'execution' && (
              <div style={{ flex: 1, padding: '0.85rem 1.25rem', overflowY: 'auto', background: '#1F1E2E', color: '#F0EFF6', fontFamily: 'var(--font-mono)', fontSize: '0.84rem' }}>
                {isRunning && (
                  <div style={{ color: '#B4B3C2', display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                    <span className="spinner-icon" />
                    <span>Executing code in isolated Docker sandbox...</span>
                  </div>
                )}
                {executionError && <div style={{ color: '#F87171' }}>{executionError}</div>}
                {!isRunning && !executionError && !executionResult && (
                  <div style={{ color: '#8E8D9E' }}>
                    Click &quot;Run Tests&quot; to execute your solution in the Docker sandbox environment.
                  </div>
                )}
                {!isRunning && executionResult && (
                  <div>
                    {executionResult.stdout && <div style={{ whiteSpace: 'pre-wrap', color: '#EAE8F2' }}>{executionResult.stdout}</div>}
                    {executionResult.stderr && <div style={{ whiteSpace: 'pre-wrap', color: '#F87171' }}>{executionResult.stderr}</div>}
                    <div style={{ borderTop: '1px solid #36344B', marginTop: '0.6rem', paddingTop: '0.45rem', fontSize: '0.76rem', color: '#B4B3C2' }}>
                      Status: {executionResult.status} • Time: {executionResult.execution_time?.toFixed(3)}s • Exit Code: {executionResult.exit_code}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Submission Result */}
            {activeTab === 'submission' && (
              <div style={{ flex: 1, padding: '1rem 1.25rem', overflowY: 'auto', background: '#ffffff' }}>
                {isSubmitting && <div style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Queueing submission for evaluation...</div>}
                {isEvaluating && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                    <span className="spinner-icon" />
                    <span>Evaluating in Docker sandbox... (Submission #{submissionId})</span>
                  </div>
                )}
                {submissionError && <div style={{ color: 'var(--accent-danger)', fontWeight: 600 }}>{submissionError}</div>}
                {!isSubmitting && !isEvaluating && !submissionResult && !submissionError && (
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Click &quot;Submit Solution&quot; to grade your solution against all challenge test cases.
                  </div>
                )}
                {!isSubmitting && !isEvaluating && submissionResult && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Summary Row */}
                    <div className="card panel-pastel-blue" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderRadius: '16px' }}>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Status</div>
                        <span className={`badge ${submissionResult.status === 'PASSED' ? 'badge-passed' : 'badge-failed'}`}>
                          {submissionResult.status}
                        </span>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Score</div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                          <AnimatedCounter value={submissionResult.score || 0} duration={800} /> / {challenge.points} pts
                        </div>
                      </div>
                      {evaluation && (
                        <div>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Tests</div>
                          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: evaluation.tests_passed === evaluation.tests_total ? 'var(--pastel-mint-text)' : 'var(--accent-danger)' }}>
                            {evaluation.tests_passed}/{evaluation.tests_total}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Test Results Breakdown */}
                    {evaluation?.test_results && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Test Results Breakdown
                        </div>
                        {evaluation.test_results.map((tc, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: '0.75rem 1rem',
                              borderRadius: '12px',
                              border: tc.passed ? '1px solid var(--pastel-mint-border)' : '1px solid var(--accent-danger-border)',
                              background: tc.passed ? 'var(--pastel-mint-light)' : 'var(--accent-danger-light)',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span style={{ fontSize: '0.88rem', fontWeight: 700, color: tc.passed ? 'var(--pastel-mint-text)' : 'var(--accent-danger)' }}>
                              {tc.name || `Test Case #${idx + 1}`} {tc.is_hidden && '(Hidden)'}
                            </span>
                            <span className={`status-pill ${tc.passed ? 'status-passed' : 'status-failed'}`} style={{ fontSize: '0.72rem' }}>
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
