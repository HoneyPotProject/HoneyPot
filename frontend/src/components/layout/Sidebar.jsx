// ── Sidebar.jsx ───────────────────────────────────────────
// App sidebar with navigation links and user info.

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Avatar } from '../ui/Avatar';
import { LayoutDashboard, FileText, Hexagon, LogOut } from 'lucide-react';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/documents', label: 'Documents',  Icon: FileText },
];

export function Sidebar({ collapsed = false, onToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <aside className={[styles.sidebar, collapsed ? styles.collapsed : ''].filter(Boolean).join(' ')}>
      {/* Logo */}
      <div className={styles.logo}>
        <span className={styles.logoIcon}>
          <Hexagon size={20} strokeWidth={2.5} />
        </span>
        {!collapsed && <span className={styles.logoText}>HoneyPot</span>}
      </div>

      {/* Nav */}
      <nav className={styles.nav} aria-label="Main navigation">
        <ul className={styles.navList}>
          {NAV_ITEMS.map(({ to, label, Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  [styles.navLink, isActive ? styles.active : ''].filter(Boolean).join(' ')
                }
                title={collapsed ? label : undefined}
              >
                <span className={styles.navIcon} aria-hidden="true">
                  <Icon size={18} strokeWidth={2.5} />
                </span>
                {!collapsed && <span className={styles.navLabel}>{label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom: user + logout */}
      <div className={styles.bottom}>
        <div className={styles.userCard}>
          <Avatar name={user?.name || 'User'} src={user?.avatar} size="md" />
          {!collapsed && (
            <div className={styles.userInfo}>
              <span className={styles.userName}>{user?.name}</span>
              <span className={styles.userEmail}>{user?.email}</span>
            </div>
          )}
        </div>
        <button
          type="button"
          className={styles.logoutBtn}
          onClick={handleLogout}
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut size={16} strokeWidth={2.5} aria-hidden="true" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
