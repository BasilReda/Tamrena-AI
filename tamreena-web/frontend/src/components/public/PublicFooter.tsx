import { Link } from 'react-router-dom';
import Logo from '../ui/Logo';
import { useTranslation } from '../../lib/i18n';

export default function PublicFooter() {
  const { t } = useTranslation();

  return (
    <footer
      style={{
        backgroundColor: 'var(--bg-page)',
        borderTop: '1px solid var(--border)',
        position: 'relative',
        zIndex: 10,
        paddingTop: '64px',
        paddingBottom: '40px',
      }}
    >
      <div
        style={{
          maxWidth: '1240px',
          margin: '0 auto',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '40px',
            marginBottom: '48px',
          }}
        >
          {/* Column 1: Brand & Status */}
          <div style={{ maxWidth: '340px' }}>
            <Link
              to="/"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                textDecoration: 'none',
                marginBottom: '16px',
              }}
            >
              <Logo size={42} />
              <span style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-heading)' }}>
                Tamrena<span style={{ color: 'var(--accent-primary)' }}>-AI</span>
              </span>
            </Link>

            <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.6, marginBottom: '20px' }}>
              {t('footer.description')}
            </p>

            {/* Live System Status Pill */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: '9999px',
                background: 'var(--accent-primary-muted)',
                border: '1px solid color-mix(in srgb, var(--accent-primary) 35%, transparent)',
                fontSize: '12px',
                color: 'var(--accent-primary)',
                fontWeight: 700,
                boxShadow: '0 0 12px var(--accent-primary-glow)',
              }}
            >
              <span
                style={{
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-primary)',
                  boxShadow: '0 0 8px var(--accent-primary)',
                }}
              />
              {t('footer.systemsOperational')}
            </div>
          </div>

          {/* Column 2: Core Platform Modules */}
          <div>
            <h4 style={{ color: 'var(--text-heading)', fontSize: '14px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              {t('footer.platformModules')}
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <li>
                <Link to="/workout" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px', transition: 'color 0.2s' }}>
                  {t('footer.workoutStudioLink')}
                </Link>
              </li>
              <li>
                <Link to="/exercises" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.cvCoachLink')}
                </Link>
              </li>
              <li>
                <Link to="/nutrition" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.nutritionLink')}
                </Link>
              </li>
              <li>
                <Link to="/progress" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.inbodyLink')}
                </Link>
              </li>
              <li>
                <Link to="/dashboard" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.commandCenterLink')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Company & Science */}
          <div>
            <h4 style={{ color: 'var(--text-heading)', fontSize: '14px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              {t('footer.companyScience')}
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <li>
                <Link to="/about" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.aboutLink')}
                </Link>
              </li>
              <li>
                <Link to="/about" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.scienceLink')}
                </Link>
              </li>
              <li>
                <Link to="/pricing" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.plansLink')}
                </Link>
              </li>
              <li>
                <Link to="/signin" style={{ color: 'var(--text-body)', textDecoration: 'none', fontSize: '13px' }}>
                  {t('footer.createAccountLink')}
                </Link>
              </li>
              <li>
                <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                  {t('footer.location')}
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div
          style={{
            paddingTop: '28px',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <p style={{ color: 'var(--text-muted)', fontSize: '12px', margin: 0 }}>
            © {new Date().getFullYear()} {t('footer.rights')}
          </p>
          <div style={{ display: 'flex', gap: '20px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              {t('footer.wcag')}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              {t('footer.jwt')}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              {t('footer.stack')}
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
