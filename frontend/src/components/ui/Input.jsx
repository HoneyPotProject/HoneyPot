// ── Input.jsx ─────────────────────────────────────────────
// Accessible form input with label, error, helper, and icon slots.

import { forwardRef, useState } from 'react';
import styles from './Input.module.css';

export const Input = forwardRef(function Input({
  label,
  error,
  helper,
  leftIcon,
  rightElement,
  id,
  className = '',
  containerClassName = '',
  type = 'text',
  ...props
}, ref) {
  const inputId = id || `input-${Math.random().toString(36).slice(2, 8)}`;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className={[styles.container, containerClassName].filter(Boolean).join(' ')}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}
      <div className={styles.inputWrap}>
        {leftIcon && (
          <span className={styles.leftIcon} aria-hidden="true">{leftIcon}</span>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          className={[
            styles.input,
            error    ? styles.hasError : '',
            leftIcon ? styles.hasLeft  : '',
            rightElement ? styles.hasRight : '',
            className,
          ].filter(Boolean).join(' ')}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={errorId}
          {...props}
        />
        {rightElement && (
          <span className={styles.rightSlot}>{rightElement}</span>
        )}
      </div>
      {error && (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      )}
      {helper && !error && (
        <p className={styles.helper}>{helper}</p>
      )}
    </div>
  );
});
