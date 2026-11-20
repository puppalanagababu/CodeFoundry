import React, { useState } from 'react';
import {
  Folder,
  FolderOpen,
  FileCode2,
  FileText,
  File,
  Lock,
  ChevronRight,
  ChevronDown,
  CheckCircle2,
} from 'lucide-react';

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
          color: isSelected ? 'var(--pastel-lavender-text)' : 'var(--text-secondary)',
          background: isSelected ? 'var(--pastel-lavender)' : 'transparent',
          borderLeft: isSelected ? '3px solid var(--accent-primary)' : '3px solid transparent',
          borderRadius: 'var(--radius-xs)',
          margin: '1px 6px',
          fontWeight: isSelected ? 700 : 500,
          transition: 'all 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        onClick={() => onSelectFile(node.path)}
        title={node.path}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', opacity: isSelected ? 1 : 0.85 }}>
          {node.path.endsWith('.py') ? (
            <FileCode2 size={15} color={isSelected ? 'var(--accent-primary)' : '#3B82F6'} />
          ) : node.path.endsWith('.md') ? (
            <FileText size={15} color="#8B5CF6" />
          ) : (
            <File size={15} color="#64748B" />
          )}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: isSelected ? 600 : 400 }}>
          {name}
        </span>
        {node.is_readonly && (
          <span style={{ display: 'inline-flex', alignItems: 'center', color: '#EF4444' }} title="Read-only protected file">
            <Lock size={12} />
          </span>
        )}
        {node.is_test && (
          <span className="badge badge-SECURITY" style={{ fontSize: '0.62rem', padding: '0.1rem 0.35rem', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
            <CheckCircle2 size={10} /> test
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
        <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center' }}>
          {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', color: isOpen ? 'var(--accent-primary)' : '#64748B' }}>
          {isOpen ? <FolderOpen size={15} /> : <Folder size={15} />}
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
