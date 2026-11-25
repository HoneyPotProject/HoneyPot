// ── storage.js ────────────────────────────────────────────
// Low-level localStorage helpers (use useLocalStorage hook in components).

/**
 * Get a JSON-parsed value from localStorage.
 * @template T
 * @param {string} key
 * @param {T} fallback
 * @returns {T}
 */
export function getItem(key, fallback = null) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw !== null ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

/**
 * Serialize and save a value to localStorage.
 * @param {string} key
 * @param {*} value
 */
export function setItem(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.warn(`storage.setItem: could not write "${key}"`, err);
  }
}

/**
 * Remove a key from localStorage.
 * @param {string} key
 */
export function removeItem(key) {
  try {
    window.localStorage.removeItem(key);
  } catch { /* ignore */ }
}

/**
 * Clear all app-prefixed keys (keys starting with "hp_").
 */
export function clearAppStorage() {
  try {
    Object.keys(window.localStorage)
      .filter(k => k.startsWith('hp_'))
      .forEach(k => window.localStorage.removeItem(k));
  } catch { /* ignore */ }
}
