import React, { useState, useEffect } from 'react';

export default function AnimatedProgress({
  value = 0,
  max = 100,
  height = 8,
  color = 'var(--accent-primary)',
  className = '',
  style = {},
}) {
  const [widthPercent, setWidthPercent] = useState(0);
  const targetPercent = Math.min(Math.max(max > 0 ? (value / max) * 100 : 0, 0), 100);

  useEffect(() => {
    // Delay slightly for smooth page entrance / staggered rendering
    const timer = setTimeout(() => {
      setWidthPercent(targetPercent);
    }, 120);

    return () => clearTimeout(timer);
  }, [targetPercent]);

  return (
    <div
      className={`progress-bar-bg ${className}`}
      style={{
        height,
        background: 'rgba(255, 255, 255, 0.06)',
        borderRadius: 'var(--radius-full)',
        overflow: 'hidden',
        position: 'relative',
        ...style,
      }}
    >
      <div
        className="progress-bar-fill"
        style={{
          width: `${widthPercent}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: 'inherit',
          transition: 'width 0.85s cubic-bezier(0.16, 1, 0.3, 1)',
          boxShadow: `0 0 10px ${color}55`,
        }}
      />
    </div>
  );
}
