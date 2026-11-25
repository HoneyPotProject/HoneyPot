// ── SignupForm.jsx ────────────────────────────────────────
// Signup form with name, email, password + strength indicator.

import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { validateEmail, validatePassword, validateName, getPasswordStrength } from '../../utils/validators';
import styles from './AuthForm.module.css';

export function SignupForm({ onSuccess, onSwitchTab }) {
  const { signup, loading, error, clearError } = useAuth();
  const [fields, setFields] = useState({ name: '', email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [showPw, setShowPw] = useState(false);

  const strength = getPasswordStrength(fields.password);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFields(f => ({ ...f, [name]: value }));
    if (errors[name]) setErrors(e => ({ ...e, [name]: null }));
    clearError();
  };

  const validate = () => {
    const errs = {};
    const nameErr  = validateName(fields.name);
    const emailErr = validateEmail(fields.email);
    const pwErr    = validatePassword(fields.password);
    if (nameErr)  errs.name = nameErr;
    if (emailErr) errs.email = emailErr;
    if (pwErr)    errs.password = pwErr;
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    const result = await signup({ name: fields.name, email: fields.email, password: fields.password });
    if (result.success) onSuccess();
  };

  return (
    <form onSubmit={handleSubmit} noValidate className={styles.form}>
      {error && (
        <div className={styles.globalError} role="alert">
          <span aria-hidden="true">⚠️</span> {error}
        </div>
      )}

      <Input
        label="Full name"
        type="text"
        name="name"
        id="signup-name"
        value={fields.name}
        onChange={handleChange}
        error={errors.name}
        autoComplete="name"
        enterKeyHint="next"
        placeholder="Alex Johnson"
        leftIcon="👤"
        required
      />

      <Input
        label="Email address"
        type="email"
        name="email"
        id="signup-email"
        value={fields.email}
        onChange={handleChange}
        error={errors.email}
        autoComplete="username"
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        enterKeyHint="next"
        placeholder="you@example.com"
        leftIcon="✉️"
        required
      />

      <div>
        <Input
          label="Password"
          type={showPw ? 'text' : 'password'}
          name="password"
          id="signup-password"
          value={fields.password}
          onChange={handleChange}
          error={errors.password}
          autoComplete="new-password"
          enterKeyHint="done"
          placeholder="Min. 8 chars, 1 uppercase, 1 number"
          leftIcon="🔒"
          rightElement={
            <button
              type="button"
              className={styles.showPwBtn}
              onClick={() => setShowPw(s => !s)}
              aria-label={showPw ? 'Hide password' : 'Show password'}
            >
              {showPw ? '🙈' : '👁️'}
            </button>
          }
          required
        />
        {/* Password strength bar */}
        {fields.password && (
          <div className={styles.strengthWrap} aria-live="polite">
            <div className={styles.strengthBar}>
              {[1, 2, 3, 4].map(lvl => (
                <div
                  key={lvl}
                  className={styles.strengthSegment}
                  style={{
                    background: strength.score >= lvl ? strength.color : 'var(--border-subtle)',
                  }}
                />
              ))}
            </div>
            <span className={styles.strengthLabel} style={{ color: strength.color }}>
              {strength.label}
            </span>
          </div>
        )}
      </div>

      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={loading}
      >
        Create Account
      </Button>

      <p className={styles.switchText}>
        Already have an account?{' '}
        <button type="button" className={styles.switchBtn} onClick={onSwitchTab}>
          Sign in
        </button>
      </p>
    </form>
  );
}
