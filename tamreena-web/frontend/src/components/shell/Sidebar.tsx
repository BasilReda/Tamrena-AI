import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';
import { clearToken } from '../../lib/api';
import Logo from '../ui/Logo';
import PreferenceToggles from '../ui/PreferenceToggles';
import { useTranslation } from '../../lib/i18n';

const MAIN_NAV = [
  {
    to: '/dashboard',
    labelKey: 'sidebar.commandCenter',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5"></rect>
        <rect x="14" y="3" width="7" height="7" rx="1.5"></rect>
        <rect x="14" y="14" width="7" height="7" rx="1.5"></rect>
        <rect x="3" y="14" width="7" height="7" rx="1.5"></rect>
      </svg>
    ),
  },
  {
    to: '/workout',
    labelKey: 'sidebar.workoutStudio',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <path d="M12 18v-6"></path>
        <path d="m9 15 3 3 3-3"></path>
      </svg>
    ),
  },
  {
    to: '/nutrition',
    labelKey: 'sidebar.nutritionMacros',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v20"></path>
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
      </svg>
    ),
  },
  {
    to: '/progress',
    labelKey: 'sidebar.progressInbody',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
      </svg>
    ),
  },
  {
    to: '/exercises',
    labelKey: 'sidebar.exerciseCoach',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.934a.5.5 0 0 0-.777-.416L16 11"></path>
        <rect x="2" y="6" width="14" height="12" rx="2"></rect>
      </svg>
    ),
  },
  {
    to: '/coach',
    labelKey: 'sidebar.coachChat',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
      </svg>
    ),
  },
];

const RESOURCE_NAV = [
  { to: '/', labelKey: 'sidebar.landingPage' },
  { to: '/about', labelKey: 'sidebar.aboutTamrena' },
  { to: '/pricing', labelKey: 'sidebar.pricingPlans' },
];

interface SidebarProps {
  isMobileOpen?: boolean;
  onClose?: () => void;
}

function Sidebar({ isMobileOpen = false, onClose }: SidebarProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleNavClick = () => {
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(11, 15, 26, 0.8)',
            backdropFilter: 'blur(8px)',
            zIndex: 49,
            transition: 'opacity 0.2s ease',
          }}
          className="mobile-sidebar-backdrop"
        />
      )}

      <aside
        className={`app-sidebar ${isMobileOpen ? 'mobile-open' : ''}`}
        style={{
          width: '260px',
          minWidth: '260px',
          backgroundColor: 'var(--bg-card)',
          backdropFilter: 'blur(20px)',
          borderRight: '1px solid var(--border)',
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          height: '100vh',
          boxSizing: 'border-box',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <div style={{ overflowY: 'auto', paddingRight: '4px' }}>
          {/* Brand Header with Logo Image */}
          <div style={{ padding: '0 8px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Link to="/" onClick={handleNavClick} style={{ textDecoration: 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Logo size={42} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-display)', letterSpacing: '-0.01em', color: 'var(--text-heading)' }}>
                      Tamrena<span style={{ color: 'var(--accent-primary)' }}>-AI</span>
                    </span>
                    <span className="badge badge-primary" style={{ padding: '2px 6px', fontSize: '10px' }}>{t('sidebar.pro')}</span>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '1px' }}>{t('sidebar.tagline')}</p>
                </div>
              </div>
            </Link>

            {/* Mobile Close Button */}
            {onClose && (
              <button
                type="button"
                aria-label="Close sidebar"
                onClick={onClose}
                className="mobile-sidebar-close"
                style={{
                  display: 'none',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-strong)',
                  color: 'var(--text-body)',
                  borderRadius: '8px',
                  padding: '6px',
                  cursor: 'pointer',
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            )}
          </div>

          {/* Quick Workout CTA */}
          <div style={{ padding: '0 4px', marginBottom: '20px' }}>
            <button
              onClick={() => {
                handleNavClick();
                navigate('/intake');
              }}
              className="btn btn-primary"
              style={{ width: '100%', gap: '8px', padding: '12px', fontSize: '13px', borderRadius: '10px' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 5v14M5 12h14"></path>
              </svg>
              {t('sidebar.generateRoutine')}
            </button>
          </div>

          {/* Main App Navigation List */}
          <div style={{ marginBottom: '20px' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 12px 6px', display: 'block' }}>
              {t('sidebar.athleteCore')}
            </span>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {MAIN_NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={handleNavClick}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    textDecoration: 'none',
                    fontSize: '13.5px',
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? 'var(--accent-primary)' : 'var(--text-body)',
                    backgroundColor: isActive ? 'var(--accent-primary-muted)' : 'transparent',
                    border: isActive ? '1px solid color-mix(in srgb, var(--accent-primary) 40%, transparent)' : '1px solid transparent',
                    boxShadow: isActive ? '0 0 12px var(--accent-primary-glow)' : 'none',
                    transition: 'all 0.2s ease',
                  })}
                >
                  {item.icon}
                  <span>{t(item.labelKey)}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Public Resources & PRD Nav */}
          <div style={{ marginBottom: '16px' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 12px 6px', display: 'block' }}>
              {t('sidebar.publicArchitecture')}
            </span>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {RESOURCE_NAV.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={handleNavClick}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    fontSize: '12px',
                    fontWeight: 500,
                    color: 'var(--text-muted)',
                    transition: 'color 0.2s',
                  }}
                >
                  <span style={{ color: 'var(--accent-primary)', fontSize: '10px' }}>↗</span>
                  <span>{t(item.labelKey)}</span>
                </Link>
              ))}
            </nav>
          </div>
        </div>

        {/* User Profile Card */}
        <div
          style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '15px',
                color: 'var(--text-on-accent)',
                boxShadow: '0 0 10px var(--accent-primary-glow)',
              }}
            >
              {user?.username ? user.username[0].toUpperCase() : 'A'}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <p style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)', margin: 0, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.username || t('sidebar.athlete')}
              </p>
              <span style={{ fontSize: '11px', color: 'var(--accent-primary)', fontWeight: 700 }}>{t('sidebar.activeGymPro')}</span>
            </div>
          </div>
          <button
            id="sign-out-btn"
            onClick={() => {
              clearToken();
              window.location.href = '/signin';
            }}
            title={t('sidebar.signOut')}
            style={{
              background: 'color-mix(in srgb, var(--status-error) 12%, transparent)',
              border: '1px solid color-mix(in srgb, var(--status-error) 30%, transparent)',
              color: 'var(--status-error)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </aside>

      <style>{`
        @media (max-width: 860px) {
          .app-sidebar {
            position: fixed !important;
            top: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            transform: translateX(-100%) !important;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.8) !important;
          }
          .app-sidebar.mobile-open {
            transform: translateX(0) !important;
          }
          .mobile-sidebar-close {
            display: flex !important;
          }
        }
      `}</style>
    </>
  );
}

export default Sidebar;
