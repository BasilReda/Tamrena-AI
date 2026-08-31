import { useLocation } from 'react-router-dom';
import PreferenceToggles from '../ui/PreferenceToggles';
import { useTranslation } from '../../lib/i18n';

function getHeaderTitleKeys(pathname: string): { titleKey: string; subtitleKey: string } {
  if (pathname === '/dashboard' || pathname === '/') return { titleKey: 'header.title.dashboard', subtitleKey: 'header.subtitle.dashboard' };
  if (pathname.startsWith('/workout')) return { titleKey: 'header.title.workout', subtitleKey: 'header.subtitle.workout' };
  if (pathname.startsWith('/nutrition')) return { titleKey: 'header.title.nutrition', subtitleKey: 'header.subtitle.nutrition' };
  if (pathname.startsWith('/progress')) return { titleKey: 'header.title.progress', subtitleKey: 'header.subtitle.progress' };
  if (pathname.startsWith('/exercises')) return { titleKey: 'header.title.exercises', subtitleKey: 'header.subtitle.exercises' };
  if (pathname.startsWith('/coach')) return { titleKey: 'header.title.coach', subtitleKey: 'header.subtitle.coach' };
  return { titleKey: 'header.title.default', subtitleKey: 'header.subtitle.default' };
}

interface HeaderProps {
  onToggleSidebar?: () => void;
}

function Header({ onToggleSidebar }: HeaderProps) {
  const location = useLocation();
  const { titleKey, subtitleKey } = getHeaderTitleKeys(location.pathname);
  const { t } = useTranslation();

  return (
    <header
      style={{
        height: '70px',
        padding: '0 clamp(16px, 3vw, 32px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--bg-glass)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 30,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Mobile Hamburger Button */}
        {onToggleSidebar && (
          <button
            type="button"
            aria-label="Toggle navigation menu"
            onClick={onToggleSidebar}
            className="mobile-header-menu-btn"
            style={{
              display: 'none',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-strong)',
              borderRadius: '8px',
              padding: '8px',
              color: 'var(--text-heading)',
              cursor: 'pointer',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
        )}

        <div>
          <h1 style={{ fontSize: 'clamp(16px, 2.5vw, 18px)', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-heading)', margin: 0, letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {t(titleKey)}
          </h1>
          <p className="header-subtitle" style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            {t(subtitleKey)}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Streak Pill */}
        <div
          className="header-streak-pill"
          style={{
            background: 'color-mix(in srgb, var(--category-motion) 15%, transparent)',
            border: '1px solid color-mix(in srgb, var(--category-motion) 35%, transparent)',
            borderRadius: '9999px',
            padding: '4px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 700,
            color: 'var(--category-motion)',
          }}
        >
          <span>🔥</span>
          <span className="streak-text">5 {t('header.streak')}</span>
        </div>

        {/* AI System Status */}
        <div
          className="header-status-pill"
          style={{
            background: 'var(--accent-primary-muted)',
            border: '1px solid color-mix(in srgb, var(--accent-primary) 40%, transparent)',
            borderRadius: '9999px',
            padding: '4px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 700,
            color: 'var(--category-nutrition)',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent-primary)',
              boxShadow: '0 0 8px var(--accent-primary)',
            }}
          />
          <span className="status-text">{t('header.aiOnline')}</span>
        </div>

        <PreferenceToggles />
      </div>

      <style>{`
        @media (max-width: 860px) {
          .mobile-header-menu-btn {
            display: flex !important;
          }
        }
        @media (max-width: 540px) {
          .header-subtitle {
            display: none !important;
          }
          .streak-text, .status-text {
            display: none !important;
          }
          .header-streak-pill, .header-status-pill {
            padding: 6px !important;
          }
        }
      `}</style>
    </header>
  );
}

export default Header;
