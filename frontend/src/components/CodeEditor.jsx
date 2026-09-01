import React from 'react';
import Editor from '@monaco-editor/react';

const LANGUAGE_MAP = {
  python: 'python',
  py: 'python',
  javascript: 'javascript',
  js: 'javascript',
  jsx: 'javascript',
  json: 'json',
  markdown: 'markdown',
  md: 'markdown',
  java: 'java',
  'c++': 'cpp',
  cpp: 'cpp',
  c: 'c',
  sql: 'sql',
  html: 'html',
  css: 'css',
  txt: 'plaintext',
};

function normalizeLanguage(lang, filePath = '') {
  if (filePath) {
    const ext = filePath.split('.').pop()?.toLowerCase();
    if (ext && LANGUAGE_MAP[ext]) {
      return LANGUAGE_MAP[ext];
    }
  }
  if (!lang) return 'plaintext';
  const clean = lang.trim().toLowerCase();
  return LANGUAGE_MAP[clean] || 'plaintext';
}

export default function CodeEditor({
  value = '',
  onChange,
  language = 'Python',
  filePath = '',
  readOnly = false,
  theme = 'vs-dark',
  options = {},
}) {
  const monacoLanguage = normalizeLanguage(language, filePath);

  const defaultOptions = {
    automaticLayout: true,
    minimap: { enabled: true },
    lineNumbers: 'on',
    wordWrap: 'on',
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
    tabSize: 4,
    scrollBeyondLastLine: false,
    smoothScrolling: true,
    cursorBlinking: 'smooth',
    renderWhitespace: 'selection',
    readOnly,
    padding: { top: 12, bottom: 12 },
    ...options,
  };

  const handleEditorChange = (val) => {
    if (onChange && !readOnly) {
      onChange(val || '');
    }
  };

  return (
    <div style={{ flex: 1, width: '100%', height: '100%', minHeight: '350px' }}>
      <Editor
        height="100%"
        width="100%"
        language={monacoLanguage}
        theme={theme}
        value={value}
        onChange={handleEditorChange}
        options={defaultOptions}
        loading={
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#8b949e',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
            }}
          >
            Initializing Monaco Editor...
          </div>
        }
      />
    </div>
  );
}
