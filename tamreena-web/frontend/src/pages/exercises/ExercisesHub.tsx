import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  type CvExercise,
  type TamreenaExerciseListItem,
  getCvExercises,
  getTamreenaExercises,
  mediaUrl,
} from '../../lib/api';

type HubMode = 'all' | 'cv';

function ExercisesHub() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<HubMode>('all');
  const [tamreenaItems, setTamreenaItems] = useState<TamreenaExerciseListItem[] | null>(null);
  const [cvItems, setCvItems] = useState<CvExercise[] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTamreenaExercises()
      .then((data) => setTamreenaItems(data.exercises))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load exercises'));
  }, []);

  const handleModeChange = (newMode: HubMode) => {
    setMode(newMode);
    setError(null);
    if (newMode === 'cv' && cvItems === null) {
      getCvExercises()
        .then((data) => setCvItems(data))
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load CV exercises'));
    }
  };

  const filteredTamreena = tamreenaItems
    ? tamreenaItems.filter((ex) => {
        const q = searchQuery.toLowerCase();
        return ex.name.toLowerCase().includes(q) || (ex.target_muscle && ex.target_muscle.toLowerCase().includes(q));
      })
    : null;

  const filteredCv = cvItems
    ? cvItems.filter((ex) => {
        const q = searchQuery.toLowerCase();
        return ex.name.toLowerCase().includes(q) || ex.muscle_groups.some((m: string) => m.toLowerCase().includes(q));
      })
    : null;

  const openTamreenaDetail = (item: TamreenaExerciseListItem) => {
    navigate(`/exercises/detail?name=${encodeURIComponent(item.name)}`, { state: { exercise: item } });
  };

  const openCvDetail = (item: CvExercise) => {
    navigate(`/exercises/detail?name=${encodeURIComponent(item.name)}`, { state: { cvExercise: item } });
  };

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: 'clamp(16px, 3vw, 32px) clamp(12px, 3vw, 24px)', fontFamily: 'var(--font-sans)' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span className="badge badge-cyan">Exercise & Kinematics Directory</span>
        </div>
        <h1 style={{ fontSize: 'clamp(22px, 4vw, 32px)', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', margin: '6px 0' }}>
          Movement Intelligence Hub
        </h1>
        <p style={{ color: '#cbd5e1', fontSize: '14px', margin: 0 }}>
          Explore resistance movements with form guides or launch real-time AI computer-vision tracking.
        </p>
      </div>

      {/* Mode Switcher + Search Bar */}
      <div
        className="hub-controls-bar"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
          marginBottom: '28px',
        }}
      >
        {/* Toggle Switcher */}
        <div
          className="hub-toggle-group"
          style={{
            display: 'flex',
            background: 'rgba(10, 20, 56, 0.85)',
            padding: '4px',
            borderRadius: '12px',
            border: '1px solid rgba(0, 255, 255, 0.25)',
            flex: '1 1 auto',
            maxWidth: '400px',
          }}
        >
          <button
            id="exercises-mode-all"
            type="button"
            onClick={() => handleModeChange('all')}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: mode === 'all' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'all' ? 'var(--text-on-accent)' : 'var(--text-body)',
              fontWeight: 800,
              fontSize: '13px',
              cursor: 'pointer',
              boxShadow: mode === 'all' ? '0 0 14px var(--accent-primary-glow)' : 'none',
              transition: 'all 0.2s',
            }}
          >
            All Database ({tamreenaItems?.length ?? '...'})
          </button>
          <button
            id="exercises-mode-cv"
            type="button"
            onClick={() => handleModeChange('cv')}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: mode === 'cv' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'cv' ? 'var(--text-on-accent)' : 'var(--text-body)',
              fontWeight: 800,
              fontSize: '13px',
              cursor: 'pointer',
              boxShadow: mode === 'cv' ? '0 0 14px var(--accent-primary-glow)' : 'none',
              transition: 'all 0.2s',
            }}
          >
            ⚡ Live CV Tracked
          </button>
        </div>

        {/* Search Bar Input */}
        <div style={{ position: 'relative', flex: '1 1 240px' }}>
          <input
            type="text"
            placeholder="Search by muscle or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input"
            style={{
              paddingLeft: '38px',
              background: 'rgba(10, 20, 56, 0.85)',
              borderColor: 'rgba(0, 255, 255, 0.25)',
              borderRadius: '12px',
              height: '42px',
              fontSize: '13px',
            }}
          />
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#708090',
            }}
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </div>
      </div>

      {error && (
        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(255, 23, 68, 0.12)', border: '1px solid rgba(255, 23, 68, 0.3)', color: '#ff80ab', fontSize: '13px', marginBottom: '24px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Grid of Exercises */}
      {mode === 'all' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
          {!filteredTamreena ? (
            <div style={{ color: '#708090', gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
              Loading movement records...
            </div>
          ) : filteredTamreena.length === 0 ? (
            <div style={{ color: '#708090', gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
              No exercises match your search query.
            </div>
          ) : (
            filteredTamreena.map((item, idx) => (
              <div
                key={idx}
                onClick={() => openTamreenaDetail(item)}
                className="glass-card-interactive glow-card-cyan"
                style={{
                  borderRadius: '16px',
                  overflow: 'hidden',
                  background: 'rgba(10, 20, 56, 0.85)',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                {item.image_url ? (
                  <div style={{ height: '140px', width: '100%', overflow: 'hidden', background: '#050c24' }}>
                    <img
                      src={mediaUrl(item.image_url ?? undefined)}
                      alt={item.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      loading="lazy"
                    />
                  </div>
                ) : (
                  <div style={{ height: '100px', width: '100%', background: 'linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 128, 128, 0.15) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '32px' }}>🏋️</span>
                  </div>
                )}

                <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <span className="badge badge-slate" style={{ fontSize: '10px', marginBottom: '6px' }}>
                      {item.target_muscle || 'Full Body'}
                    </span>
                    <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff', margin: '4px 0 0' }}>
                      {item.name}
                    </h3>
                  </div>

                  <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {item.equipment || 'Bodyweight'}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-primary)' }}>
                      View Guide →
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {!filteredCv ? (
            <div style={{ color: 'var(--text-muted)', gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
              Loading Computer Vision models...
            </div>
          ) : filteredCv.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
              No CV exercises match your filter.
            </div>
          ) : (
            filteredCv.map((item) => (
              <div
                key={item.id}
                onClick={() => openCvDetail(item)}
                className="glass-card-interactive"
                style={{
                  borderRadius: '16px',
                  padding: '20px',
                  background: 'var(--bg-card)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span className="badge badge-amber">30 FPS BlazePose</span>
                    <span style={{ fontSize: '11px', color: 'var(--category-motion)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      {item.id}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                    {item.name}
                  </h3>

                  <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.5, margin: '8px 0 16px' }}>
                    {item.description || 'Full biomechanical rep tracking with real-time audio corrections.'}
                  </p>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                    {item.muscle_groups.map((m: string, i: number) => (
                      <span key={i} style={{ padding: '3px 8px', borderRadius: '6px', background: 'var(--bg-input)', fontSize: '11px', color: 'var(--text-body)', border: '1px solid var(--border)' }}>
                        {m}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Focus: <strong style={{ color: 'var(--text-heading)' }}>{item.muscle_groups.join(', ')}</strong>
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--category-motion)' }}>
                    Start CV Live →
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default ExercisesHub;
