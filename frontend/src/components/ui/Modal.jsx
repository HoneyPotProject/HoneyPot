
import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import styles from './Modal.module.css';

export function Modal({ isOpen, onClose, title, size = 'md', children }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  const handleClose = () => {
    if (isOpen) onClose();
  };

  const handleClick = (e) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className={[styles.dialog, styles[size]].join(' ')}
      onClose={handleClose}
      onClick={handleClick}
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div className={styles.inner}>
        {(title || onClose) && (
          <header className={styles.header}>
            {title && (
              <h2 id="modal-title" className={styles.title}>
                {title}
              </h2>
            )}

            <button
              type="button"
              className={styles.closeBtn}
              onClick={onClose}
              aria-label="Close dialog"
            >
              <X size={16} strokeWidth={2.5} />
            </button>
          </header>
        )}

        <div className={styles.body}>{children}</div>
      </div>
    </dialog>
  );
}
