import React from 'react';

export default function Loading({ message = 'Loading...' }) {
  return (
    <div className="loading-box">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  );
}
