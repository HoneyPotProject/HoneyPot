// ── PageLayout.jsx ────────────────────────────────────────
// Main authenticated layout: Sidebar + Navbar + main content area.

import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Navbar }  from './Navbar';
import styles from './PageLayout.module.css';

export function PageLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={styles.shell}>
      <Sidebar collapsed={collapsed} />
      <div className={styles.main}>
        <Navbar onToggleSidebar={() => setCollapsed(c => !c)} />
        <main className={styles.content}>
          {children}
        </main>
      </div>
    </div>
  );
}
