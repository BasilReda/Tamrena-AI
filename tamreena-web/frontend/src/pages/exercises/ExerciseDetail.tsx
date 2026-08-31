import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import {
  type CvExercise,
  type TamreenaExerciseListItem,
  type TamreenaExerciseDetail,
  getCvExercises,
  getTamreenaExerciseDetail,
  mediaUrl,
} from '../../lib/api';

type Source = 'tamreena' | 'cv';

function ExerciseDetail() {
  const [searchParams] = useSearchParams();
  const nameParam = searchParams.get('name');
  const navigate = useNavigate();
  const location = useLocation();

  const stateExercise = (location.state as { exercise?: TamreenaExerciseListItem; cvExercise?: CvExercise }) || {};

  const [source] = useState<Source>(stateExercise.cvExercise ? 'cv' : 'tamreena');
  const [tamreenaDetail, setTamreenaDetail] = useState<TamreenaExerciseDetail | null>(null);
  const [cvExercise, setCvExercise] = useState<CvExercise | null>(stateExercise.cvExercise ?? null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const targetName = nameParam || (stateExercise.exercise?.name) || (stateExercise.cvExercise?.name);
    if (!targetName) return;

    if (source === 'tamreena') {
      getTamreenaExerciseDetail(targetName)
        .then((data) => setTamreenaDetail(data))
        .catch((err) => setError(err instanceof Error ? err.message : 'Exercise not found'));
    }

    if (source === 'cv' && !cvExercise) {
      getCvExercises()
        .then((data) => {
          const match = data.find((ex) => ex.name.toLowerCase() === targetName.toLowerCase());
          if (match) setCvExercise(match);
          else setError(`CV model not available for ${targetName}`);
        })
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load CV exercise'));
    }
  }, [nameParam, source, cvExercise, stateExercise.exercise, stateExercise.cvExercise]);

  const item = source === 'cv' ? cvExercise : (tamreenaDetail || stateExercise.exercise);

  if (error) {
    return (
      <div style={{ maxWidth: '800px', margin: '48px auto', padding: '0 24px', textAlign: 'center' }}>
        <p style={{ color: '#ff80ab', fontSize: '15px' }}>⚠️ {error}</p>
        <button onClick={() => navigate('/exercises')} className="btn btn-secondary" style={{ marginTop: '16px' }}>
          ← Back to Exercise Directory
        </button>
      </div>
    );
  }

  if (!item) {
    return (
      <div style={{ maxWidth: '800px', margin: '48px auto', padding: '0 24px', textAlign: 'center', color: '#cbd5e1' }}>
        Loading exercise telemetry…
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: 'clamp(16px, 3vw, 32px) clamp(12px, 3vw, 24px)', fontFamily: 'var(--font-sans)' }}>
      {/* Back link */}
      <button
        onClick={() => navigate('/exercises')}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--accent-primary)',
          fontSize: '13px',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: 0,
          marginBottom: '20px',
        }}
      >
        ← Back to Exercises
      </button>

      {/* Main Card */}
      <div
        className="glass-panel"
        style={{
          padding: 'clamp(20px, 4vw, 36px)',
          marginBottom: '28px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span className={source === 'cv' ? 'badge badge-amber' : 'badge badge-primary'}>
            {source === 'cv' ? 'Computer Vision Model' : 'Biomechanical Guide'}
          </span>
          {'target_muscle' in item && item.target_muscle && (
            <span className="badge badge-data">{item.target_muscle}</span>
          )}
        </div>

        <h1 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em', margin: '6px 0 14px' }}>
          {item.name}
        </h1>

        {/* Media or Placeholder */}
        {'image_url' in item && item.image_url && (
          <div style={{ borderRadius: '14px', overflow: 'hidden', maxHeight: '340px', marginBottom: '24px', border: '1px solid var(--border)' }}>
            <img
              src={mediaUrl(item.image_url ?? undefined)}
              alt={item.name}
              style={{ width: '100%', height: '100%', objectFit: 'contain', background: 'var(--bg-input)' }}
            />
          </div>
        )}

        {/* Description / Instructions */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Movement Execution
          </h3>
          <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.7, margin: 0 }}>
            {'description' in item && item.description ? item.description : 'Maintain neutral spine, brace your core, and execute smooth controlled cadence across full range of motion.'}
          </p>
        </div>

        {/* CV Exercise Live Session Launcher Card */}
        {source === 'cv' && cvExercise && (
          <div
            style={{
              padding: 'clamp(16px, 3vw, 24px)',
              borderRadius: '14px',
              background: 'var(--accent-primary-muted)',
              border: '1px solid var(--category-motion)',
              boxShadow: '0 0 25px rgba(245, 158, 11, 0.2)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '14px' }}>⚡</span>
                <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--category-motion)', textTransform: 'uppercase' }}>
                  Live AI Pose Coaching
                </span>
              </div>
              <p style={{ color: 'var(--text-heading)', fontSize: '13px', margin: 0 }}>
                Launch webcam rep tracking with instant joint angle telemetry and audio cues.
              </p>
            </div>

            <button
              onClick={() => navigate('/exercises/live-session', { state: { exercise: cvExercise } })}
              className="btn btn-primary"
              style={{ padding: '12px 28px', fontSize: '14px', flex: '1 1 auto', justifyContent: 'center' }}
            >
              <span>Launch Live CV Studio</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ExerciseDetail;
