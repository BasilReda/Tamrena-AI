import { useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  getSessionPlan,
  submitFeedback,
  type ExerciseFeedback,
  type ParsedDay,
  type ParsedExercise,
  type SessionPlanResponse,
} from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

function PlanView() {
  const { t } = useTranslation();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [planData, setPlanData] = useState<SessionPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [activeDayId, setActiveDayId] = useState<number | null>(null);

  const [dayLabel, setDayLabel] = useState<string>('');
  const [exerciseName, setExerciseName] = useState<string>('');
  const [difficulty, setDifficulty] = useState<ExerciseFeedback['difficulty']>('just_right');
  const [pain, setPain] = useState(false);
  const [feedbackNote, setFeedbackNote] = useState('');
  const [feedbackResult, setFeedbackResult] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadPlan = () => {
    if (!sessionId) return;
    getSessionPlan(sessionId)
      .then((data) => {
        setPlanData(data);
        const freshDays = data.days ?? [];
        if (freshDays.length > 0) {
          setActiveDayId((current) => current ?? freshDays[0].day_number);

          const resolvedDayLabel = dayLabel || freshDays[0].label;
          const dayForLabel = freshDays.find((d) => d.label === resolvedDayLabel) ?? freshDays[0];
          setDayLabel(resolvedDayLabel);

          const exerciseStillExists =
            !!exerciseName && dayForLabel.exercises.some((ex) => ex.name === exerciseName);
          setExerciseName(exerciseStillExists ? exerciseName : dayForLabel.exercises[0]?.name ?? '');
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load plan'));
  };

  useEffect(loadPlan, [sessionId]);

  // Generation can still be running when this page mounts (the previous
  // screen navigates as soon as it gets the SSE "done" event, but that
  // event fires the instant the backend's async task exits — a "ready"
  // status update and a "done" event both leave the same await chain, but
  // there's no guarantee of exactly which happens first from the client's
  // perspective; more importantly, the whole point of this endpoint is
  // also to be visited directly / reloaded any time, so it needs to work
  // when landed on mid-generation too). Without polling here, a session
  // that's still "pending" on the first fetch would show "Loading..."
  // forever with no way to ever see the finished result short of a manual
  // refresh timed after the backend actually finishes.
  useEffect(() => {
    if (planData?.status !== 'pending') return;
    const interval = setInterval(loadPlan, 5000);
    return () => clearInterval(interval);
  }, [planData?.status, sessionId]);

  const days: ParsedDay[] = planData?.days ?? [];
  const activeDay = days.find((d) => d.day_number === activeDayId) ?? days[0];
  const selectedDayObject = days.find((d) => d.label === dayLabel) ?? activeDay;

  const handleDaySelectChange = (newDayLabel: string) => {
    setDayLabel(newDayLabel);
    const dayObj = days.find((d) => d.label === newDayLabel);
    if (dayObj && dayObj.exercises.length > 0) {
      setExerciseName(dayObj.exercises[0].name);
    }
  };

  const handleOpenFeedback = (exercise: ParsedExercise) => {
    setExerciseName(exercise.name);
    if (activeDay) setDayLabel(activeDay.label);
    setDifficulty('just_right');
    setPain(false);
    setFeedbackNote('');
    setFeedbackResult(null);

    const el = document.getElementById('exercise-feedback-section');
    el?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleFeedbackSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!sessionId) return;
    setSubmitting(true);
    setFeedbackResult(null);
    try {
      const result = await submitFeedback(sessionId, dayLabel, [
        { name: exerciseName, difficulty, pain, note: feedbackNote || undefined },
      ]);

      if (result.adjustment_triggered && result.adjustments && result.adjustments.length > 0) {
        const adj = result.adjustments[0];
        setFeedbackResult(
          adj.new_exercise_name
            ? `✨ AI Core Adjusted Routine: Swapped for ${adj.new_exercise_name}! (${adj.reason})`
            : result.summary ?? 'Feedback recorded and the plan was adjusted.',
        );
        loadPlan();
      } else {
        setFeedbackResult(result.summary ?? 'Feedback recorded successfully by AI Core.');
      }
    } catch (err) {
      setFeedbackResult(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  if (error) {
    return (
      <div className="glass-panel" style={{ maxWidth: '540px', margin: '40px auto', padding: '36px', textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px' }}>
        <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--status-error)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '24px', border: '1px solid var(--status-error)' }}>
          ⚠️
        </div>
        <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
          {t('plan.failed')}
        </h3>
        <p style={{ color: 'var(--text-body)', fontSize: '14px', marginBottom: '24px' }}>{error}</p>
        <Link
          to="/intake"
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px 20px', justifyContent: 'center' }}
        >
          <span>{t('home.cta.generatePlan')}</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
        </Link>
      </div>
    );
  }

  if (!planData || planData.status === 'pending') {
    return (
      <div className="glass-panel" style={{ maxWidth: '520px', margin: '60px auto', padding: '40px', textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px' }}>
        <div style={{ position: 'relative', width: '70px', height: '70px', margin: '0 auto 20px' }}>
          <div
            style={{
              width: '70px',
              height: '70px',
              borderRadius: '50%',
              border: '3px solid var(--border)',
              borderTopColor: 'var(--accent-primary)',
              borderRightColor: 'var(--category-data)',
              animation: 'spin 1.2s linear infinite',
            }}
          />
        </div>
        <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-heading)', marginBottom: '8px' }}>
          {t('plan.loading')}
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '13.5px', marginBottom: '24px' }}>
          Formulating exercise volumes, rest intervals, and customized splits...
        </p>
        <Link
          to="/intake"
          className="btn btn-secondary"
          style={{ fontSize: '13px', padding: '8px 18px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <span>{t('home.cta.generatePlan')}</span>
          <span>→</span>
        </Link>
      </div>
    );
  }

  if (planData.status === 'failed') {
    return (
      <div className="glass-panel" style={{ maxWidth: '540px', margin: '40px auto', padding: '36px', textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px' }}>
        <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--status-error)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '24px', border: '1px solid var(--status-error)' }}>
          ⚠️
        </div>
        <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
          {t('plan.failed')}
        </h3>
        <p style={{ color: 'var(--text-body)', fontSize: '14px', marginBottom: '24px', lineHeight: 1.5 }}>
          {planData.error || 'The workout plan for this session is unavailable.'}
        </p>
        <Link
          to="/intake"
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px 20px', justifyContent: 'center' }}
        >
          <span>{t('home.cta.generatePlan')}</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
        </Link>
      </div>
    );
  }

  if (!activeDay) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <p style={{ fontWeight: 600 }}>{t('plan.nodays')}</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(20px, 4vw, 28px)' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span className="badge badge-primary">{t('plan.badge')}</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t('plan.session')}{sessionId?.slice(-6)}</span>
          </div>
          <h1 style={{ fontSize: 'clamp(22px, 3.5vw, 28px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0, letterSpacing: '-0.02em' }}>
            {t('plan.title')}
          </h1>
        </div>

        <button onClick={() => window.print()} className="btn btn-secondary" style={{ gap: '8px', fontSize: '13px' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"></path></svg>
          {t('plan.export')}
        </button>
      </div>

      {/* Day Selector Horizontal Scroll */}
      <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '6px', WebkitOverflowScrolling: 'touch' }}>
        {days.map((day) => {
          const isActive = day.day_number === activeDay.day_number;
          return (
            <button
              key={day.day_number}
              onClick={() => {
                setActiveDayId(day.day_number);
                setDayLabel(day.label);
                if (day.exercises.length > 0) setExerciseName(day.exercises[0].name);
              }}
              style={{
                padding: '10px 18px',
                borderRadius: '10px',
                border: isActive ? '1px solid var(--accent-primary)' : '1px solid var(--border)',
                background: isActive ? 'var(--accent-primary-muted)' : 'var(--bg-card)',
                color: isActive ? 'var(--accent-primary)' : 'var(--text-body)',
                fontWeight: isActive ? 800 : 500,
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 0 15px var(--accent-primary-glow)' : 'none',
              }}
            >
              {day.label}
            </button>
          );
        })}
      </div>

      {/* Active Day Table & Details */}
      <div className="glass-panel" style={{ padding: 'clamp(18px, 4vw, 28px)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: 'clamp(18px, 3vw, 22px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
              {activeDay.label}
            </h2>
            <span style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 700, letterSpacing: '0.05em' }}>
              {t('plan.targetFocus')} {activeDay.target_focus}
            </span>
          </div>

          <span className="badge badge-primary">
            {activeDay.exercises.length} {t('plan.exercises')}
          </span>
        </div>

        {activeDay.warmup && (
          <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '10px', padding: '14px 18px', marginBottom: '24px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
              {t('plan.warmup')}
            </span>
            <p style={{ fontSize: '13.5px', color: 'var(--text-body)', margin: 0 }}>
              {activeDay.warmup}
            </p>
          </div>
        )}

        <div style={{ overflowX: 'auto', borderRadius: '10px', border: '1px solid var(--border)', marginBottom: '28px', WebkitOverflowScrolling: 'touch' }}>
          <table style={{ width: '100%', minWidth: '600px', borderCollapse: 'collapse', textAlign: 'left', fontFamily: 'var(--font-sans)' }}>
            <thead>
              <tr style={{ background: 'var(--bg-input)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t('plan.col.num')}</th>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t('plan.col.exercise')}</th>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t('plan.col.muscle')}</th>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t('plan.col.volume')}</th>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{t('plan.col.rpe')}</th>
                <th style={{ padding: '12px 14px', fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', textAlign: 'right' }}>{t('plan.col.log')}</th>
              </tr>
            </thead>
            <tbody>
              {activeDay.exercises.map((ex, idx) => (
                <tr key={`${ex.name}-${idx}`} style={{ borderBottom: '1px solid var(--border)', background: idx % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent' }}>
                  <td style={{ padding: '14px', fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {idx + 1}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-heading)' }}>
                      {ex.name}
                    </div>
                    {ex.replaced_from && (
                      <span className="badge badge-amber" style={{ padding: '2px 6px', fontSize: '10px', marginTop: '4px' }}>
                        {t('plan.replaced')} {ex.replaced_from})
                      </span>
                    )}
                    {ex.adjustment_reason && (
                      <p style={{ fontSize: '11px', color: 'var(--category-motion)', margin: '2px 0 0 0' }}>
                        {t('plan.reason')} {ex.adjustment_reason}
                      </p>
                    )}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <span className="badge badge-data" style={{ padding: '3px 8px', fontSize: '10px' }}>
                      {ex.muscle_group ?? '—'}
                    </span>
                  </td>
                  <td style={{ padding: '14px', fontSize: '13px', fontWeight: 700, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>
                    {ex.sets != null && ex.reps ? `${ex.sets} sets × ${ex.reps} reps` : '—'}
                  </td>
                  <td style={{ padding: '14px', fontSize: '12px', color: 'var(--text-body)' }}>
                    {ex.rpe ? `RPE ${ex.rpe}` : ''}{ex.rpe && ex.rest ? ' · ' : ''}{ex.rest ? `${ex.rest} rest` : ''}
                  </td>
                  <td style={{ padding: '14px', textAlign: 'right' }}>
                    <button
                      type="button"
                      onClick={() => handleOpenFeedback(ex)}
                      className="btn btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px', gap: '4px' }}
                    >
                      <span>{t('plan.adjust')}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <details style={{ marginTop: '16px' }}>
          <summary style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600, cursor: 'pointer', outline: 'none' }}>
            {t('plan.rawText')}
          </summary>
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              fontFamily: 'var(--font-sans)',
              fontSize: '13px',
              lineHeight: 1.6,
              color: 'var(--text-body)',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border)',
              borderRadius: '10px',
              padding: '16px',
              marginTop: '12px',
            }}
          >
            {planData.plan}
          </pre>
        </details>

        <div id="exercise-feedback-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '24px', marginTop: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ color: 'var(--accent-primary)' }}>⚡</span>
            <h4 style={{ fontSize: '13px', fontWeight: 800, letterSpacing: '0.05em', color: 'var(--accent-primary)', textTransform: 'uppercase', margin: 0 }}>
              {t('plan.feedback.title')}
            </h4>
          </div>

          <form onSubmit={handleFeedbackSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">{t('plan.feedback.day')}</label>
              <select
                id="feedback-day-label"
                value={dayLabel}
                onChange={(e) => handleDaySelectChange(e.target.value)}
                className="form-input"
                required
              >
                {days.map((d) => (
                  <option key={d.day_number} value={d.label} style={{ background: 'var(--bg-input)' }}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">{t('plan.feedback.exercise')}</label>
              <select
                id="feedback-exercise-name"
                value={exerciseName}
                onChange={(e) => setExerciseName(e.target.value)}
                className="form-input"
                required
              >
                {(selectedDayObject?.exercises ?? []).map((ex) => (
                  <option key={ex.name} value={ex.name} style={{ background: 'var(--bg-input)' }}>
                    {ex.name}{ex.muscle_group ? ` (${ex.muscle_group})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">{t('plan.feedback.difficulty')}</label>
              <select
                id="feedback-difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as ExerciseFeedback['difficulty'])}
                className="form-input"
              >
                <option value="too_easy" style={{ background: 'var(--bg-input)' }}>{t('plan.feedback.tooEasy')}</option>
                <option value="just_right" style={{ background: 'var(--bg-input)' }}>{t('plan.feedback.justRight')}</option>
                <option value="too_hard" style={{ background: 'var(--bg-input)' }}>{t('plan.feedback.tooHard')}</option>
              </select>
            </div>

            <div className="form-group" style={{ gridColumn: '1 / -1', marginBottom: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <input
                  id="feedback-pain-checkbox"
                  type="checkbox"
                  checked={pain}
                  onChange={(e) => setPain(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--status-error)', cursor: 'pointer' }}
                />
                <label htmlFor="feedback-pain-checkbox" style={{ fontSize: '13px', fontWeight: 700, color: pain ? 'var(--status-error)' : 'var(--text-body)', cursor: 'pointer' }}>
                  {t('plan.feedback.pain')}
                </label>
              </div>
              <textarea
                placeholder={t('plan.feedback.placeholder')}
                value={feedbackNote}
                onChange={(e) => setFeedbackNote(e.target.value)}
                rows={2}
                className="form-input"
                style={{ height: '70px', resize: 'vertical' }}
              />
            </div>

            <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
              <button
                id="submit-feedback-btn"
                type="submit"
                disabled={submitting}
                className="btn btn-primary"
                style={{ padding: '12px 28px', fontSize: '14px' }}
              >
                {submitting ? t('plan.feedback.analyzing') : t('plan.feedback.submit')}
              </button>
            </div>
          </form>

          {feedbackResult && (
            <div
              style={{
                marginTop: '16px',
                padding: '16px',
                borderRadius: '10px',
                background: feedbackResult.includes('Adjusted') || feedbackResult.includes('Swapped') ? 'color-mix(in srgb, var(--category-motion) 15%, transparent)' : 'var(--accent-primary-muted)',
                border: feedbackResult.includes('Adjusted') || feedbackResult.includes('Swapped') ? '1px solid var(--category-motion)' : '1px solid var(--accent-primary)',
                color: feedbackResult.includes('Adjusted') || feedbackResult.includes('Swapped') ? 'var(--category-motion)' : 'var(--accent-primary)',
                fontSize: '14px',
                fontWeight: 600,
              }}
            >
              {feedbackResult}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PlanView;
