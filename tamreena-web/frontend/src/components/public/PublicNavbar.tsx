import { useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';
import Logo from '../ui/Logo';
import PreferenceToggles from '../ui/PreferenceToggles';
import { useTranslation } from '../../lib/i18n';

export default function PublicNavbar() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { t } = useTranslation();

  const navLinks = [
    { to: '/', labelKey: 'nav.home', end: true },
    { to: '/about', labelKey: 'nav.about', end: false },
    { to: '/pricing', labelKey: 'nav.pricing', end: false },
  ];

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: 'var(--bg-glass)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <div
        style={{
          maxWidth: '1240px',
          margin: '0 auto',
          padding: '0 clamp(16px, 3vw, 24px)',
          height: '72px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo with Profile Picture */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
          }}
        >
          <div style={{ flexShrink: 0 }}>
            <Logo size={42} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span
                style={{
                  fontSize: 'clamp(17px, 3vw, 20px)',
                  fontWeight: 700,
                  fontFamily: 'var(--font-display)',
                  letterSpacing: '-0.01em',
                  color: 'var(--text-heading)',
                }}
              >
                Tamrena<span style={{ color: 'var(--accent-primary)' }}>-AI</span>
              </span>
              <span className="badge badge-primary brand-tag" style={{ padding: '2px 8px', fontSize: '9px' }}>
                {t('nav.brandTag')}
              </span>
            </div>
            <p className="brand-subtitle" style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0, fontWeight: 600 }}>
              {t('nav.brandSubtitle')}
            </p>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
          className="desktop-nav"
        >
          {navLinks.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-pill-link ${isActive ? 'active' : ''}`}
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
        </nav>

        {/* Desktop Action / Auth Buttons */}
        <div className="desktop-actions" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <PreferenceToggles />
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-strong)',
                  borderRadius: '9999px',
                }}
              >
                <div
                  style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: 'var(--accent-primary)',
                    color: 'var(--text-on-accent)',
                    fontSize: '12px',
                    fontWeight: 800,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {user.username ? user.username[0].toUpperCase() : 'A'}
                </div>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)' }}>
                  {user.username || t('sidebar.athlete')}
                </span>
              </div>
              <button
                onClick={() => navigate('/dashboard')}
                className="btn btn-primary"
                style={{ padding: '8px 18px', fontSize: '13px' }}
              >
                <span>{t('nav.enterGymCommand')}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7"></path>
                </svg>
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Link
                to="/signin"
                className="btn btn-secondary"
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                {t('nav.signIn')}
              </Link>
              <Link
                to="/signin"
                className="btn btn-primary"
                style={{ padding: '8px 18px', fontSize: '13px' }}
              >
                <span>{t('nav.getStartedFree')}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7"></path>
                </svg>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Menu Toggle Button */}
        <button
          type="button"
          aria-label="Toggle navigation menu"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{
            display: 'none',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-strong)',
            borderRadius: '8px',
            padding: '8px',
            color: 'var(--text-heading)',
            cursor: 'pointer',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          className="mobile-menu-btn"
        >
          {mobileMenuOpen ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          )}
        </button>
      </div>

      {/* Mobile Dropdown Drawer Menu */}
      {mobileMenuOpen && (
        <div
          style={{
            borderTop: '1px solid var(--border)',
            backgroundColor: 'var(--bg-page)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            padding: '16px 20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.8)',
          }}
        >
          {navLinks.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileMenuOpen(false)}
              style={({ isActive }) => ({
                padding: '12px 16px',
                borderRadius: '10px',
                textDecoration: 'none',
                fontSize: '15px',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? 'var(--accent-primary)' : 'var(--text-body)',
                backgroundColor: isActive ? 'var(--accent-primary-muted)' : 'transparent',
                border: isActive ? '1px solid var(--accent-primary)' : '1px solid transparent',
                transition: 'all 0.2s ease',
              })}
            >
              {t(item.labelKey)}
            </NavLink>
          ))}

          <div style={{ marginTop: '12px', paddingTop: '14px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <PreferenceToggles />
            {user ? (
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate('/dashboard');
                }}
                className="btn btn-primary"
                style={{ width: '100%', padding: '12px', fontSize: '14px' }}
              >
                <span>{t('nav.enterGymCommand')} ({user.username})</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7"></path>
                </svg>
              </button>
            ) : (
              <>
                <Link
                  to="/signin"
                  onClick={() => setMobileMenuOpen(false)}
                  className="btn btn-secondary"
                  style={{ width: '100%', padding: '12px', fontSize: '14px', textAlign: 'center' }}
                >
                  Sign In
                </Link>
                <Link
                  to="/signin"
                  onClick={() => setMobileMenuOpen(false)}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '12px', fontSize: '14px', textAlign: 'center' }}
                >
                  <span>{t('nav.getStartedFree')}</span>
                </Link>
              </>
            )}
          </div>
        </div>
      )}

      {/* Responsive CSS Media Queries */}
      <style>{`
        @media (max-width: 860px) {
          .desktop-nav {
            display: none !important;
          }
          .desktop-actions {
            display: none !important;
          }
          .mobile-menu-btn {
            display: flex !important;
          }
        }
        @media (max-width: 480px) {
          .brand-tag, .brand-subtitle {
            display: none !important;
          }
        }
      `}</style>
    </header>
  );
}
