// ── validators.js ─────────────────────────────────────────
// Pure validation functions for forms.

/**
 * Validate an email address.
 * @param {string} email
 * @returns {string|null} error message or null
 */
export function validateEmail(email) {
  if (!email) return 'Email is required.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Please enter a valid email.';
  return null;
}

/**
 * Validate a password (min 8 chars, 1 uppercase, 1 number).
 * @param {string} password
 * @returns {string|null} error message or null
 */
export function validatePassword(password) {
  if (!password) return 'Password is required.';
  if (password.length < 8) return 'Password must be at least 8 characters.';
  if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter.';
  if (!/[0-9]/.test(password)) return 'Password must contain at least one number.';
  return null;
}

/**
 * Validate a display name (2–50 Unicode chars).
 * @param {string} name
 * @returns {string|null}
 */
export function validateName(name) {
  if (!name || !name.trim()) return 'Name is required.';
  if (name.trim().length < 2) return 'Name must be at least 2 characters.';
  if (name.trim().length > 50) return 'Name must be 50 characters or fewer.';
  return null;
}

/**
 * Validate a document title.
 * @param {string} title
 * @returns {string|null}
 */
export function validateDocTitle(title) {
  if (!title || !title.trim()) return 'Title is required.';
  if (title.trim().length < 3) return 'Title must be at least 3 characters.';
  if (title.trim().length > 120) return 'Title must be 120 characters or fewer.';
  return null;
}

/**
 * Calculate password strength score (0–4).
 * @param {string} password
 * @returns {{ score: number, label: string, color: string }}
 */
export function getPasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' };

  let score = 0;
  if (password.length >= 8)  score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels = [
    { score: 0, label: '', color: '' },
    { score: 1, label: 'Weak', color: 'var(--color-danger)' },
    { score: 2, label: 'Fair', color: 'var(--color-warning)' },
    { score: 3, label: 'Good', color: 'var(--color-info)' },
    { score: 4, label: 'Strong', color: 'var(--color-success)' },
    { score: 5, label: 'Very Strong', color: 'var(--color-success)' },
  ];

  return levels[Math.min(score, 5)];
}
