import { useState, useEffect } from 'react';

type ExerciseKey = 'squat' | 'deadlift' | 'bicep_curl';

interface ExerciseDef {
  name: string;
  targetJoints: string;
  idealAngle: string;
  errorName: string;
  errorAdvice: string;
}

const EXERCISES: Record<ExerciseKey, ExerciseDef> = {
  squat: {
    name: 'Barbell Back Squat',
    targetJoints: 'Knee, Hip, Ankle, Spine',
    idealAngle: '85° - 90° depth',
    errorName: 'Knee Valgus (Inward Collapse)',
    errorAdvice: 'Warning: Right knee collapsing inward at bottom of rep. Drive knees out over toes.',
  },
  deadlift: {
    name: 'Conventional Deadlift',
    targetJoints: 'Hip Hinge, Spine, Knee',
    idealAngle: '175° lockout',
    errorName: 'Lumbar Flexion (Rounded Back)',
    errorAdvice: 'Critical: Lumbar spine rounding detected during initial pull. Engage lats and brace core.',
  },
  bicep_curl: {
    name: 'Strict Dumbbell Curl',
    targetJoints: 'Elbow, Shoulder stability',
    idealAngle: '40° peak flexion',
    errorName: 'Elbow Drift & Momentum',
    errorAdvice: 'Warning: Elbows drifting forward 15°. Keep upper arm pinned to torso for strict bicep isolation.',
  },
};

export default function PoseVisualizerDemo() {
  const [exercise, setExercise] = useState<ExerciseKey>('squat');
  const [repProgress, setRepProgress] = useState<number>(0.2);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [hasFormFlaw, setHasFormFlaw] = useState<boolean>(false);
  const [repCount, setRepCount] = useState<number>(3);

  // Auto animation loop when playing
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setRepProgress((prev) => {
        const next = prev + 0.04;
        if (next >= 1) {
          setRepCount((c) => c + 1);
          return 0;
        }
        return next;
      });
    }, 60);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const depthFactor = Math.sin(repProgress * Math.PI);
  const stage =
    repProgress < 0.45
      ? 'Eccentric (Lowering)'
      : repProgress <= 0.55
      ? 'Inflection / Peak Depth'
      : repProgress < 0.95
      ? 'Concentric (Ascending)'
      : 'Lockout & Stabilization';

  // Kinematic calculations for squat SVG coordinates
  const headY = 70 + depthFactor * 45;
  const shoulderY = 100 + depthFactor * 45;
  const hipY = 180 + depthFactor * 65;
  const hipX = 160 - (exercise === 'deadlift' ? depthFactor * 25 : depthFactor * 10);
  const kneeY = 250 + depthFactor * 20;
  const kneeX = 165 + (hasFormFlaw && exercise === 'squat' ? -15 : depthFactor * 25);
  const ankleY = 320;
  const ankleX = 160;

  // Joint angle metrics
  const kneeAngle = Math.round(170 - depthFactor * 85);
  const hipAngle = Math.round(165 - depthFactor * 80);
  const formScore = hasFormFlaw ? Math.max(62, Math.round(98 - depthFactor * 32)) : 97;

  return (
    <div
      className="glass-panel pose-demo-container"
      style={{
        padding: 'clamp(18px, 4vw, 28px)',
        background: 'var(--bg-card)',
        border: '1px solid rgba(245, 158, 11, 0.4)',
        boxShadow: '0 0 35px rgba(245, 158, 11, 0.15)',
        borderRadius: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top Ambient Glow */}
      <div
        style={{
          position: 'absolute',
          top: '-20%',
          left: '30%',
          width: '350px',
          height: '350px',
          background: 'radial-gradient(circle, rgba(245, 158, 11, 0.1) 0%, rgba(0, 0, 0, 0) 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* Header with Title & Badge */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
          marginBottom: '20px',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '16px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--category-motion)',
                boxShadow: '0 0 10px var(--category-motion)',
              }}
            />
            <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--category-motion)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              BlazePose CV Simulator (30 FPS)
            </span>
          </div>
          <h3 style={{ fontSize: 'clamp(17px, 3vw, 20px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
            Interactive Biomechanical Form Tracker
          </h3>
        </div>

        {/* Exercise Selector Buttons */}
        <div
          className="pose-selector-group"
          style={{
            display: 'flex',
            background: 'var(--bg-input)',
            padding: '4px',
            borderRadius: '10px',
            border: '1px solid var(--border)',
            flexWrap: 'wrap',
          }}
        >
          {(Object.keys(EXERCISES) as ExerciseKey[]).map((key) => {
            const isSelected = exercise === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setExercise(key)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 700,
                  border: 'none',
                  cursor: 'pointer',
                  background: isSelected ? 'var(--category-motion)' : 'transparent',
                  color: isSelected ? '#062A1E' : 'var(--text-body)',
                  boxShadow: isSelected ? '0 0 12px rgba(245, 158, 11, 0.4)' : 'none',
                  transition: 'all 0.2s ease',
                  flex: '1 1 auto',
                }}
              >
                {key === 'squat' ? 'Squat' : key === 'deadlift' ? 'Deadlift' : 'Bicep Curl'}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Visualizer Canvas + Telemetry Console */}
      <div
        className="pose-main-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(260px, 1fr) minmax(280px, 1.2fr)',
          gap: '24px',
          alignItems: 'center',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Left: Kinematic Skeleton Screen */}
        <div
          style={{
            position: 'relative',
            background: 'var(--bg-input)',
            border: '1px solid var(--border)',
            borderRadius: '14px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            boxShadow: 'inset 0 0 25px rgba(0, 0, 0, 0.6)',
            width: '100%',
          }}
        >
          {/* Overlay Stage Pill */}
          <div
            style={{
              position: 'absolute',
              top: '12px',
              left: '12px',
              padding: '4px 10px',
              borderRadius: '9999px',
              background: 'var(--bg-card)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              fontSize: '11px',
              fontWeight: 700,
              color: 'var(--category-motion)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            STAGE: {stage}
          </div>

          {/* Rep Count Counter */}
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              textAlign: 'right',
            }}
          >
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 800 }}>REPS</span>
            <div className="metric-val" style={{ fontSize: '20px', color: 'var(--accent-primary)' }}>
              {repCount} <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>/ 8</span>
            </div>
          </div>

          {/* Skeleton SVG */}
          <svg
            viewBox="0 0 320 360"
            style={{
              width: '100%',
              maxWidth: '280px',
              height: 'auto',
              maxHeight: '340px',
              margin: '10px 0',
            }}
          >
            {/* Grid Reference Floor Lines */}
            <line x1="40" y1="330" x2="280" y2="330" stroke="var(--border)" strokeWidth="1.5" strokeDasharray="4 4" />
            <line x1="160" y1="40" x2="160" y2="340" stroke="rgba(245, 158, 11, 0.2)" strokeWidth="1" strokeDasharray="3 3" />

            {/* Spine Line */}
            <line
              x1="160"
              y1={headY + 15}
              x2={hipX}
              y2={hipY}
              stroke={hasFormFlaw && exercise === 'deadlift' ? 'var(--status-error)' : 'var(--category-motion)'}
              strokeWidth="4"
              strokeLinecap="round"
            />

            {/* Thigh Line */}
            <line
              x1={hipX}
              y1={hipY}
              x2={kneeX}
              y2={kneeY}
              stroke={hasFormFlaw && exercise === 'squat' ? 'var(--status-error)' : 'var(--accent-primary)'}
              strokeWidth="4"
              strokeLinecap="round"
            />

            {/* Shin Line */}
            <line
              x1={kneeX}
              y1={kneeY}
              x2={ankleX}
              y2={ankleY}
              stroke="var(--category-motion)"
              strokeWidth="4"
              strokeLinecap="round"
            />

            {/* Upper Torso / Arms */}
            <line
              x1="160"
              y1={shoulderY}
              x2="190"
              y2={shoulderY + 45}
              stroke="var(--category-data)"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            <line
              x1="190"
              y1={shoulderY + 45}
              x2={190 + depthFactor * 15}
              y2={shoulderY + 80 - depthFactor * 25}
              stroke="var(--category-data)"
              strokeWidth="3.5"
              strokeLinecap="round"
            />

            {/* Joint Nodes */}
            {/* Head */}
            <circle cx="160" cy={headY} r="16" fill="rgba(245, 158, 11, 0.2)" stroke="var(--category-motion)" strokeWidth="2.5" />
            {/* Shoulder */}
            <circle cx="160" cy={shoulderY} r="6" fill="var(--category-motion)" stroke="var(--bg-card)" strokeWidth="1.5" />
            {/* Hip */}
            <circle cx={hipX} cy={hipY} r="7" fill="var(--accent-primary)" stroke="var(--category-motion)" strokeWidth="1.5" />
            {/* Knee with dynamic warning halo */}
            <circle
              cx={kneeX}
              cy={kneeY}
              r={hasFormFlaw && exercise === 'squat' ? 9 : 7}
              fill={hasFormFlaw && exercise === 'squat' ? 'var(--status-error)' : 'var(--accent-primary)'}
              stroke="#ffffff"
              strokeWidth="2"
            />
            {/* Ankle */}
            <circle cx={ankleX} cy={ankleY} r="6" fill="var(--accent-primary)" stroke="var(--category-motion)" strokeWidth="1.5" />

            {/* Angle Indicator Callout on Knee */}
            <g transform={`translate(${kneeX + 15}, ${kneeY - 10})`}>
              <rect x="0" y="0" width="56" height="22" rx="6" fill="var(--bg-card)" stroke="var(--border-strong)" strokeWidth="1" />
              <text x="8" y="15" fill="var(--category-motion)" fontSize="11" fontFamily="JetBrains Mono" fontWeight="700">
                {kneeAngle}°
              </text>
            </g>

            {/* Hip Angle Callout */}
            <g transform={`translate(${hipX - 65}, ${hipY - 10})`}>
              <rect x="0" y="0" width="56" height="22" rx="6" fill="var(--bg-card)" stroke="var(--border-strong)" strokeWidth="1" />
              <text x="8" y="15" fill="var(--accent-primary)" fontSize="11" fontFamily="JetBrains Mono" fontWeight="700">
                {hipAngle}°
              </text>
            </g>
          </svg>

          {/* Bottom Interactive Scrub Bar */}
          <div style={{ width: '100%', marginTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
              <span>Progress: {Math.round(repProgress * 100)}%</span>
              <span>Target: {EXERCISES[exercise].idealAngle}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={repProgress}
              onChange={(e) => {
                setIsPlaying(false);
                setRepProgress(parseFloat(e.target.value));
              }}
              style={{
                width: '100%',
                accentColor: 'var(--category-motion)',
                cursor: 'pointer',
              }}
            />
          </div>
        </div>

        {/* Right: Live Biomechanics & AI Rule Evaluation Console */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%' }}>
          {/* Form Score & Precision Metric */}
          <div
            style={{
              display: 'flex',
              gap: '12px',
              background: 'var(--bg-input)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
                Instant Form Score
              </span>
              <div
                className="metric-val"
                style={{
                  fontSize: '28px',
                  color: formScore >= 85 ? 'var(--accent-primary)' : 'var(--status-error)',
                  marginTop: '2px',
                }}
              >
                {formScore}<span style={{ fontSize: '15px', color: 'var(--text-muted)' }}>/100</span>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
                Kinematic Precision
              </span>
              <div className="metric-val" style={{ fontSize: '28px', color: 'var(--category-data)', marginTop: '2px' }}>
                99.2% <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Acc</span>
              </div>
            </div>
          </div>

          {/* Active AI Rule Violations & Live Coach Speech Output */}
          <div
            style={{
              padding: '16px',
              borderRadius: '12px',
              background: hasFormFlaw ? 'rgba(239, 68, 68, 0.12)' : 'var(--accent-primary-muted)',
              border: `1px solid ${hasFormFlaw ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
              transition: 'all 0.3s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '16px' }}>{hasFormFlaw ? '⚠️' : '⚡'}</span>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 800,
                  color: hasFormFlaw ? 'var(--status-error)' : 'var(--accent-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {hasFormFlaw ? 'Biomechanical Flaw Detected' : 'Form Optimal & Verified'}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-heading)', margin: 0, lineHeight: 1.5 }}>
              {hasFormFlaw ? EXERCISES[exercise].errorAdvice : `Kinematic angles verified. Spine neutral, full range of motion reached at ${kneeAngle}°. Maintain tempo.`}
            </p>
          </div>

          {/* Interactive Control Knobs */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className={isPlaying ? 'btn btn-secondary' : 'btn btn-primary'}
              style={{ flex: '1 1 140px', padding: '10px 14px', fontSize: '13px' }}
            >
              {isPlaying ? '⏸ Pause Loop' : '▶ Play Rep Loop'}
            </button>

            <button
              type="button"
              onClick={() => setHasFormFlaw(!hasFormFlaw)}
              style={{
                flex: '1 1 160px',
                padding: '10px 14px',
                fontSize: '13px',
                fontWeight: 700,
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                border: '1px solid',
                backgroundColor: hasFormFlaw ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                borderColor: hasFormFlaw ? 'var(--status-error)' : 'var(--category-motion)',
                color: hasFormFlaw ? 'var(--status-error)' : 'var(--category-motion)',
                transition: 'all 0.2s ease',
              }}
            >
              {hasFormFlaw ? '✓ Clear Form Flaw' : `⚡ Test Flaw: ${EXERCISES[exercise].errorName.split(' ')[0]}`}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .pose-main-grid {
            grid-template-columns: 1fr !important;
          }
          .pose-selector-group {
            width: 100% !important;
          }
        }
      `}</style>
    </div>
  );
}
