// ── Button.jsx ────────────────────────────────────────────
// Flexible button component with variants, sizes, and loading state.

import styles from './Button.module.css';

/**
 * @param {'primary'|'secondary'|'ghost'|'danger'|'outline'} [variant='primary']
 * @param {'sm'|'md'|'lg'} [size='md']
 * @param {boolean} [loading=false]
 * @param {boolean} [fullWidth=false]
 * @param {string} [leftIcon]
 * @param {string} [rightIcon]
 */
export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  children,
  className = '',
  disabled,
  type = 'button',
  ...props
}) {
  const classes = [
    styles.btn,
    styles[variant],
    styles[size],
    fullWidth ? styles.fullWidth : '',
    loading ? styles.loading : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <span className={styles.spinner} aria-hidden="true" />
      ) : leftIcon ? (
        <span className={styles.icon} aria-hidden="true">{leftIcon}</span>
      ) : null}
      {children && <span className={styles.label}>{children}</span>}
      {!loading && rightIcon && (
        <span className={styles.icon} aria-hidden="true">{rightIcon}</span>
      )}
    </button>
  );
}
