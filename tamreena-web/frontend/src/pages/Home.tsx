import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSessions, type WorkoutSession } from '../lib/api';
import { useTranslation } from '../lib/i18n';

function Home() {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<WorkoutSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSessions()
      .then(setSessions)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load sessions'));
  }, []);

  if (error) {
    return (
      <div
        style={{
          padding: '20px',
          borderRadius: '12px',
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: 'var(--status-error)',
          fontSize: '14px',
        }}
      >
        ⚠️ {error}
      </div>
    );
  }

  if (sessions === null) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <p style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>{t('home.loading')}</p>
      </div>
    );
  }

  const hasPlan = sessions.length > 0;
  const latest = sessions[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(20px, 4vw, 32px)' }}>
      {/* Hero Welcome Command Card */}
      <div
        className="glass-panel"
        style={{
          padding: 'clamp(20px, 4vw, 32px)',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          position: 'relative',
          overflow: 'hidden',
          borderRadius: '16px',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '-50%',
            right: '-10%',
            width: '450px',
            height: '450px',
            background: 'radial-gradient(circle, color-mix(in srgb, var(--accent-primary) 10%, transparent) 0%, rgba(0,0,0,0) 70%)',
            pointerEvents: 'none',
          }}
        />

        <div className="home-hero-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px', position: 'relative', zIndex: 1 }}>
          <div style={{ maxWidth: '640px', flex: '1 1 300px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <span className="badge badge-primary">{t('home.badge.engine')}</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t('home.badge.updatedToday')}</span>
            </div>
            <h2 style={{ fontSize: 'clamp(22px, 3.5vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0, letterSpacing: '-0.02em' }}>
              {hasPlan
                ? `${t('home.hero.protocol')} ${latest.goal ?? 'Hypertrophy & Strength'}`
                : t('home.hero.noplan')}
            </h2>
            <p style={{ color: 'var(--text-body)', fontSize: '14px', marginTop: '8px', lineHeight: 1.6 }}>
              {hasPlan
                ? `${t('home.hero.activeBody')} ${latest.status.toUpperCase()}. ${t('home.hero.activeBody2')}`
                : t('home.hero.noplanBody')}
            </p>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px', flexWrap: 'wrap' }}>
              <Link
                id={hasPlan ? 'latest-session-link' : 'generate-first-plan-link'}
                to={hasPlan ? `/workout/${latest.session_id}` : '/intake'}
                className="btn btn-primary"
                style={{ padding: '12px 24px', fontSize: '14px', flex: '1 1 auto', justifyContent: 'center' }}
              >
                <span>{hasPlan ? t('home.cta.openWorkout') : t('home.cta.generatePlan')}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
              </Link>

              <Link to="/nutrition" className="btn btn-secondary" style={{ padding: '12px 20px', fontSize: '14px', flex: '1 1 auto', justifyContent: 'center' }}>
                <span>{t('home.cta.buildNutrition')}</span>
              </Link>
            </div>
          </div>

          {/* Quick Metrics Ribbon */}
          <div className="home-metrics-ribbon" style={{ display: 'flex', flexDirection: 'column', gap: '12px', minWidth: '200px', flex: '1 1 200px' }}>
            <div className="glass-panel" style={{ padding: '14px 18px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{t('home.metric.totalSessions')}</span>
              <div className="metric-val" style={{ fontSize: '24px', color: 'var(--accent-primary)', marginTop: '2px' }}>
                {sessions.length} <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>{t('home.metric.plansBuilt')}</span>
              </div>
            </div>
            <div className="glass-panel" style={{ padding: '14px 18px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{t('home.metric.overloadIndex')}</span>
              <div className="metric-val" style={{ fontSize: '24px', color: 'var(--category-data)', marginTop: '2px' }}>
                98.4% <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>{t('home.metric.optimal')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Action Cards Grid */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {t('home.modules.title')}
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {/* Card 1: AI Workout Plan (AI Category: Purple) */}
          <Link to="/workout" style={{ textDecoration: 'none' }}>
            <div className="glass-card-interactive" style={{ padding: '24px', height: '100%', background: 'var(--bg-card)', border: '1px solid color-mix(in srgb, var(--category-ai) 30%, transparent)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'color-mix(in srgb, var(--category-ai) 15%, transparent)', border: '1px solid color-mix(in srgb, var(--category-ai) 40%, transparent)', color: 'var(--category-ai)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px', boxShadow: '0 0 12px color-mix(in srgb, var(--category-ai) 25%, transparent)' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              </div>
              <h4 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>{t('home.card.workout.title')}</h4>
              <p style={{ fontSize: '13px', color: 'var(--text-body)', marginTop: '6px', lineHeight: 1.5 }}>
                {t('home.card.workout.body')}
              </p>
              <div style={{ marginTop: '16px', fontSize: '13px', fontWeight: 700, color: 'var(--category-ai)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t('home.card.workout.cta')}
              </div>
            </div>
          </Link>

          {/* Card 2: Nutrition & Macros (Nutrition Category: Green) */}
          <Link to="/nutrition" style={{ textDecoration: 'none' }}>
            <div className="glass-card-interactive" style={{ padding: '24px', height: '100%', background: 'var(--bg-card)', border: '1px solid color-mix(in srgb, var(--category-nutrition) 30%, transparent)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--accent-primary-muted)', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--category-nutrition)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px', boxShadow: '0 0 12px var(--accent-primary-glow)' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
              </div>
              <h4 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>{t('home.card.nutrition.title')}</h4>
              <p style={{ fontSize: '13px', color: 'var(--text-body)', marginTop: '6px', lineHeight: 1.5 }}>
                {t('home.card.nutrition.body')}
              </p>
              <div style={{ marginTop: '16px', fontSize: '13px', fontWeight: 700, color: 'var(--category-nutrition)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t('home.card.nutrition.cta')}
              </div>
            </div>
          </Link>

          {/* Card 3: InBody & Progress (Data Category: Blue) */}
          <Link to="/progress" style={{ textDecoration: 'none' }}>
            <div className="glass-card-interactive" style={{ padding: '24px', height: '100%', background: 'var(--bg-card)', border: '1px solid color-mix(in srgb, var(--category-data) 30%, transparent)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'color-mix(in srgb, var(--category-data) 15%, transparent)', border: '1px solid color-mix(in srgb, var(--category-data) 40%, transparent)', color: 'var(--category-data)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px', boxShadow: '0 0 12px color-mix(in srgb, var(--category-data) 25%, transparent)' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
              </div>
              <h4 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>{t('home.card.progress.title')}</h4>
              <p style={{ fontSize: '13px', color: 'var(--text-body)', marginTop: '6px', lineHeight: 1.5 }}>
                {t('home.card.progress.body')}
              </p>
              <div style={{ marginTop: '16px', fontSize: '13px', fontWeight: 700, color: 'var(--category-data)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t('home.card.progress.cta')}
              </div>
            </div>
          </Link>

          {/* Card 4: Exercises & CV Coach (Motion Category: Amber) */}
          <Link to="/exercises" style={{ textDecoration: 'none' }}>
            <div className="glass-card-interactive" style={{ padding: '24px', height: '100%', background: 'var(--bg-card)', border: '1px solid color-mix(in srgb, var(--category-motion) 30%, transparent)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'color-mix(in srgb, var(--category-motion) 15%, transparent)', border: '1px solid color-mix(in srgb, var(--category-motion) 40%, transparent)', color: 'var(--category-motion)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px', boxShadow: '0 0 12px color-mix(in srgb, var(--category-motion) 25%, transparent)' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.934a.5.5 0 0 0-.777-.416L16 11"></path><rect x="2" y="6" width="14" height="12" rx="2"></rect></svg>
              </div>
              <h4 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>{t('home.card.cv.title')}</h4>
              <p style={{ fontSize: '13px', color: 'var(--text-body)', marginTop: '6px', lineHeight: 1.5 }}>
                {t('home.card.cv.body')}
              </p>
              <div style={{ marginTop: '16px', fontSize: '13px', fontWeight: 700, color: 'var(--category-motion)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t('home.card.cv.cta')}
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Home;
