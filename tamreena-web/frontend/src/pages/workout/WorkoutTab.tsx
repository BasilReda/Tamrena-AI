import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { getSessions, type WorkoutSession } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

function WorkoutTab() {
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
      <div style={{ padding: '16px', borderRadius: '12px', background: 'color-mix(in srgb, var(--status-error) 15%, transparent)', border: '1px solid color-mix(in srgb, var(--status-error) 30%, transparent)', color: 'var(--status-error)' }}>
        ⚠️ {error}
      </div>
    );
  }

  if (sessions === null) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
        <p>{t('workout.loading')}</p>
      </div>
    );
  }

  if (sessions.length > 0) {
    return <Navigate to={`/workout/${sessions[0].session_id}`} replace />;
  }

  return (
    <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', maxWidth: '640px', margin: '40px auto' }}>
      <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'var(--accent-primary-muted)', border: '1px solid color-mix(in srgb, var(--accent-primary) 30%, transparent)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
      </div>

      <h2 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-heading)', marginBottom: '12px' }}>{t('workout.noplan.title')}</h2>
      <p style={{ color: 'var(--text-body)', fontSize: '15px', lineHeight: 1.6, marginBottom: '28px' }}>
        {t('workout.noplan.body')}
      </p>

      <Link
        id="start-intake-link"
        to="/intake"
        className="btn btn-primary"
        style={{ padding: '14px 32px', fontSize: '15px' }}
      >
        <span>{t('workout.noplan.cta')}</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
      </Link>
    </div>
  );
}

export default WorkoutTab;
