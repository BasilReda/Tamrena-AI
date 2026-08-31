import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';
import PoseVisualizerDemo from '../../components/public/PoseVisualizerDemo';
import LangGraphPipelineDemo from '../../components/public/LangGraphPipelineDemo';
import Logo from '../../components/ui/Logo';
import { useTranslation } from '../../lib/i18n';

export default function LandingHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t, language } = useTranslation();

  return (
    <div style={{ position: 'relative' }}>
      {/* 1. HERO SECTION */}
      <section
        className="public-section"
        style={{
          paddingTop: 'clamp(36px, 5vw, 60px)',
          paddingBottom: 'clamp(40px, 6vw, 80px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Ambient Top Glow */}
        <div
          style={{
            position: 'absolute',
            top: '0',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 'min(700px, 95vw)',
            height: '450px',
            background: 'radial-gradient(ellipse, var(--accent-primary-glow) 0%, color-mix(in srgb, var(--category-data) 8%, transparent) 45%, rgba(0,0,0,0) 80%)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />

        {/* Hero Logo Emblem - Prominent Center Branding */}
        <div
          style={{
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            zIndex: 1,
            filter: 'drop-shadow(0 0 40px var(--accent-primary-glow))',
          }}
        >
          <Logo size={110} />
        </div>

        {/* Announcement Pill */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '9999px',
            background: 'var(--accent-primary-muted)',
            border: '1px solid color-mix(in srgb, var(--accent-primary) 40%, transparent)',
            marginBottom: '18px',
            boxShadow: '0 0 20px var(--accent-primary-glow)',
            maxWidth: '100%',
          }}
        >
          <span style={{ fontSize: '13px' }}>⚡</span>
          <span style={{ fontSize: 'clamp(10px, 2.2vw, 13px)', fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            {t('landing.hero.eyebrow')}
          </span>
        </div>

        {/* Hero Title */}
        <h1
          style={{
            fontSize: 'clamp(28px, 6vw, 64px)',
            fontWeight: 700,
            lineHeight: 1.12,
            letterSpacing: '-0.03em',
            color: 'var(--text-heading)',
            maxWidth: '1000px',
            marginBottom: '20px',
          }}
        >
          {t('landing.hero.title1')}{' '}
          <span style={{ color: 'var(--category-motion)' }}>{t('landing.hero.title2')}</span>{' '}
          <span className="gradient-text-emerald">{t('landing.hero.title3')}</span>
        </h1>

        {/* Hero Subtitle */}
        <p
          style={{
            fontSize: 'clamp(14px, 2vw, 18px)',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            maxWidth: '780px',
            marginBottom: '32px',
          }}
        >
          {t('landing.hero.subtitle.pre')} <strong style={{ color: 'var(--text-heading)' }}>{t('landing.hero.subtitle.strong1')}</strong>,{' '}
          <strong style={{ color: 'var(--category-motion)' }}>{t('landing.hero.subtitle.strong2')}</strong>
          {language === 'ar' ? '، و' : ', and a '}
          <strong style={{ color: 'var(--category-nutrition)' }}>{t('landing.hero.subtitle.strong3')}</strong> {t('landing.hero.subtitle.post')}
        </p>

        {/* Hero Action Buttons */}
        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '40px', width: '100%', maxWidth: '500px' }}>
          {user ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="btn btn-primary"
              style={{ padding: '14px 32px', fontSize: '15px', borderRadius: '10px', flex: '1 1 auto', justifyContent: 'center' }}
            >
              <span>{t('landing.hero.goToDashboard')}</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
            </button>
          ) : (
            <>
              <Link
                to="/signin"
                className="btn btn-primary"
                style={{ padding: '14px 28px', fontSize: '15px', borderRadius: '10px', flex: '1 1 auto', justifyContent: 'center' }}
              >
                <span>{t('landing.hero.startFree')}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7"></path>
                </svg>
              </Link>
              <Link
                to="/about"
                className="btn btn-secondary"
                style={{ padding: '14px 24px', fontSize: '15px', borderRadius: '10px', flex: '1 1 auto', justifyContent: 'center' }}
              >
                <span>{t('landing.hero.learnMore')}</span>
              </Link>
            </>
          )}
        </div>

        {/* Live System Telemetry Strip using Category Colors */}
        <div
          className="glass-panel"
          style={{
            width: '100%',
            maxWidth: '960px',
            padding: 'clamp(14px, 3vw, 20px) clamp(16px, 4vw, 28px)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))',
            gap: '16px',
            fontSize: '13px',
            background: 'var(--bg-card)',
            borderColor: 'var(--border)',
          }}
        >
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
              {t('landing.stat.microservices.label')}
            </span>
            <strong style={{ color: 'var(--category-data)', fontFamily: 'var(--font-mono)' }}>{t('landing.stat.microservices.value')}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
              {t('landing.stat.cvStream.label')}
            </span>
            <strong style={{ color: 'var(--category-motion)', fontFamily: 'var(--font-mono)' }}>{t('landing.stat.cvStream.value')}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
              {t('landing.stat.nutrition.label')}
            </span>
            <strong style={{ color: 'var(--category-nutrition)', fontFamily: 'var(--font-mono)' }}>{t('landing.stat.nutrition.value')}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
              {t('landing.stat.aiReasoning.label')}
            </span>
            <strong style={{ color: 'var(--category-ai)', fontFamily: 'var(--font-mono)' }}>{t('landing.stat.aiReasoning.value')}</strong>
          </div>
        </div>
      </section>

      {/* 2. LIVE INTERACTIVE CV POSE TRACKER DEMO PREVIEW */}
      <section className="public-section" style={{ paddingTop: '0' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span className="badge badge-amber" style={{ marginBottom: '12px' }}>
            {t('landing.demo.badge')}
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            {t('landing.demo.title')}
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '640px', margin: '8px auto 0' }}>
            {t('landing.demo.subtitle')}
          </p>
        </div>

        <PoseVisualizerDemo />
      </section>

      {/* 3. THREE CORE PILLARS SECTION */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            {t('landing.pillars.badge')}
          </span>
          <h2 style={{ fontSize: 'clamp(26px, 4vw, 40px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            {t('landing.pillars.title')}
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '680px', margin: '10px auto 0' }}>
            {t('landing.pillars.subtitle')}
          </p>
        </div>

        <div className="three-pillars-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
          {/* Pillar 1: AI Workout & Hunter Protocol (AI Category: Purple #A78BFA) */}
          <div
            className="glass-panel"
            style={{
              padding: 'clamp(24px, 4vw, 36px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-page)',
              borderColor: 'color-mix(in srgb, var(--category-ai) 25%, transparent)',
            }}
          >
            <div>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '14px',
                  background: 'color-mix(in srgb, var(--category-ai) 15%, transparent)',
                  border: '1px solid color-mix(in srgb, var(--category-ai) 40%, transparent)',
                  color: 'var(--category-ai)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  boxShadow: '0 0 15px color-mix(in srgb, var(--category-ai) 25%, transparent)',
                }}
              >
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
              </div>

              <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '12px' }}>
                {t('landing.pillar1.title')}
              </h3>

              <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.6, marginBottom: '20px' }}>
                {t('landing.pillar1.body')}
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: 'var(--text-body)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-ai)' }}>✓</span> {t('landing.pillar1.li1')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-ai)' }}>✓</span> {t('landing.pillar1.li2')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-ai)' }}>✓</span> {t('landing.pillar1.li3')}
                </li>
              </ul>
            </div>

            <Link
              to="/about"
              style={{
                color: 'var(--category-ai)',
                fontSize: '14px',
                fontWeight: 700,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {t('landing.pillar1.cta')}
            </Link>
          </div>

          {/* Pillar 2: Computer Vision Real-Time Coaching (Motion Category: Amber #F59E0B) */}
          <div
            className="glass-panel"
            style={{
              padding: 'clamp(24px, 4vw, 36px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-page)',
              borderColor: 'color-mix(in srgb, var(--category-motion) 25%, transparent)',
            }}
          >
            <div>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '14px',
                  background: 'color-mix(in srgb, var(--category-motion) 15%, transparent)',
                  border: '1px solid color-mix(in srgb, var(--category-motion) 40%, transparent)',
                  color: 'var(--category-motion)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  boxShadow: '0 0 15px color-mix(in srgb, var(--category-motion) 25%, transparent)',
                }}
              >
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.934a.5.5 0 0 0-.777-.416L16 11"></path>
                  <rect x="2" y="6" width="14" height="12" rx="2"></rect>
                </svg>
              </div>

              <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '12px' }}>
                {t('landing.pillar2.title')}
              </h3>

              <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.6, marginBottom: '20px' }}>
                {t('landing.pillar2.body')}
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: 'var(--text-body)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-motion)' }}>✓</span> {t('landing.pillar2.li1')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-motion)' }}>✓</span> {t('landing.pillar2.li2')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-motion)' }}>✓</span> {t('landing.pillar2.li3')}
                </li>
              </ul>
            </div>

            <Link
              to="/about"
              style={{
                color: 'var(--category-motion)',
                fontSize: '14px',
                fontWeight: 700,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {t('landing.pillar2.cta')}
            </Link>
          </div>

          {/* Pillar 3: 7-Node Egyptian Nutrition (Nutrition Category: Green #10B981) */}
          <div
            className="glass-panel"
            style={{
              padding: 'clamp(24px, 4vw, 36px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-page)',
              borderColor: 'color-mix(in srgb, var(--category-nutrition) 25%, transparent)',
            }}
          >
            <div>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '14px',
                  background: 'var(--accent-primary-muted)',
                  border: '1px solid color-mix(in srgb, var(--category-nutrition) 40%, transparent)',
                  color: 'var(--category-nutrition)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                  boxShadow: '0 0 15px var(--accent-primary-glow)',
                }}
              >
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
              </div>

              <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '12px' }}>
                {t('landing.pillar3.title')}
              </h3>

              <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.6, marginBottom: '20px' }}>
                {t('landing.pillar3.body')}
              </p>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: 'var(--text-body)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-nutrition)' }}>✓</span> {t('landing.pillar3.li1')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-nutrition)' }}>✓</span> {t('landing.pillar3.li2')}
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--category-nutrition)' }}>✓</span> {t('landing.pillar3.li3')}
                </li>
              </ul>
            </div>

            <Link
              to="/about"
              style={{
                color: 'var(--category-nutrition)',
                fontSize: '14px',
                fontWeight: 700,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {t('landing.pillar3.cta')}
            </Link>
          </div>
        </div>
      </section>

      {/* 4. WORKFLOW WALKTHROUGH */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <span className="badge badge-slate" style={{ marginBottom: '12px' }}>
            End-to-End Workflow
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            How Tamrena-AI Elevates Your Training
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '640px', margin: '8px auto 0' }}>
            From your initial intake assessment to live webcam coaching and dynamic progressive overload.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
          {/* Step 1: Data */}
          <div className="glass-panel" style={{ padding: '20px', position: 'relative', borderColor: 'color-mix(in srgb, var(--category-data) 25%, transparent)' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--category-data)', fontFamily: 'var(--font-mono)', marginBottom: '10px' }}>
              01
            </div>
            <h4 style={{ fontSize: '17px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '6px' }}>
              Intake & InBody Scan
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-body)', lineHeight: 1.5, margin: 0 }}>
              Complete the Hunter Profile with your goals, gym equipment, and upload your InBody scan sheet for OCR limb asymmetry parsing.
            </p>
          </div>

          {/* Step 2: AI & Nutrition */}
          <div className="glass-panel" style={{ padding: '20px', position: 'relative', borderColor: 'color-mix(in srgb, var(--category-ai) 25%, transparent)' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--category-ai)', fontFamily: 'var(--font-mono)', marginBottom: '10px' }}>
              02
            </div>
            <h4 style={{ fontSize: '17px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '6px' }}>
              Protocol Synthesis
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-body)', lineHeight: 1.5, margin: 0 }}>
              The Workout engine generates targeted sets, reps, and RPE progressions while the 7-node LangGraph pipeline creates your daily Egyptian meal split.
            </p>
          </div>

          {/* Step 3: Motion */}
          <div className="glass-panel" style={{ padding: '20px', position: 'relative', borderColor: 'color-mix(in srgb, var(--category-motion) 25%, transparent)' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--category-motion)', fontFamily: 'var(--font-mono)', marginBottom: '10px' }}>
              03
            </div>
            <h4 style={{ fontSize: '17px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '6px' }}>
              Live CV Form Coaching
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-body)', lineHeight: 1.5, margin: 0 }}>
              Open your webcam or upload a workout video. Receive 30 FPS skeleton tracking, joint angle verification, and real-time auditory corrective cues.
            </p>
          </div>

          {/* Step 4: Nutrition & Recovery */}
          <div className="glass-panel" style={{ padding: '20px', position: 'relative', borderColor: 'rgba(16, 185, 129, 0.25)' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--category-nutrition)', fontFamily: 'var(--font-mono)', marginBottom: '10px' }}>
              04
            </div>
            <h4 style={{ fontSize: '17px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '6px' }}>
              Adaptive Overload
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-body)', lineHeight: 1.5, margin: 0 }}>
              Session performance metrics flow back into your profile. The system recalculates volume and nutrition to ensure uninterrupted progressive overload.
            </p>
          </div>
        </div>
      </section>

      {/* 5. NUTRITION PIPELINE INTERACTIVE EMBED */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            Multi-Agent AI Architecture
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Explore the 7-Node Egyptian Nutrition Pipeline
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '650px', margin: '8px auto 0' }}>
            Click through each pipeline node to inspect agent logic, inputs, outputs, and our authentic Egyptian meal balancing algorithms.
          </p>
        </div>

        <LangGraphPipelineDemo />
      </section>

      {/* 6. ATHLETIC ACCREDITATION & REVIEWS */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            Athlete Community & Results
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Built for Serious Lifters & Health Seekers
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ color: 'var(--accent-primary)', fontSize: '16px', marginBottom: '10px' }}>★★★★★</div>
            <p style={{ fontSize: '13.5px', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '18px' }}>
              "Having the CV coach catch my knee valgus on heavy squats in real-time changed my lifting longevity. Plus, getting a meal plan with actual Egyptian food like Foul and grilled chicken instead of oatmeal was a game changer."
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'var(--accent-primary)', color: 'var(--text-on-accent)', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                K
              </div>
              <div>
                <h5 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>Karim El-Sayed</h5>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Competitive Powerlifter (Cairo)</span>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ color: 'var(--accent-primary)', fontSize: '16px', marginBottom: '10px' }}>★★★★★</div>
            <p style={{ fontSize: '13.5px', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '18px' }}>
              "The InBody scan OCR integration spotted a 14% muscular imbalance between my left and right quads. Tamrena-AI immediately shifted my unilateral volume to correct it over 8 weeks."
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'var(--category-data)', color: 'var(--text-on-accent)', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                M
              </div>
              <div>
                <h5 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>Mahmoud Tarek</h5>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Bodybuilding Athlete (Alexandria)</span>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ color: 'var(--accent-primary)', fontSize: '16px', marginBottom: '10px' }}>★★★★★</div>
            <p style={{ fontSize: '13.5px', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '18px' }}>
              "The speed and accuracy of the 4 microservices running together is incredible. I use the webcam tracker at my home gym and get trainer-quality feedback without the hourly trainer fees."
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'var(--category-ai)', color: 'var(--text-on-accent)', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                N
              </div>
              <div>
                <h5 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>Nourhan Ahmed</h5>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CrossFit & Functional Fitness</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. FINAL CONVERSION BANNER */}
      <section className="public-section" style={{ paddingBottom: '80px' }}>
        <div
          className="glass-panel"
          style={{
            padding: 'clamp(32px, 6vw, 56px) clamp(20px, 4vw, 40px)',
            textAlign: 'center',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(19, 26, 43, 0.95) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            boxShadow: '0 0 40px var(--accent-primary-glow)',
          }}
        >
          <span className="badge badge-primary" style={{ marginBottom: '16px' }}>
            Transform Your Fitness Today
          </span>
          <h2 style={{ fontSize: 'clamp(26px, 5vw, 44px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em', maxWidth: '800px', margin: '0 auto 16px' }}>
            Ready for Evidence-Based Athletic Mastery?
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '600px', margin: '0 auto 28px', lineHeight: 1.6 }}>
            Join Tamrena-AI to start your personalized InBody assessment, receive periodized workout routines, and track your form with 30 FPS Computer Vision.
          </p>

          <Link
            to="/signin"
            className="btn btn-primary"
            style={{ padding: '16px 36px', fontSize: '16px', borderRadius: '10px' }}
          >
            <span>Create Your Free Athlete Account</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7"></path>
            </svg>
          </Link>
        </div>
      </section>
    </div>
  );
}
