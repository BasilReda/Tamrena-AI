import { Outlet } from 'react-router-dom';
import PublicNavbar from './PublicNavbar';
import PublicFooter from './PublicFooter';

export default function PublicLayout() {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-dark)',
        color: 'var(--text-primary)',
        position: 'relative',
        overflowX: 'hidden',
      }}
    >
      {/* Background Ambient Glow Elements */}
      <div
        style={{
          position: 'fixed',
          top: '-15%',
          left: '10%',
          width: '700px',
          height: '700px',
          background: 'radial-gradient(circle, var(--accent-primary-glow) 0%, rgba(0, 0, 0, 0) 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />
      <div
        style={{
          position: 'fixed',
          bottom: '5%',
          right: '5%',
          width: '800px',
          height: '800px',
          background: 'radial-gradient(circle, color-mix(in srgb, var(--category-motion) 8%, transparent) 0%, rgba(0, 0, 0, 0) 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Sticky Navbar */}
      <PublicNavbar />

      {/* Main Content Area */}
      <main style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        <Outlet />
      </main>

      {/* Footer */}
      <PublicFooter />
    </div>
  );
}
