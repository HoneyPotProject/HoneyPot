// ── AuthPage.jsx ──────────────────────────────────────────
// Combined Login + Signup page with tab switching.

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { LoginForm }  from '../../components/auth/LoginForm';
import { SignupForm } from '../../components/auth/SignupForm';
import { Hexagon } from 'lucide-react';
import styles from './AuthPage.module.css';

export function AuthPage() {
  const [tab, setTab] = useState('login');
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    navigate('/dashboard', { replace: true });
    return null;
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>
              <Hexagon size={24} strokeWidth={2.5} />
            </span>
            <span className={styles.logoName}>HoneyPot</span>
          </div>
          <p className={styles.tagline}>
            {tab === 'login'
              ? 'Welcome back! Sign in to continue.'
              : 'Create your account and get started.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className={styles.tabs} role="tablist" aria-label="Authentication mode">
          <button
            type="button"
            role="tab"
            id="tab-login"
            aria-selected={tab === 'login'}
            aria-controls="panel-login"
            className={[styles.tab, tab === 'login' ? styles.activeTab : ''].filter(Boolean).join(' ')}
            onClick={() => setTab('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            id="tab-signup"
            aria-selected={tab === 'signup'}
            aria-controls="panel-signup"
            className={[styles.tab, tab === 'signup' ? styles.activeTab : ''].filter(Boolean).join(' ')}
            onClick={() => setTab('signup')}
          >
            Sign Up
          </button>
          {/* Hidden — no sliding indicator needed in neobrutalism; solid bg does the work */}
          <div className={styles.tabIndicator} aria-hidden="true" />
        </div>

        {/* Form Panels */}
        <div
          id="panel-login"
          role="tabpanel"
          aria-labelledby="tab-login"
          hidden={tab !== 'login'}
          className={styles.panel}
        >
          <LoginForm onSuccess={() => navigate('/dashboard')} onSwitchTab={() => setTab('signup')} />
        </div>

        <div
          id="panel-signup"
          role="tabpanel"
          aria-labelledby="tab-signup"
          hidden={tab !== 'signup'}
          className={styles.panel}
        >
          <SignupForm onSuccess={() => navigate('/dashboard')} onSwitchTab={() => setTab('login')} />
        </div>
      </div>
    </div>
  );
}
