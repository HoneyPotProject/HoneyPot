// ── formatters.js ─────────────────────────────────────────
// Pure formatting/display helpers.

/**
 * Format an ISO date string as a human-readable relative time.
 * @param {string} isoString
 * @returns {string}
 */
export function formatRelativeTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr  = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr  / 24);

  if (diffSec < 60)   return 'just now';
  if (diffMin < 60)   return `${diffMin}m ago`;
  if (diffHr  < 24)   return `${diffHr}h ago`;
  if (diffDay < 7)    return `${diffDay}d ago`;
  if (diffDay < 30)   return `${Math.floor(diffDay / 7)}w ago`;
  if (diffDay < 365)  return `${Math.floor(diffDay / 30)}mo ago`;
  return `${Math.floor(diffDay / 365)}y ago`;
}

/**
 * Format an ISO date string as "Nov 25, 2026".
 * @param {string} isoString
 * @returns {string}
 */
export function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

/**
 * Truncate text to `maxLen` chars with an ellipsis.
 * @param {string} text
 * @param {number} [maxLen=120]
 * @returns {string}
 */
export function truncate(text, maxLen = 120) {
  if (!text) return '';
  return text.length <= maxLen ? text : `${text.slice(0, maxLen).trimEnd()}…`;
}

/**
 * Convert a string to Title Case.
 * @param {string} str
 * @returns {string}
 */
export function toTitleCase(str) {
  return str.replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Get initials from a name (up to 2 chars).
 * @param {string} name
 * @returns {string}
 */
export function getInitials(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() || '')
    .join('');
}

/**
 * Format a number with compact notation (1.2K, 3.5M).
 * @param {number} n
 * @returns {string}
 */
export function formatCompact(n) {
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
}
