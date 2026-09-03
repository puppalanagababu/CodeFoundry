import React, { useState, useEffect, useRef } from 'react';

export default function AnimatedCounter({ value, duration = 900, suffix = '', prefix = '', decimals = 0 }) {
  const [displayValue, setDisplayValue] = useState(0);
  const target = typeof value === 'number' ? value : Number(value) || 0;
  const startRef = useRef(0);
  const startTimeRef = useRef(null);
  const animFrameRef = useRef(null);

  useEffect(() => {
    // If reduced motion is requested by user, display directly
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplayValue(target);
      return;
    }

    const startVal = startRef.current;
    const diff = target - startVal;
    if (diff === 0) {
      setDisplayValue(target);
      return;
    }

    startTimeRef.current = null;

    const easeOutQuad = (t) => t * (2 - t);

    const step = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);
      const easedProgress = easeOutQuad(progress);
      const current = startVal + diff * easedProgress;

      setDisplayValue(current);

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(step);
      } else {
        startRef.current = target;
        setDisplayValue(target);
      }
    };

    animFrameRef.current = requestAnimationFrame(step);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [target, duration]);

  const formatted = decimals > 0 ? displayValue.toFixed(decimals) : Math.round(displayValue);

  return (
    <span className="animated-counter">
      {prefix}{formatted}{suffix}
    </span>
  );
}
