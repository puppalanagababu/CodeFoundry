import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getChallenge } from '../api/challenges';
import { runCode } from '../api/execution';
import { createSubmission, getSubmission } from '../api/submissions';
import Loading from '../components/Loading';
import CodeEditor from '../components/CodeEditor';
import RepositoryTree from '../components/RepositoryTree';

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
      .then((data) => {
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

          // Select default file: prioritize editable app python file, then first non-test file, then first file
          const defaultFile =
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

  // Helper to obtain the primary execution code
  const getPrimaryCode = () => {
    if (isRepoChallenge) {
      // Find main runnable code (e.g. app/calculator.py or current active python file or first non-readonly)
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

  const startPolling = (subId) => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
    }

    let attempts = 0;
    const maxAttempts = 30;

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
        } else if (attempts >= maxAttempts) {
          clearInterval(pollingTimerRef.current);
          pollingTimerRef.current = null;
          setIsEvaluating(false);
          setSubmissionError('Evaluation timed out. Please check back shortly.');
        }
      } catch (err) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
        setIsEvaluating(false);
        setSubmissionError(err.message || 'Failed to poll evaluation status.');
      }
    }, 1000);
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
        <div className="error-box">
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
          <Link to={`/challenges/${challenge.id}`} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            &larr; Challenge Overview
          </Link>
          <span className={`badge badge-${challenge.difficulty}`}>
            {challenge.difficulty}
          </span>
        </div>

        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: '700', marginBottom: '0.5rem' }}>
            {challenge.title}
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span className="badge badge-type">{challenge.challenge_type.replace('_', ' ')}</span>
            <span className="badge badge-lang">{challenge.programming_language}</span>
            <span className="badge badge-lang">{challenge.points} pts</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', padding: '0.6rem 0' }}>
          <span>Timeout: <strong style={{ color: 'var(--text-secondary)' }}>{challenge.time_limit}s</strong></span>
          <span>Memory: <strong style={{ color: 'var(--text-secondary)' }}>{challenge.memory_limit} MB</strong></span>
        </div>

        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            Description & Requirements
          </h3>
          <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: '1.6' }}>
            {challenge.description}
          </div>
        </div>
      </aside>

      {/* Right Panel: Editor Shell, Inputs & Panels */}
      <main className="workspace-panel-right">
        <div className="editor-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>{isRepoChallenge ? activeFilePath || 'repository' : 'solution.py'}</span>
            {isCurrentFileReadOnly && (
              <span className="badge" style={{ fontSize: '0.65rem', backgroundColor: '#30363d', color: '#8b949e' }}>
                READ-ONLY
              </span>
            )}
          </div>
          <span>{challenge.programming_language}</span>
        </div>

        {/* Code Editor Area: Multi-file layout or Single-file */}
        {isRepoChallenge ? (
          <div className="editor-with-repo-layout">
            <RepositoryTree
              files={repoFiles}
              activeFile={activeFilePath}
              onSelectFile={handleFileSelect}
            />
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

        {/* Stdin Area */}
        <div className="stdin-container">
          <label className="stdin-label" htmlFor="workspace-stdin">
            Standard Input (stdin)
          </label>
          <textarea
            id="workspace-stdin"
            className="stdin-textarea"
            value={stdin}
            onChange={(e) => setStdin(e.target.value)}
            placeholder="Enter standard input values (optional)..."
            spellCheck="false"
          />
        </div>

        {/* Action Buttons */}
        <div className="editor-footer">
          <button
            className="btn btn-secondary"
            onClick={handleRunCode}
            disabled={isRunning || isSubmitting || isEvaluating || !getPrimaryCode().trim()}
          >
            {isRunning ? 'Running in Docker...' : 'Run Code'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSubmitSolution}
            disabled={isSubmitting || isEvaluating || isRunning || !getPrimaryCode().trim()}
          >
            {isSubmitting
              ? 'Submitting...'
              : isEvaluating
              ? 'Evaluating...'
              : 'Submit Solution'}
          </button>
        </div>

        {/* Bottom Panel Tabs */}
        <div className="panel-tabs">
          <button
            className={`panel-tab ${activeTab === 'execution' ? 'active' : ''}`}
            onClick={() => setActiveTab('execution')}
          >
            Terminal Output
          </button>
          <button
            className={`panel-tab ${activeTab === 'submission' ? 'active' : ''}`}
            onClick={() => setActiveTab('submission')}
          >
            Submission Result
            {isEvaluating && <span style={{ color: '#d29922', fontSize: '0.75rem' }}>(Evaluating...)</span>}
            {submissionResult && (
              <span className={`badge badge-${submissionResult.status}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                {submissionResult.status}
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Terminal / Output Panel */}
        {activeTab === 'execution' && (
          <div className="terminal-panel">
            <div className="terminal-header">
              <span>Execution Output</span>
              {isRunning && <span style={{ color: '#58a6ff' }}>Executing...</span>}
              {executionResult && (
                <span className={executionResult.status === 'SUCCESS' ? 'status-indicator-success' : 'status-indicator-failed'}>
                  STATUS: {executionResult.status}
                </span>
              )}
            </div>

            <div className="terminal-body">
              {isRunning && (
                <div style={{ color: 'var(--text-muted)' }}>
                  Running code in isolated Docker container sandbox...
                </div>
              )}

              {executionError && (
                <div className="terminal-stderr">
                  {executionError}
                </div>
              )}

              {!isRunning && !executionError && !executionResult && (
                <div className="terminal-empty">
                  Click &quot;Run Code&quot; to test your code in Docker. Output will appear here.
                </div>
              )}

              {!isRunning && executionResult && (
                <>
                  {executionResult.stdout && (
                    <div className="terminal-stdout">
                      {executionResult.stdout}
                    </div>
                  )}
                  {executionResult.stderr && (
                    <div className="terminal-stderr">
                      {executionResult.stderr}
                    </div>
                  )}
                  {!executionResult.stdout && !executionResult.stderr && (
                    <div className="terminal-empty">
                      (Program completed with no output)
                    </div>
                  )}
                </>
              )}
            </div>

            {executionResult && (
              <div className="terminal-footer">
                <span>Exit Code: <strong>{executionResult.exit_code}</strong></span>
                <span>Execution Time: <strong>{executionResult.execution_time.toFixed(3)}s</strong></span>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Submission Result Panel */}
        {activeTab === 'submission' && (
          <div className="terminal-panel" style={{ height: '240px', minHeight: '180px' }}>
            <div className="terminal-header">
              <span>Evaluation & Grading</span>
              {isSubmitting && <span style={{ color: '#58a6ff' }}>Submitting...</span>}
              {isEvaluating && <span style={{ color: '#d29922' }}>Evaluating Solution (Celery Async)...</span>}
              {submissionResult && (
                <span className={submissionResult.status === 'PASSED' ? 'status-indicator-success' : 'status-indicator-failed'}>
                  STATUS: {submissionResult.status}
                </span>
              )}
            </div>

            <div className="submission-result-container">
              {isSubmitting && (
                <div style={{ color: 'var(--text-muted)' }}>
                  Queueing solution for evaluation...
                </div>
              )}

              {isEvaluating && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                  <div>Submission #{submissionId} is queued in Redis and running across Docker test cases...</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Polling evaluation status every second...</div>
                </div>
              )}

              {submissionError && (
                <div className="terminal-stderr">
                  {submissionError}
                </div>
              )}

              {!isSubmitting && !isEvaluating && !submissionError && !submissionResult && (
                <div className="terminal-empty">
                  Click &quot;Submit Solution&quot; to grade your solution against all challenge test cases.
                </div>
              )}

              {!isSubmitting && !isEvaluating && submissionResult && (
                <>
                  {/* Summary Card */}
                  <div className="submission-summary-card">
                    <div>
                      <div className="submission-stat-label">Final Status</div>
                      <span className={`badge badge-${submissionResult.status}`}>
                        {submissionResult.status}
                      </span>
                    </div>
                    <div>
                      <div className="submission-stat-label">Score Awarded</div>
                      <div className="submission-stat-val">
                        {submissionResult.score} / {challenge.points} pts
                      </div>
                    </div>
                    {evaluation && (
                      <>
                        <div>
                          <div className="submission-stat-label">Tests Passed</div>
                          <div className="submission-stat-val" style={{ color: evaluation.tests_passed === evaluation.tests_total ? '#3fb950' : '#f85149' }}>
                            {evaluation.tests_passed} / {evaluation.tests_total}
                          </div>
                        </div>
                        <div>
                          <div className="submission-stat-label">Execution Time</div>
                          <div className="submission-stat-val">
                            {evaluation.execution_time ? `${evaluation.execution_time.toFixed(3)}s` : '0.000s'}
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Link
                      to="/submissions"
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}
                    >
                      View Submission History &rarr;
                    </Link>
                  </div>

                  {/* Test Cases List */}
                  {evaluation && evaluation.test_results && evaluation.test_results.length > 0 && (
                    <div className="test-cases-list">
                      <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Test Results Breakdown
                      </div>

                      {evaluation.test_results.map((tc, index) => (
                        <div
                          key={tc.test_case_id || index}
                          className={`test-case-item ${tc.passed ? 'passed' : 'failed'}`}
                        >
                          <div className="test-case-header">
                            <span>
                              {tc.name || `Test Case #${index + 1}`}
                              {tc.is_hidden && (
                                <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', color: '#8b949e', fontWeight: 'normal' }}>
                                  (Hidden Test)
                                </span>
                              )}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {tc.points} / {tc.max_points} pts
                              </span>
                              <span className={tc.passed ? 'status-indicator-success' : 'status-indicator-failed'}>
                                {tc.passed ? 'Passed' : 'Failed'}
                              </span>
                            </div>
                          </div>

                          {/* Public Test Details */}
                          {!tc.is_hidden && (
                            <div className="test-case-details">
                              {tc.input_data && (
                                <div className="test-case-field">
                                  <span className="test-case-field-label">Input:</span>
                                  <span>{tc.input_data}</span>
                                </div>
                              )}
                              <div className="test-case-field">
                                <span className="test-case-field-label">Expected:</span>
                                <span>{tc.expected_output}</span>
                              </div>
                              <div className="test-case-field">
                                <span className="test-case-field-label">Actual:</span>
                                <span>{tc.actual_output || '(no output)'}</span>
                              </div>
                              {tc.stderr && (
                                <div className="test-case-field" style={{ color: '#f85149' }}>
                                  <span className="test-case-field-label">Stderr:</span>
                                  <span>{tc.stderr}</span>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Hidden Test Notice */}
                          {tc.is_hidden && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                              Hidden test case — input and expected output are concealed for grading integrity.
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
