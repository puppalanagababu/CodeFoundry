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
        style={{ paddingLeft: `${level * 14 + 10}px` }}
        onClick={() => onSelectFile(node.path)}
        title={node.path}
      >
        <span className="tree-icon">{node.path.endsWith('.py') ? '🐍' : node.path.endsWith('.md') ? '📝' : '📄'}</span>
        <span className="tree-name">{name}</span>
        {node.is_readonly && (
          <span className="tree-badge readonly" title="Read-only file">
            🔒
          </span>
        )}
        {node.is_test && (
          <span className="tree-badge test" title="Test file">
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
        className="tree-dir-header"
        style={{ paddingLeft: `${level * 14 + 8}px` }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="tree-arrow">{isOpen ? '▼' : '▶'}</span>
        <span className="tree-icon">{isOpen ? '📂' : '📁'}</span>
        <span className="tree-name">{name}/</span>
      </div>
      {isOpen && (
        <div className="tree-dir-children">
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
    <div className="repository-tree-container">
      <div className="repository-tree-header">
        <span>Repository Files</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{files.length} files</span>
      </div>
      <div className="repository-tree-body">
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
    </div>
  );
}
