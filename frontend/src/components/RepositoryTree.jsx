import React, { useState } from 'react';

/**
 * Builds a nested tree structure from flat file path list.
 */
function buildFileTree(files) {
  const root = {};

  files.forEach((file) => {
    const parts = file.path.split('/');
    let current = root;

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      if (isFile) {
        current[part] = {
          __isFile: true,
          ...file,
        };
      } else {
        if (!current[part] || current[part].__isFile) {
          current[part] = { __isDir: true, children: {} };
        }
        current = current[part].children;
      }
    });
  });

  return root;
}

function TreeNode({ name, node, activeFile, onSelectFile, level = 0 }) {
  const [isOpen, setIsOpen] = useState(true);

  if (node.__isFile) {
    const isSelected = activeFile === node.path;
    return (
      <div
        className={`tree-file ${isSelected ? 'active' : ''}`}
        style={{
          paddingLeft: `${level * 14 + 14}px`,
          paddingRight: '12px',
          paddingTop: '6px',
          paddingBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          fontSize: '0.84rem',
          color: isSelected ? '#fff' : 'var(--text-secondary)',
          background: isSelected ? 'rgba(99, 102, 241, 0.18)' : 'transparent',
          borderLeft: isSelected ? '2px solid var(--accent-primary)' : '2px solid transparent',
          boxShadow: isSelected ? 'inset 0 0 12px rgba(99, 102, 241, 0.12)' : 'none',
          transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        onClick={() => onSelectFile(node.path)}
        title={node.path}
      >
        <span style={{ fontSize: '0.9rem', opacity: isSelected ? 1 : 0.8 }}>
          {node.path.endsWith('.py') ? '🐍' : node.path.endsWith('.md') ? '📝' : '📄'}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: isSelected ? 600 : 400 }}>
          {name}
        </span>
        {node.is_readonly && (
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }} title="Read-only file">
            🔒
          </span>
        )}
        {node.is_test && (
          <span className="badge badge-SECURITY" style={{ fontSize: '0.62rem', padding: '0.1rem 0.35rem' }}>
            test
          </span>
        )}
      </div>
    );
  }

  // Directory node
  return (
    <div className="tree-dir">
      <div
        style={{
          paddingLeft: `${level * 14 + 10}px`,
          paddingRight: '10px',
          paddingTop: '6px',
          paddingBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          cursor: 'pointer',
          fontSize: '0.82rem',
          fontWeight: 600,
          color: 'var(--text-secondary)',
          userSelect: 'none',
          transition: 'color 0.15s ease',
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'inline-block', transition: 'transform 0.2s ease', transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}>
          ▶
        </span>
        <span style={{ fontSize: '0.9rem' }}>
          {isOpen ? '📂' : '📁'}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
          {name}/
        </span>
      </div>
      {isOpen && (
        <div className="tree-dir-children" style={{ animation: 'fadeIn 0.2s ease-out' }}>
          {Object.entries(node.children || {}).map(([childName, childNode]) => (
            <TreeNode
              key={childName}
              name={childName}
              node={childNode}
              activeFile={activeFile}
              onSelectFile={onSelectFile}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function RepositoryTree({
  files = [],
  activeFile,
  onSelectFile,
}) {
  if (!files || files.length === 0) {
    return null;
  }

  const tree = buildFileTree(files);

  return (
    <div className="repository-tree" style={{ padding: '0.5rem 0' }}>
      <div style={{ padding: '0.4rem 1rem 0.6rem', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>Explorer</span>
        <span style={{ fontSize: '0.7rem', color: 'var(--accent-blue)' }}>{files.length} files</span>
      </div>
      {Object.entries(tree).map(([name, node]) => (
        <TreeNode
          key={name}
          name={name}
          node={node}
          activeFile={activeFile}
          onSelectFile={onSelectFile}
          level={0}
        />
      ))}
    </div>
  );
}
