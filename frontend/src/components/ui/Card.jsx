// ── Card.jsx ──────────────────────────────────────────────
// Glass-morphism card container with optional hover effect.

import styles from './Card.module.css';

export function Card({ children, className = '', hover = false, padding = 'md', ...props }) {
  return (
    <div
      className={[
        styles.card,
        hover ? styles.hover : '',
        styles[`pad-${padding}`],
        className,
      ].filter(Boolean).join(' ')}
      {...props}
    >
      {children}
    </div>
  );
}
