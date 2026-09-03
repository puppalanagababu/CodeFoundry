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
const ACTIVE_SUBMISSION_STORAGE_KEY = 'devforge_active_submission_id';

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

  // Unified polling function
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

  // Clean up polling timer on unmount
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

        // Check for repository multi-file structure
        const repoFiles = data.repository?.files;
        if (repoFiles && repoFiles.length > 0) {
          const initialMap = {};
          repoFiles.forEach((f) => {
            initialMap[f.path] = f.content || '';
          });
          setFilesState(initialMap);

          // Select default file: prioritize entrypoint, then editable app python file, then first non-test file, then first file
          const defaultFile =
            repoFiles.find((f) => data.entrypoint && f.path === data.entrypoint) ||
            repoFiles.find((f) => !f.is_readonly && !f.is_test && f.path.endsWith('.py')) ||
            repoFiles.find((f) => !f.is_test) ||
            repoFiles[0];

          const defaultPath = defaultFile ? defaultFile.path : repoFiles[0].path;
          setActiveFilePath(defaultPath);
          setCode(initialMap[defaultPath] || '');
        } else {
          // Backward-compatible single-file challenge
          setFilesState({});
          setActiveFilePath('');
          setCode(data.starter_code || '');
        }

        // Check for active submission in sessionStorage to resume after refresh
        const savedSubId = sessionStorage.getItem(ACTIVE_SUBMISSION_STORAGE_KEY);
        if (savedSubId) {
          try {
            const subData = await getSubmission(savedSubId);
            if (!isMounted) return;

            // Ensure submission belongs to the current challenge
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
              // Stale submission from another challenge; clear it
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
      // If editing the main Python file or active file, update code state as well
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

  // Helper to obtain the primary execution code
  const getPrimaryCode = () => {
    if (isRepoChallenge) {
      // Find main runnable code (e.g. entrypoint, or app/calculator.py or current active python file)
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

    // Filter out test files from being sent to execution
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
      <div className="page-container">
        <Loading message="Loading workspace environment..." />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="page-container">
        <div className="error-box" style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', color: '#f87171', borderRadius: 'var(--radius-md)', padding: '1.5rem', textAlign: 'center' }}>
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
    <div className="workspace-container">
      {/* Left Panel: Challenge Details */}
      <aside className="workspace-panel-left">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to={`/challenges/${challenge.id}`} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
            <span>&larr;</span> Overview
          </Link>
          <span className={`badge badge-${challenge.difficulty}`}>
            {challenge.difficulty}
          </span>
        </div>

        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem', color: '#fff', letterSpacing: '-0.02em' }}>
            {challenge.title}
          </h2>
          <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
            <span className="badge badge-type">{challenge.challenge_type.replace('_', ' ')}</span>
            <span className="badge badge-lang">{challenge.programming_language}</span>
            <span className="badge badge-lang">{challenge.points} pts</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', padding: '0.65rem 0' }}>
          <span>Timeout: <strong style={{ color: 'var(--text-secondary)' }}>{challenge.time_limit}s</strong></span>
          <span>Memory: <strong style={{ color: 'var(--text-secondary)' }}>{challenge.memory_limit} MB</strong></span>
        </div>

        <div>
          <h3 style={{ fontSize: '0.92rem', fontWeight: '600', marginBottom: '0.5rem', color: '#fff' }}>
            Description &amp; Requirements
          </h3>
          <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.6' }}>
            {challenge.description}
          </div>
        </div>
      </aside>

      {/* Right Panel: Editor Shell, Inputs & Panels (SAFE: Monaco Editor inside receives NO CSS transforms) */}
      <main className="workspace-panel-right">
        <div className="editor-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
            <span style={{ color: '#fff', fontWeight: 600 }}>{isRepoChallenge ? activeFilePath || 'repository' : 'solution.py'}</span>
            {isCurrentFileReadOnly && (
              <span className="badge" style={{ fontSize: '0.65rem', backgroundColor: 'rgba(255, 255, 255, 0.08)', color: 'var(--text-muted)' }}>
                READ-ONLY
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={handleResetCode}
              className="btn btn-secondary"
              style={{
                fontSize: '0.75rem',
                padding: '0.25rem 0.65rem',
                height: 'auto',
                color: 'var(--text-muted)',
                borderRadius: 'var(--radius-full)',
              }}
              title="Reset all files to original starter code"
            >
              Reset Code
            </button>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{challenge.programming_language}</span>
          </div>
        </div>

        {/* Code Editor Area: Multi-file layout or Single-file */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
          {isRepoChallenge ? (
            <div style={{ display: 'flex', width: '100%', height: '100%' }}>
              <div style={{ width: '220px', minWidth: '180px', borderRight: '1px solid var(--border-color)', backgroundColor: '#0c111d', overflowY: 'auto' }}>
                <RepositoryTree
                  files={repoFiles}
                  activeFile={activeFilePath}
                  onSelectFile={handleFileSelect}
                />
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
                {activeFileObj?.is_test && !currentEditorContent ? (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '100%',
                      minHeight: '350px',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.88rem',
                      textAlign: 'center',
                      padding: '2rem',
                      backgroundColor: '#0d1117',
                    }}
                  >
                    🔒 Test suite implementation is protected and executed securely on the server.
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
            </div>
          ) : (
            <CodeEditor
              value={code}
              onChange={setCode}
              language={challenge.programming_language}
              filePath="solution.py"
              theme="vs-dark"
            />
          )}
        </div>

        {/* Stdin Area */}
        <div style={{ borderTop: '1px solid var(--border-color)', padding: '0.5rem 1rem', backgroundColor: '#090d16' }}>
          <label htmlFor="workspace-stdin" style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.25rem' }}>
            Standard Input (stdin)
          </label>
          <textarea
            id="workspace-stdin"
            value={stdin}
            onChange={(e) => setStdin(e.target.value)}
            placeholder="Enter standard input values (optional)..."
            spellCheck="false"
            style={{
              width: '100%',
              height: '42px',
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              padding: '0.4rem 0.6rem',
              resize: 'none',
              outline: 'none',
            }}
          />
        </div>

        {/* Action Buttons Toolbar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.75rem', padding: '0.65rem 1.25rem', backgroundColor: '#0e1422', borderTop: '1px solid var(--border-color)' }}>
          <button
            className="btn btn-secondary"
            onClick={handleRunCode}
            disabled={isRunning || isSubmitting || isEvaluating || !getPrimaryCode().trim()}
            style={{ padding: '0.45rem 1.15rem', fontSize: '0.85rem' }}
          >
            {isRunning ? (
              <>
                <span className="spinner-icon" />
                <span>Running in Sandbox...</span>
              </>
            ) : (
              <span>▶ Run Code</span>
            )}
          </button>
          <button
            className="btn-gency btn-gency-primary"
            onClick={handleSubmitSolution}
            disabled={isSubmitting || isEvaluating || isRunning || !getPrimaryCode().trim()}
            style={{
              padding: '0.5rem 1.4rem',
              fontSize: '0.88rem',
              boxShadow: isEvaluating ? '0 0 20px rgba(99, 102, 241, 0.6)' : 'none',
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
                <span>Evaluating Sandbox...</span>
              </>
            ) : (
              <>
                <span>Submit Solution</span>
                <span className="btn-arrow-icon">↗</span>
              </>
            )}
          </button>
        </div>

        {/* Bottom Panel Tabs */}
        <div className="workspace-tabs-bar">
          <button
            className={`workspace-tab-btn ${activeTab === 'execution' ? 'active' : ''}`}
            onClick={() => setActiveTab('execution')}
          >
            Terminal Output
          </button>
          <button
            className={`workspace-tab-btn ${activeTab === 'submission' ? 'active' : ''}`}
            onClick={() => setActiveTab('submission')}
          >
            Submission Result
            {isEvaluating && <span style={{ color: '#fbbf24', fontSize: '0.75rem', marginLeft: '0.35rem' }}>(Evaluating...)</span>}
            {submissionResult && (
              <span className={`badge badge-${submissionResult.status}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem', marginLeft: '0.35rem' }}>
                {submissionResult.status}
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Terminal / Output Panel */}
        {activeTab === 'execution' && (
          <div className="workspace-bottom-pane">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.82rem' }}>Execution Console</span>
              {isRunning && <span style={{ color: 'var(--accent-blue)', fontSize: '0.78rem' }}>Executing container...</span>}
              {executionResult && (
                <span className={`status-pill ${executionResult.status === 'SUCCESS' ? 'status-passed' : 'status-failed'}`}>
                  <span className="status-dot" />
                  <span>STATUS: {executionResult.status}</span>
                </span>
              )}
            </div>

            <div style={{ flex: 1, overflowY: 'auto' }}>
              {isRunning && (
                <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="spinner-icon" />
                  <span>Executing code in hardened Docker container sandbox...</span>
                </div>
              )}

              {executionError && (
                <div style={{ color: '#f87171', whiteSpace: 'pre-wrap' }}>
                  {executionError}
                </div>
              )}

              {!isRunning && !executionError && !executionResult && (
                <div style={{ color: 'var(--text-muted)' }}>
                  Click &quot;Run Code&quot; to test your code in Docker. Standard output and errors will appear here.
                </div>
              )}

              {!isRunning && executionResult && (
                <>
                  {executionResult.stdout && (
                    <div style={{ color: '#e2e8f0', whiteSpace: 'pre-wrap', marginBottom: '0.5rem' }}>
                      {executionResult.stdout}
                    </div>
                  )}
                  {executionResult.stderr && (
                    <div style={{ color: '#f87171', whiteSpace: 'pre-wrap', marginBottom: '0.5rem' }}>
                      {executionResult.stderr}
                    </div>
                  )}
                  {!executionResult.stdout && !executionResult.stderr && (
                    <div style={{ color: 'var(--text-muted)' }}>
                      (Program exited cleanly with no output)
                    </div>
                  )}
                </>
              )}
            </div>

            {executionResult && (
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.4rem', marginTop: 'auto' }}>
                <span>Exit Code: <strong style={{ color: '#fff' }}>{executionResult.exit_code}</strong></span>
                <span>Execution Time: <strong style={{ color: '#fff' }}>{executionResult.execution_time.toFixed(3)}s</strong></span>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Submission Result Panel */}
        {activeTab === 'submission' && (
          <div className="workspace-bottom-pane" style={{ height: '280px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.82rem' }}>Evaluation &amp; Grading</span>
              {isSubmitting && <span style={{ color: 'var(--accent-blue)', fontSize: '0.78rem' }}>Submitting...</span>}
              {isEvaluating && <span style={{ color: '#fbbf24', fontSize: '0.78rem' }}>Evaluating Solution (Celery Sandbox)...</span>}
              {submissionResult && (
                <span className={`status-pill ${submissionResult.status === 'PASSED' ? 'status-passed' : 'status-failed'}`}>
                  <span className="status-dot" />
                  <span>STATUS: {submissionResult.status}</span>
                </span>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {isSubmitting && (
                <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="spinner-icon" />
                  <span>Queueing solution for evaluation...</span>
                </div>
              )}

              {isEvaluating && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="spinner-icon" />
                    <span>Submission #{submissionId} is queued in Redis and executing Docker evaluation tests...</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Polling evaluation worker status every second...
                  </div>
                </div>
              )}

              {submissionError && (
                <div style={{ color: '#f87171', whiteSpace: 'pre-wrap' }}>
                  {submissionError}
                </div>
              )}

              {!isSubmitting && !isEvaluating && !submissionError && !submissionResult && (
                <div style={{ color: 'var(--text-muted)' }}>
                  Click &quot;Submit Solution&quot; to grade your solution against all challenge test cases.
                </div>
              )}

              {!isSubmitting && !isEvaluating && submissionResult && (
                <>
                  {/* Summary Card */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', backgroundColor: 'var(--bg-tertiary)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Final Status</div>
                      <span className={`badge badge-${submissionResult.status}`} style={{ marginTop: '0.2rem' }}>
                        {submissionResult.status}
                      </span>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Score Awarded</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
                        <AnimatedCounter value={submissionResult.score || 0} duration={800} /> / {challenge.points} pts
                      </div>
                    </div>
                    {evaluation && (
                      <>
                        <div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tests Passed</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: evaluation.tests_passed === evaluation.tests_total ? '#34d399' : '#f87171' }}>
                            <AnimatedCounter value={evaluation.tests_passed || 0} duration={600} /> / {evaluation.tests_total}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Execution Time</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
                            {evaluation.execution_time ? `${evaluation.execution_time.toFixed(3)}s` : '0.000s'}
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Skill Breakdown */}
                  {evaluation && (
                    <div
                      style={{
                        backgroundColor: 'var(--bg-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '0.85rem 1rem',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: '600',
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          marginBottom: '0.6rem',
                        }}
                      >
                        Skill Breakdown
                      </div>
                      {(() => {
                        const breakdownScores = evaluation.skill_breakdown?.scores;
                        const validSkills = Object.entries(SKILL_DIMENSION_NAMES)
                          .filter(([key]) => typeof breakdownScores?.[key] === 'number')
                          .map(([key, label]) => ({
                            key,
                            label,
                            score: breakdownScores[key],
                          }));

                        if (validSkills.length === 0) {
                          return (
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                              Skill breakdown is not available for this evaluation.
                            </p>
                          );
                        }

                        return (
                          <div
                            style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                              gap: '0.75rem',
                            }}
                          >
                            {validSkills.map((skill) => (
                              <div
                                key={skill.key}
                                style={{
                                  backgroundColor: 'var(--bg-tertiary)',
                                  padding: '0.65rem 0.85rem',
                                  borderRadius: 'var(--radius-sm)',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '0.4rem',
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
                                  <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>
                                    {skill.label}
                                  </span>
                                  <span
                                    style={{
                                      fontWeight: '700',
                                      color:
                                        skill.score >= 80
                                          ? '#34d399'
                                          : skill.score >= 50
                                          ? '#fbbf24'
                                          : '#f87171',
                                    }}
                                  >
                                    <AnimatedCounter value={skill.score} duration={600} />%
                                  </span>
                                </div>
                                <AnimatedProgress
                                  value={skill.score}
                                  max={100}
                                  height={5}
                                  color={
                                    skill.score >= 80
                                      ? '#34d399'
                                      : skill.score >= 50
                                      ? '#fbbf24'
                                      : '#f87171'
                                  }
                                />
                              </div>
                            ))}
                          </div>
                        );
                      })()}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Link
                      to="/submissions"
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.35rem 0.85rem', borderRadius: 'var(--radius-full)' }}
                    >
                      View Submission Archives &rarr;
                    </Link>
                  </div>

                  {/* Test Cases List */}
                  {evaluation && evaluation.test_results && evaluation.test_results.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                      <div style={{ fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Test Results Breakdown
                      </div>

                      {evaluation.test_results.map((tc, index) => (
                        <div
                          key={tc.test_case_id || index}
                          style={{
                            backgroundColor: 'var(--bg-tertiary)',
                            border: `1px solid ${tc.passed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                            borderRadius: 'var(--radius-sm)',
                            padding: '0.75rem 1rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.85rem' }}>
                              {tc.name || `Test Case #${index + 1}`}
                              {tc.is_hidden && (
                                <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                                  (Hidden Test)
                                </span>
                              )}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {tc.points} / {tc.max_points} pts
                              </span>
                              <span className={`status-pill ${tc.passed ? 'status-passed' : 'status-failed'}`} style={{ fontSize: '0.68rem', padding: '0.1rem 0.5rem' }}>
                                <span className="status-dot" />
                                {tc.passed ? 'Passed' : 'Failed'}
                              </span>
                            </div>
                          </div>

                          {!tc.is_hidden && (
                            <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.3rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {tc.input_data && (
                                <div>
                                  <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Input:</span>
                                  <span>{tc.input_data}</span>
                                </div>
                              )}
                              <div>
                                <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Expected:</span>
                                <span style={{ color: '#34d399' }}>{tc.expected_output}</span>
                              </div>
                              <div>
                                <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Actual:</span>
                                <span style={{ color: tc.passed ? '#34d399' : '#f87171' }}>{tc.actual_output || '(no output)'}</span>
                              </div>
                              {tc.stderr && (
                                <div style={{ color: '#f87171' }}>
                                  <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Stderr:</span>
                                  <span>{tc.stderr}</span>
                                </div>
                              )}
                            </div>
                          )}

                          {tc.is_hidden && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '0.3rem' }}>
                              Hidden test case — inputs and outputs are concealed for grading integrity.
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
