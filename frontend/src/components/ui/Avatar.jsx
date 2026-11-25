// ── Avatar.jsx ────────────────────────────────────────────
// User avatar with image fallback to initials.

import { getInitials } from '../../utils/formatters';
import styles from './Avatar.module.css';

export function Avatar({ name = '', src, size = 'md', className = '' }) {
  const initials = getInitials(name);

  return (
    <div
      className={[styles.avatar, styles[size], className].filter(Boolean).join(' ')}
      aria-label={name}
      title={name}
    >
      {src ? (
        <img src={src} alt={name} className={styles.img} />
      ) : (
        <span className={styles.initials} aria-hidden="true">{initials}</span>
      )}
    </div>
  );
}
