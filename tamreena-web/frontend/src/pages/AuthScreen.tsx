import { useState, type FormEvent } from 'react';
import { saveToken, signUp, logIn } from '../lib/api';
import Logo from '../components/ui/Logo';
import PreferenceToggles from '../components/ui/PreferenceToggles';
import { useTranslation } from '../lib/i18n';

type Mode = 'signin' | 'signup';

interface AuthScreenProps {
  onSignedIn: () => void;
}

function AuthScreen({ onSignedIn }: AuthScreenProps) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<Mode>('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const session =
        mode === 'signin' ? await logIn(username, password) : await signUp(username, password, confirmPassword);
      saveToken(session.access_token);
      onSignedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${mode === 'signin' ? 'Sign in' : 'Sign up'} failed`);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleMode = () => {
    setMode((m) => (m === 'signin' ? 'signup' : 'signin'));
    setError(null);
    setPassword('');
    setConfirmPassword('');
  };

  return (
    <div
      className="auth-screen-container"
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-page)',
        display: 'flex',
        alignItems: 'stretch',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Left Feature Showcase Banner (hidden on mobile) */}
      <div
        className="auth-left-banner"
        style={{
          flex: 1,
          background: 'linear-gradient(135deg, var(--bg-card) 0%, var(--bg-page) 100%)',
          borderRight: '1px solid var(--border)',
          padding: 'clamp(32px, 5vw, 60px)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '-20%',
            left: '-10%',
            width: '600px',
            height: '600px',
            background: 'radial-gradient(circle, var(--accent-primary-glow) 0%, rgba(0, 0, 0, 0) 70%)',
            pointerEvents: 'none',
          }}
        />

        {/* Brand Top + preference toggles */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <Logo size={52} />
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-heading)', margin: 0, letterSpacing: '-0.01em' }}>
              Tamrena<span style={{ color: 'var(--accent-primary)' }}>-AI</span>
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>{t('auth.brand.subtitle')}</p>
          </div>
        </div>
        <PreferenceToggles />
        </div>

        {/* Hero Copy */}
        <div style={{ zIndex: 1, maxWidth: '520px', margin: '40px 0' }}>
          <span className="badge badge-primary" style={{ marginBottom: '16px' }}>
            {t('auth.hero.badge')}
          </span>
          <h1 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 800, lineHeight: 1.15, color: 'var(--text-heading)', marginBottom: '20px' }}>
            {t('auth.hero.title')} <span className="gradient-text-emerald">{t('auth.hero.titleHighlight')}</span>.
          </h1>
          <p style={{ fontSize: '15px', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '32px' }}>
            {t('auth.hero.body')}
          </p>

          {/* Feature Grid with Semantic Category Colors */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            <div className="glass-panel" style={{ padding: '16px', background: 'var(--bg-input)', border: '1px solid color-mix(in srgb, var(--category-nutrition) 30%, transparent)' }}>
              <div style={{ color: 'var(--category-nutrition)', marginBottom: '6px', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                {t('auth.feature.nutrition')}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('auth.feature.nutrition.body')}</p>
            </div>
            <div className="glass-panel" style={{ padding: '16px', background: 'var(--bg-input)', border: '1px solid color-mix(in srgb, var(--category-data) 30%, transparent)' }}>
              <div style={{ color: 'var(--category-data)', marginBottom: '6px', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                {t('auth.feature.inbody')}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('auth.feature.inbody.body')}</p>
            </div>
            <div className="glass-panel" style={{ padding: '16px', background: 'var(--bg-input)', border: '1px solid color-mix(in srgb, var(--category-motion) 30%, transparent)' }}>
              <div style={{ color: 'var(--category-motion)', marginBottom: '6px', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
                {t('auth.feature.cv')}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('auth.feature.cv.body')}</p>
            </div>
            <div className="glass-panel" style={{ padding: '16px', background: 'var(--bg-input)', border: '1px solid color-mix(in srgb, var(--category-ai) 30%, transparent)' }}>
              <div style={{ color: 'var(--category-ai)', marginBottom: '6px', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path></svg>
                {t('auth.feature.ai')}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('auth.feature.ai.body')}</p>
            </div>
          </div>
        </div>

        {/* Footer Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', zIndex: 1 }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t('auth.footer.trust')}</span>
        </div>
      </div>

      {/* Right Auth Card Form */}
      <div
        className="auth-right-form-wrapper"
        style={{
          width: '520px',
          minWidth: '320px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 'clamp(20px, 4vw, 40px)',
          backgroundColor: 'var(--bg-page)',
        }}
      >
        <div className="glass-panel" style={{ width: '100%', maxWidth: '440px', padding: 'clamp(24px, 5vw, 40px)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          {/* Mobile-Only Top Brand Logo */}
          <div className="mobile-auth-logo" style={{ display: 'none', justifyContent: 'center', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Logo size={42} />
            <span style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-heading)' }}>
              Tamrena<span style={{ color: 'var(--accent-primary)' }}>-AI</span>
            </span>
          </div>

          {/* Header */}
          <div style={{ marginBottom: '24px', textAlign: 'center' }}>
            <h2 style={{ fontSize: '22px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-heading)', marginBottom: '6px' }}>
              {mode === 'signin' ? t('auth.form.welcomeBack') : t('auth.form.createAccount')}
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-body)', margin: 0 }}>
              {mode === 'signin' ? t('auth.form.signInSubtitle') : t('auth.form.signUpSubtitle')}
            </p>
          </div>

          {/* Tab Mode Selector */}
          <div
            style={{
              display: 'flex',
              background: 'var(--bg-input)',
              borderRadius: '10px',
              padding: '4px',
              marginBottom: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <button
              type="button"
              onClick={() => { setMode('signin'); setError(null); }}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 800,
                border: 'none',
                cursor: 'pointer',
                background: mode === 'signin' ? 'var(--accent-primary)' : 'transparent',
                color: mode === 'signin' ? 'var(--text-on-accent)' : 'var(--text-body)',
                boxShadow: mode === 'signin' ? '0 0 14px var(--accent-primary-glow)' : 'none',
                transition: 'all 0.2s ease',
              }}
            >
              {t('auth.form.signIn')}
            </button>
            <button
              type="button"
              onClick={() => { setMode('signup'); setError(null); }}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 800,
                border: 'none',
                cursor: 'pointer',
                background: mode === 'signup' ? 'var(--accent-primary)' : 'transparent',
                color: mode === 'signup' ? 'var(--text-on-accent)' : 'var(--text-body)',
                boxShadow: mode === 'signup' ? '0 0 14px var(--accent-primary-glow)' : 'none',
                transition: 'all 0.2s ease',
              }}
            >
              {t('auth.form.register')}
            </button>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="username-input">{t('auth.form.username')}</label>
              <input
                id="username-input"
                type="text"
                placeholder={t('auth.form.usernamePlaceholder')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="password-input">{t('auth.form.password')}</label>
              <input
                id="password-input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
                required
                minLength={8}
              />
            </div>

            {mode === 'signup' && (
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" htmlFor="confirm-password-input">{t('auth.form.confirmPassword')}</label>
                <input
                  id="confirm-password-input"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="form-input"
                  required
                  minLength={8}
                />
              </div>
            )}

            {error && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '8px',
                  padding: '12px',
                  color: 'var(--status-error)',
                  fontSize: '13px',
                }}
              >
                ⚠️ {error}
              </div>
            )}

            <button
              id="submit-btn"
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
              style={{ width: '100%', height: '46px', fontSize: '15px', marginTop: '8px' }}
            >
              {submitting
                ? t('auth.form.authenticating')
                : mode === 'signin'
                  ? t('auth.form.submitSignIn')
                  : t('auth.form.submitSignUp')}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <button
              id="toggle-mode-btn"
              type="button"
              onClick={toggleMode}
              style={{
                fontSize: '13px',
                color: 'var(--accent-primary)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 700,
              }}
            >
              {mode === 'signin' ? t('auth.form.noAccount') : t('auth.form.haveAccount')}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 860px) {
          .auth-left-banner {
            display: none !important;
          }
          .auth-right-form-wrapper {
            width: 100% !important;
            flex: 1 !important;
          }
          .mobile-auth-logo {
            display: flex !important;
          }
        }
      `}</style>
    </div>
  );
}

export default AuthScreen;
