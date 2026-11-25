// ── useDebounce ───────────────────────────────────────────
// Returns a debounced copy of `value` after `delay` ms of inactivity.

import { useState, useEffect } from 'react';

/**
 * @template T
 * @param {T} value
 * @param {number} [delay=400]
 * @returns {T}
 */
export function useDebounce(value, delay = 400) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
