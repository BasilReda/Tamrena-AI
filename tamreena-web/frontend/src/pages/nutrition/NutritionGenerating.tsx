import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getNutritionResult, getNutritionStreamUrl } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

interface NutritionGeneratingLocationState {
  run_id: string;
}

const STEP_DEFINITIONS = [
  {
    id: 'profile',
    labelKey: 'nutrition.generating.step.profile',
    nodes: ['profile', 'profile_agent'],
    progress: 15,
  },
  {
    id: 'calories',
    labelKey: 'nutrition.generating.step.calories',
    nodes: ['calories', 'calories_calculator'],
    progress: 30,
  },
  {
    id: 'macros',
    labelKey: 'nutrition.generating.step.macros',
    nodes: ['macros', 'macro_calculator'],
    progress: 45,
  },
  {
    id: 'meal_composition',
    labelKey: 'nutrition.generating.step.mealComposition',
    nodes: [
      'meal_distributor',
      'retrieve_foods',
      'food_retrieval',
      'compose_meal',
      'dataset_triple_composer',
      'compose_meals_iterative',
      'compose_meals_parquet_arabic',
      'increment_retry',
    ],
    progress: 75,
  },
  {
    id: 'validation',
    labelKey: 'nutrition.generating.step.validation',
    nodes: ['validate', 'validation_engine'],
    progress: 88,
  },
  {
    id: 'explanation',
    labelKey: 'nutrition.generating.step.explanation',
    nodes: ['explain', 'explanation_agent', 'workflow'],
    progress: 100,
  },
];

function NutritionGenerating() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as NutritionGeneratingLocationState | null;

  const [statusText, setStatusText] = useState(t('nutrition.generating.init'));
  const [currentNode, setCurrentNode] = useState<string>('profile');
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [progressPercent, setProgressPercent] = useState<number>(10);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollIntervalRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<number | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!state?.run_id) {
      navigate('/nutrition/intake', { replace: true });
      return;
    }

    const runId = state.run_id;

    // Elapsed timer
    timerIntervalRef.current = window.setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    const handleSuccess = () => {
      if (completedRef.current) return;
      completedRef.current = true;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollIntervalRef.current !== null) {
        window.clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (timerIntervalRef.current !== null) {
        window.clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
      navigate(`/nutrition/results/${encodeURIComponent(runId)}`, { replace: true });
    };

    // Dual-channel checking: Background polling in parallel with SSE
    const checkResultDirectly = async () => {
      try {
        const res = await getNutritionResult(runId);
        if (res && res.success && (res.meal_plan || res.triple_meal_plan)) {
          handleSuccess();
        } else if (res && res.error) {
          completedRef.current = true;
          setError(res.error);
        }
      } catch {
        // Result not ready yet, continue polling
      }
    };

    pollIntervalRef.current = window.setInterval(checkResultDirectly, 2500);

    // Initial check in case it finished instantly
    checkResultDirectly();

    // SSE Stream
    try {
      const streamUrl = getNutritionStreamUrl(runId);
      const eventSource = new EventSource(streamUrl);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.node) {
            const rawNode = String(data.node).toLowerCase();
            setCurrentNode(rawNode);

            // Find step matching this node
            const matchedStepIndex = STEP_DEFINITIONS.findIndex((s) => s.nodes.includes(rawNode));
            if (matchedStepIndex !== -1) {
              const prevStepIds = STEP_DEFINITIONS.slice(0, matchedStepIndex).map((s) => s.id);
              setCompletedSteps(prevStepIds);
              setProgressPercent(STEP_DEFINITIONS[matchedStepIndex].progress);
            }
          }

          if (data.progress && typeof data.progress === 'number') {
            setProgressPercent((prev) => Math.max(prev, data.progress));
          }

          if (data.node === 'workflow' && data.status === 'completed') {
            setCompletedSteps(STEP_DEFINITIONS.map((s) => s.id));
            setProgressPercent(100);
            handleSuccess();
          } else if (data.node === 'workflow' && data.status === 'failed') {
            setError(data.reason || data.message || 'Nutrition plan generation failed.');
          } else if (data.message) {
            setStatusText(data.message);
          }
        } catch {
          // ignore parsing error
        }
      };

      eventSource.onerror = () => {
        // Don't crash immediately on SSE disconnect — fallback to polling
        checkResultDirectly();
      };
    } catch {
      // Fallback solely to polling
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollIntervalRef.current !== null) {
        window.clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (timerIntervalRef.current !== null) {
        window.clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    };
  }, [state, navigate]);

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (error) {
    return (
      <div className="glass-panel" style={{ maxWidth: '520px', margin: '60px auto', textAlign: 'center', padding: '40px', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--status-error)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '26px', border: '1px solid var(--status-error)' }}>
          ⚠️
        </div>
        <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
          {t('nutrition.generating.error.title')}
        </h2>
        <p style={{ color: 'var(--text-body)', fontSize: '14px', marginBottom: '24px' }}>{error}</p>
        <button
          id="nutrition-generating-retry-btn"
          onClick={() => navigate('/nutrition/intake')}
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px' }}
        >
          {t('nutrition.generating.error.retry')}
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '620px', margin: '40px auto', padding: '0 16px' }}>
      <div
        className="glass-panel"
        style={{
          padding: 'clamp(28px, 5vw, 44px)',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          textAlign: 'center',
          boxShadow: '0 0 35px var(--accent-primary-glow)',
          borderRadius: '16px',
        }}
      >
        {/* Animated Loading Spinner & Progress Ring */}
        <div style={{ position: 'relative', width: '80px', height: '80px', margin: '0 auto 24px' }}>
          <div
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              border: '4px solid var(--border)',
              borderTopColor: 'var(--accent-primary)',
              borderRightColor: 'var(--category-data)',
              animation: 'spin 1.2s linear infinite',
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '13px',
              fontWeight: 800,
              color: 'var(--text-heading)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {formatTimer(elapsedSeconds)}
          </div>
        </div>

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '9999px', background: 'var(--accent-primary-muted)', border: '1px solid rgba(16, 185, 129, 0.4)', marginBottom: '14px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-primary)', boxShadow: '0 0 10px var(--accent-primary)' }} />
          <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {t('nutrition.generating.badge')}
          </span>
        </div>

        <h1 style={{ fontSize: 'clamp(22px, 4vw, 26px)', fontWeight: 800, color: 'var(--text-heading)', margin: '0 0 8px 0' }}>
          {t('nutrition.generating.title')}
        </h1>
        <p id="nutrition-generating-status" style={{ color: 'var(--category-data)', fontSize: '14.5px', marginBottom: '8px', fontWeight: 600 }}>
          {statusText}
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', marginBottom: '22px' }}>
          {t('nutrition.generating.subtitle')}
        </p>

        {/* Linear Progress Bar */}
        <div style={{ width: '100%', height: '6px', background: 'var(--bg-input)', borderRadius: '9999px', overflow: 'hidden', marginBottom: '24px', border: '1px solid var(--border)' }}>
          <div
            style={{
              height: '100%',
              width: `${progressPercent}%`,
              background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--category-data) 100%)',
              transition: 'width 0.4s ease-in-out',
            }}
          />
        </div>

        {/* Pipeline Step Progress */}
        <div
          style={{
            textAlign: 'left',
            background: 'var(--bg-input)',
            borderRadius: '14px',
            padding: '16px 20px',
            border: '1px solid var(--border)',
          }}
        >
          {STEP_DEFINITIONS.map((step, i) => {
            const isDone = completedSteps.includes(step.id);
            const isCurrent = !isDone && step.nodes.includes(currentNode);

            return (
              <div
                key={step.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '10px 0',
                  borderBottom: i < STEP_DEFINITIONS.length - 1 ? '1px solid var(--border)' : 'none',
                }}
              >
                <div
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 800,
                    backgroundColor: isDone
                      ? 'var(--accent-primary)'
                      : isCurrent
                      ? 'var(--category-data)'
                      : 'rgba(148, 163, 184, 0.2)',
                    color: isDone || isCurrent ? '#000' : 'var(--text-muted)',
                    boxShadow: isDone
                      ? '0 0 10px var(--accent-primary-glow)'
                      : isCurrent
                      ? '0 0 10px var(--category-data)'
                      : 'none',
                    transition: 'all 0.3s',
                  }}
                >
                  {isDone ? '✓' : i + 1}
                </div>
                <span
                  style={{
                    fontSize: '13.5px',
                    fontWeight: isCurrent ? 700 : isDone ? 600 : 400,
                    color: isDone
                      ? 'var(--text-heading)'
                      : isCurrent
                      ? 'var(--category-data)'
                      : 'var(--text-muted)',
                    transition: 'all 0.3s',
                  }}
                >
                  {t(step.labelKey)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default NutritionGenerating;
