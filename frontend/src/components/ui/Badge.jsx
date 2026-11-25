// ── Badge.jsx ─────────────────────────────────────────────
// Status/tag badges.

import styles from './Badge.module.css';

const COLOR_MAP = {
  primary:  'primary',
  secondary:'secondary',
  success:  'success',
  warning:  'warning',
  danger:   'danger',
  info:     'info',
  default:  'default',
  // Document statuses
  published:'success',
  draft:    'warning',
  archived: 'default',
};

export function Badge({ children, variant = 'default', dot = false, className = '' }) {
  const colorKey = COLOR_MAP[variant] || 'default';
  return (
    <span className={[styles.badge, styles[colorKey], className].filter(Boolean).join(' ')}>
      {dot && <span className={styles.dot} aria-hidden="true" />}
      {children}
    </span>
  );
}
