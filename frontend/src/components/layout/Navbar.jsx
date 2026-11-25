// ── Navbar.jsx ────────────────────────────────────────────
// Top navigation bar with page title, search, and sidebar toggle.

import { useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Avatar } from '../ui/Avatar';
import styles from './Navbar.module.css';

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/documents': 'Documents',
};

export function Navbar({ onToggleSidebar }) {
  const location = useLocation();
  const { user } = useAuth();
  const title = PAGE_TITLES[location.pathname] || 'HoneyPot';

  return (
    <header className={styles.navbar}>
      <div className={styles.left}>
        <button
          type="button"
          className={styles.menuBtn}
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
        >
          <span className={styles.menuIcon} aria-hidden="true">☰</span>
        </button>
        <h1 className={styles.pageTitle}>{title}</h1>
      </div>

      <div className={styles.right}>
        <span className={styles.greeting}>
          Hey, <strong>{user?.name?.split(' ')[0] || 'there'}</strong> 👋
        </span>
        <Avatar name={user?.name || ''} src={user?.avatar} size="sm" />
      </div>
    </header>
  );
}
