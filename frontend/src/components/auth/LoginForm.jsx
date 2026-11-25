// ── LoginForm.jsx ─────────────────────────────────────────
// Login form with email/password validation and show-password toggle.

import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { validateEmail, validatePassword } from '../../utils/validators';
import { Mail, Lock, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import styles from './AuthForm.module.css';

export function LoginForm({ onSuccess, onSwitchTab }) {
  const { login, loading, error, clearError } = useAuth();
  const [fields, setFields] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [showPw, setShowPw] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFields(f => ({ ...f, [name]: value }));
    if (errors[name]) setErrors(e => ({ ...e, [name]: null }));
    clearError();
  };

  const validate = () => {
    const errs = {};
    const emailErr = validateEmail(fields.email);
    if (emailErr) errs.email = emailErr;
    if (!fields.password) errs.password = 'Password is required.';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    const result = await login({ email: fields.email, password: fields.password });
    if (result.success) onSuccess();
  };

  return (
    <form onSubmit={handleSubmit} noValidate className={styles.form}>
      {error && (
        <div className={styles.globalError} role="alert">
          <AlertTriangle size={16} aria-hidden="true" /> {error}
        </div>
      )}

      <Input
        label="Email address"
        type="email"
        name="email"
        id="login-email"
        value={fields.email}
        onChange={handleChange}
        error={errors.email}
        autoComplete="username"
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        enterKeyHint="next"
        placeholder="you@example.com"
        leftIcon={<Mail size={16} strokeWidth={2} />}
        required
      />

      <Input
        label="Password"
        type={showPw ? 'text' : 'password'}
        name="password"
        id="login-password"
        value={fields.password}
        onChange={handleChange}
        error={errors.password}
        autoComplete="current-password"
        enterKeyHint="done"
        placeholder="••••••••"
        leftIcon={<Lock size={16} strokeWidth={2} />}
        rightElement={
          <button
            type="button"
            className={styles.showPwBtn}
            onClick={() => setShowPw(s => !s)}
            aria-label={showPw ? 'Hide password' : 'Show password'}
          >
            {showPw
              ? <EyeOff size={15} strokeWidth={2} />
              : <Eye size={15} strokeWidth={2} />
            }
          </button>
        }
        required
      />

      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={loading}
      >
        Sign In
      </Button>

      <p className={styles.switchText}>
        Don't have an account?{' '}
        <button type="button" className={styles.switchBtn} onClick={onSwitchTab}>
          Sign up free
        </button>
      </p>
    </form>
  );
}
