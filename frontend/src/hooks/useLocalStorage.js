// ── useLocalStorage ───────────────────────────────────────
// Syncs state to localStorage with JSON serialization.

import { useState, useCallback } from 'react';

/**
 * @template T
 * @param {string} key - localStorage key
 * @param {T} initialValue - default value if key is absent
 * @returns {[T, (value: T | ((prev: T) => T)) => void]}
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    setStoredValue(prev => {
      const next = typeof value === 'function' ? value(prev) : value;
      try {
        window.localStorage.setItem(key, JSON.stringify(next));
      } catch (err) {
        console.warn(`useLocalStorage: could not write key "${key}"`, err);
      }
      return next;
    });
  }, [key]);

  return [storedValue, setValue];
}
