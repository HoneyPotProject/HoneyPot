// ── Modal.jsx ─────────────────────────────────────────────
// Accessible modal dialog using the native <dialog> element.

import { useEffect, useRef } from 'react';
import { Button } from './Button';
import styles from './Modal.module.css';

/**
 * @param {boolean} isOpen
 * @param {() => void} onClose
 * @param {string} [title]
 * @param {'sm'|'md'|'lg'} [size='md']
 */
export function Modal({ isOpen, onClose, title, size = 'md', children }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen) {
      if (!dialog.open) dialog.showModal();
    } else {
      if (dialog.open) dialog.close();
    }
  }, [isOpen]);

  // Close on backdrop click
  const handleClick = (e) => {
    if (e.target === dialogRef.current) onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      className={[styles.dialog, styles[size]].join(' ')}
      onClose={onClose}
      onClick={handleClick}
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div className={styles.inner}>
        {(title || onClose) && (
          <header className={styles.header}>
            {title && <h2 id="modal-title" className={styles.title}>{title}</h2>}
            <button
              type="button"
              className={styles.closeBtn}
              onClick={onClose}
              aria-label="Close dialog"
            >
              ✕
            </button>
          </header>
        )}
        <div className={styles.body}>{children}</div>
      </div>
    </dialog>
  );
}
