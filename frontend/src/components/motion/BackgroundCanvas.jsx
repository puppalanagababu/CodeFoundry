import React from 'react';

export default function BackgroundCanvas() {
  return (
    <div className="ambient-background-system" aria-hidden="true">
      <div className="ambient-grid-overlay" />
      <div className="ambient-glow-orb orb-primary" />
      <div className="ambient-glow-orb orb-secondary" />
      <div className="ambient-glow-orb orb-tertiary" />
    </div>
  );
}
