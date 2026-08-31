import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  type CvSessionReport,
  getLiveSessionReport,
  getLiveSessionWebSocketUrl,
  uploadLiveSessionVideo,
} from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import SessionReportView from './SessionReportView';

type Phase = 'upload' | 'live' | 'complete' | 'error';
type InputMode = 'upload' | 'camera';

interface LiveState {
  reps: number;
  good: number;
  bad: number;
  feedback: string[];
}

interface CompletionResult {
  reps: number;
  good: number;
  bad: number;
}

const INITIAL_LIVE_STATE: LiveState = { reps: 0, good: 0, bad: 0, feedback: [] };

const AVAILABLE_EXERCISES = [
  { id: 'biceps_curl', name: 'Biceps / Dumbbell Curl' },
  { id: 'squat', name: 'Barbell / Bodyweight Squat' },
  { id: 'pushup', name: 'Push-Up' },
  { id: 'deadlift', name: 'Deadlift' },
  { id: 'shoulder_press', name: 'Shoulder Press' },
  { id: 'lat_pulldown', name: 'Lat Pulldown' },
  { id: 'lateral_raise', name: 'Lateral Raise' },
  { id: 'leg_press', name: 'Leg Press' },
  { id: 'hack_squat', name: 'Hack Squat' },
  { id: 'upright_row', name: 'Upright Row' },
  { id: 'cable_chest_fly', name: 'Cable Chest Fly' },
  { id: 'cable_straight_arm_pulldown', name: 'Cable Straight Arm Pulldown' },
  { id: 'hyp', name: 'Hyperextension' },
];

function LiveSession() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const state = location.state as { exercise?: { id?: string; name?: string } | string } | null;
  const stateEx = typeof state?.exercise === 'object'
    ? (state.exercise.id || state.exercise.name)
    : state?.exercise;
  const initialExercise = searchParams.get('exercise') ?? stateEx ?? 'biceps_curl';

  const [exercise, setExercise] = useState<string>(initialExercise);
  const [inputMode, setInputMode] = useState<InputMode>('upload');
  const [phase, setPhase] = useState<Phase>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [liveState, setLiveState] = useState<LiveState>(INITIAL_LIVE_STATE);
  const [frameUrl, setFrameUrl] = useState<string | null>(null);
  const [result, setResult] = useState<CompletionResult | null>(null);
  const [cvSessionId, setCvSessionId] = useState<string | null>(null);
  const [report, setReport] = useState<CvSessionReport | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const liveStateRef = useRef<LiveState>(INITIAL_LIVE_STATE);
  const phaseRef = useRef<Phase>('upload');
  const frameUrlRef = useRef<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const frameIntervalRef = useRef<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  phaseRef.current = phase;

  const stopCameraStream = useCallback(() => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraReady(false);
  }, []);

  const stopFrameCapture = useCallback(() => {
    if (frameIntervalRef.current !== null) {
      window.clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  }, []);

  const startCameraStream = useCallback(async () => {
    setCameraError(null);
    try {
      if (mediaStreamRef.current && mediaStreamRef.current.active) {
        if (videoRef.current && videoRef.current.srcObject !== mediaStreamRef.current) {
          videoRef.current.srcObject = mediaStreamRef.current;
          await videoRef.current.play().catch(() => {});
        }
        setCameraReady(true);
        return;
      }
      stopCameraStream();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(() => {});
          setCameraReady(true);
        };
      } else {
        setCameraReady(true);
      }
    } catch (err) {
      setCameraReady(false);
      setCameraError(
        err instanceof Error
          ? `${t('liveSession.camera.permissionDenied')} (${err.message})`
          : t('liveSession.camera.permissionDenied')
      );
    }
  }, [stopCameraStream, t]);

  useEffect(() => {
    if (inputMode === 'camera' && (phase === 'upload' || phase === 'live')) {
      startCameraStream();
    } else if (inputMode === 'upload' && phase === 'upload') {
      stopCameraStream();
    }
  }, [inputMode, phase, startCameraStream, stopCameraStream]);

  useEffect(() => {
    return () => {
      stopFrameCapture();
      stopCameraStream();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (frameUrlRef.current) {
        URL.revokeObjectURL(frameUrlRef.current);
      }
    };
  }, [stopCameraStream, stopFrameCapture]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setError(null);
  };

  const finishSession = async (reps: number, good: number, bad: number, sessionId: string | null) => {
    stopFrameCapture();
    stopCameraStream();
    setPhase('complete');
    setResult({ reps, good, bad });
    if (frameUrlRef.current) {
      URL.revokeObjectURL(frameUrlRef.current);
      frameUrlRef.current = null;
    }
    setFrameUrl(null);

    const activeSessionId = sessionId ?? cvSessionId;
    if (activeSessionId) {
      try {
        const fullReport = await getLiveSessionReport(activeSessionId);
        setReport(fullReport);
      } catch {
        // Fall back to live numbers
      }
    }
  };

  const startFrameLoop = (ws: WebSocket) => {
    const sendFrame = () => {
      if (ws.readyState !== WebSocket.OPEN) return;
      const video = videoRef.current;
      if (!video || video.paused || video.ended || video.readyState < 2) return;

      if (!canvasRef.current) {
        canvasRef.current = document.createElement('canvas');
      }
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      try {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          (blob) => {
            if (blob && ws.readyState === WebSocket.OPEN) {
              ws.send(blob);
            }
          },
          'image/jpeg',
          0.7
        );
      } catch {
        // ignore frame capture error
      }
    };

    stopFrameCapture();
    // Send immediate first frame
    sendFrame();
    // Run interval loop at ~10 FPS
    frameIntervalRef.current = window.setInterval(sendFrame, 100);
  };

  const startLiveSession = (target: { mode: 'video'; videoId: string } | { mode: 'camera' }) => {
    const wsUrl = getLiveSessionWebSocketUrl(exercise, target);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = 'blob';

    ws.onopen = () => {
      setPhase('live');
      setUploading(false);
      if (target.mode === 'camera') {
        startFrameLoop(ws);
      }
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'state' || payload.type === 'state_update') {
            const nextState: LiveState = {
              reps: payload.reps ?? liveStateRef.current.reps,
              good: payload.good ?? liveStateRef.current.good,
              bad: payload.bad ?? liveStateRef.current.bad,
              feedback: payload.feedback ?? liveStateRef.current.feedback,
            };
            liveStateRef.current = nextState;
            setLiveState(nextState);
          } else if (payload.type === 'end' || payload.type === 'complete') {
            const r = payload.reps ?? liveStateRef.current.reps;
            const g = payload.good ?? liveStateRef.current.good;
            const b = payload.bad ?? liveStateRef.current.bad;
            const sId = payload.session_id ?? null;
            if (sId) setCvSessionId(sId);
            finishSession(r, g, b, sId);
          } else if (payload.type === 'error') {
            stopFrameCapture();
            stopCameraStream();
            setError(payload.message ?? 'Computer Vision analysis error');
            setPhase('error');
            setUploading(false);
          }
        } catch {
          // ignore non-json messages
        }
      } else if (event.data instanceof Blob) {
        if (phaseRef.current === 'live') {
          if (frameUrlRef.current) {
            URL.revokeObjectURL(frameUrlRef.current);
          }
          const url = URL.createObjectURL(event.data);
          frameUrlRef.current = url;
          setFrameUrl(url);
        }
      }
    };

    ws.onerror = () => {
      stopFrameCapture();
      stopCameraStream();
      setError('Connection to Computer Vision WebSocket engine failed.');
      setPhase('error');
      setUploading(false);
    };

    ws.onclose = () => {
      stopFrameCapture();
      if (phaseRef.current === 'live') {
        const { reps, good, bad } = liveStateRef.current;
        finishSession(reps, good, bad, null);
      }
    };
  };

  const handleStartVideoAnalysis = async () => {
    if (!file) return;
    setError(null);
    setUploading(true);

    try {
      const resp = await uploadLiveSessionVideo(file);
      setCvSessionId(resp.id);
      startLiveSession({ mode: 'video', videoId: resp.id });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload video');
      setUploading(false);
    }
  };

  const handleStartCameraAnalysis = () => {
    if (!cameraReady) {
      setError('Camera is not ready. Please enable camera permission first.');
      return;
    }
    setError(null);
    setUploading(true);
    startLiveSession({ mode: 'camera' });
  };

  const handleEndSession = () => {
    stopFrameCapture();
    stopCameraStream();
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ action: 'stop' }));
      } catch {
        // ignore
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    const { reps, good, bad } = liveStateRef.current;
    finishSession(reps, good, bad, null);
  };

  const handleRetry = () => {
    stopFrameCapture();
    stopCameraStream();
    setPhase('upload');
    setError(null);
    setCameraError(null);
    setFile(null);
    setLiveState(INITIAL_LIVE_STATE);
    setResult(null);
    setCvSessionId(null);
    setReport(null);
    if (inputMode === 'camera') {
      startCameraStream();
    }
  };

  const activeExerciseName = AVAILABLE_EXERCISES.find((e) => e.id === exercise)?.name ?? exercise;

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-dark)',
        padding: 'clamp(24px, 4vw, 48px) clamp(16px, 3vw, 24px)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Persistent Hidden/Active Video Element to maintain MediaStream across phases */}
      <div
        style={{
          position: 'fixed',
          top: '-9999px',
          left: '-9999px',
          width: '1px',
          height: '1px',
          opacity: 0,
          pointerEvents: 'none',
        }}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ width: '640px', height: '480px' }}
        />
      </div>

      <div style={{ maxWidth: '760px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '9999px', background: 'var(--accent-primary-muted)', border: '1px solid rgba(16, 185, 129, 0.4)', marginBottom: '12px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--category-motion)', boxShadow: '0 0 10px var(--category-motion)' }} />
            <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--category-motion)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{t('liveSession.badge')}</span>
          </div>
          <h1 style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '6px' }}>
            {t('liveSession.title')} — {activeExerciseName}
          </h1>
          <p style={{ color: 'var(--text-body)', fontSize: '13px', margin: 0 }}>
            {t('liveSession.subtitle')}
          </p>
        </div>

        {/* Phase Panels */}
        {phase === 'upload' && (
          <div className="glass-panel" style={{ padding: 'clamp(24px, 5vw, 36px)', textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            {/* Mode Switcher Tabs */}
            <div
              style={{
                display: 'flex',
                background: 'var(--bg-input)',
                padding: '4px',
                borderRadius: '12px',
                border: '1px solid var(--border)',
                marginBottom: '24px',
                gap: '4px',
              }}
            >
              <button
                id="live-session-mode-upload"
                type="button"
                onClick={() => setInputMode('upload')}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: inputMode === 'upload' ? 'var(--accent-primary)' : 'transparent',
                  color: inputMode === 'upload' ? 'var(--text-on-accent)' : 'var(--text-body)',
                  fontWeight: 800,
                  fontSize: '13px',
                  cursor: 'pointer',
                  boxShadow: inputMode === 'upload' ? '0 0 14px var(--accent-primary-glow)' : 'none',
                  transition: 'all 0.2s',
                }}
              >
                {t('liveSession.mode.upload')}
              </button>
              <button
                id="live-session-mode-camera"
                type="button"
                onClick={() => setInputMode('camera')}
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: inputMode === 'camera' ? 'var(--accent-primary)' : 'transparent',
                  color: inputMode === 'camera' ? 'var(--text-on-accent)' : 'var(--text-body)',
                  fontWeight: 800,
                  fontSize: '13px',
                  cursor: 'pointer',
                  boxShadow: inputMode === 'camera' ? '0 0 14px var(--accent-primary-glow)' : 'none',
                  transition: 'all 0.2s',
                }}
              >
                {t('liveSession.mode.camera')}
              </button>
            </div>

            {/* Exercise Selector */}
            <div style={{ marginBottom: '20px', textAlign: 'left' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                {t('liveSession.selectExercise')}
              </label>
              <select
                id="live-session-exercise-select"
                value={exercise}
                onChange={(e) => {
                  setExercise(e.target.value);
                  setSearchParams({ exercise: e.target.value });
                }}
                className="form-input"
                style={{ width: '100%', padding: '10px 12px', borderRadius: '8px' }}
              >
                {AVAILABLE_EXERCISES.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Upload Video Mode */}
            {inputMode === 'upload' && (
              <div>
                <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'var(--accent-primary-muted)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '24px', border: '1px solid var(--accent-primary)', boxShadow: '0 0 20px var(--accent-primary-glow)' }}>
                  📹
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
                  {t('liveSession.upload.title')}
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-body)', marginBottom: '20px' }}>
                  {t('liveSession.upload.body')}
                </p>

                <input id="live-session-file-input" type="file" accept="video/*" onChange={handleFileChange} className="form-input" style={{ marginBottom: '16px' }} />

                {error && <p style={{ color: 'var(--status-error)', fontSize: '13px', marginBottom: '16px' }}>⚠️ {error}</p>}

                <button
                  id="live-session-start-btn"
                  onClick={handleStartVideoAnalysis}
                  disabled={!file || uploading}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '14px', fontSize: '14px' }}
                >
                  {uploading ? t('liveSession.analyzing') : t('liveSession.startAnalysis')}
                </button>
              </div>
            )}

            {/* Live Camera Mode */}
            {inputMode === 'camera' && (
              <div>
                <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--category-motion)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '24px', border: '1px solid var(--category-motion)', boxShadow: '0 0 20px rgba(245, 158, 11, 0.25)' }}>
                  📷
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
                  {t('liveSession.camera.title')}
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-body)', marginBottom: '20px' }}>
                  {t('liveSession.camera.body')}
                </p>

                {/* Camera Live Preview Element */}
                <div
                  style={{
                    position: 'relative',
                    width: '100%',
                    maxWidth: '480px',
                    margin: '0 auto 20px',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    background: '#050c24',
                    border: '1px solid var(--border)',
                    boxShadow: '0 0 20px rgba(0, 0, 0, 0.5)',
                  }}
                >
                  <video
                    ref={(el) => {
                      if (el && mediaStreamRef.current && el.srcObject !== mediaStreamRef.current) {
                        el.srcObject = mediaStreamRef.current;
                        el.play().catch(() => {});
                      }
                    }}
                    autoPlay
                    playsInline
                    muted
                    style={{
                      width: '100%',
                      height: 'auto',
                      display: 'block',
                      transform: 'scaleX(-1)', // Mirror webcam for natural user experience
                    }}
                  />

                  {cameraReady && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '12px',
                        left: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        background: 'rgba(5, 12, 36, 0.75)',
                        padding: '4px 10px',
                        borderRadius: '9999px',
                        border: '1px solid var(--accent-primary)',
                      }}
                    >
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-primary)', boxShadow: '0 0 8px var(--accent-primary)' }} />
                      <span style={{ fontSize: '11px', color: 'var(--text-heading)', fontWeight: 700 }}>
                        {t('liveSession.camera.active')}
                      </span>
                    </div>
                  )}

                  {!cameraReady && !cameraError && (
                    <div style={{ padding: '40px 20px', color: 'var(--text-muted)', fontSize: '13px' }}>
                      Initializing camera stream...
                    </div>
                  )}
                </div>

                {cameraError && (
                  <div style={{ marginBottom: '16px', padding: '12px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--status-error)', fontSize: '13px' }}>
                    ⚠️ {cameraError}
                    <div style={{ marginTop: '8px' }}>
                      <button
                        type="button"
                        onClick={startCameraStream}
                        className="btn btn-secondary"
                        style={{ padding: '6px 14px', fontSize: '12px' }}
                      >
                        {t('liveSession.camera.retry')}
                      </button>
                    </div>
                  </div>
                )}

                {error && <p style={{ color: 'var(--status-error)', fontSize: '13px', marginBottom: '16px' }}>⚠️ {error}</p>}

                <button
                  id="live-session-start-camera-btn"
                  onClick={handleStartCameraAnalysis}
                  disabled={!cameraReady || uploading}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '14px', fontSize: '14px' }}
                >
                  {uploading ? t('liveSession.analyzing') : t('liveSession.startCameraAnalysis')}
                </button>
              </div>
            )}
          </div>
        )}

        {phase === 'live' && (
          <div className="glass-panel" style={{ padding: 'clamp(16px, 3vw, 24px)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            {/* Annotated Stream Frame */}
            {frameUrl ? (
              <img
                id="live-session-frame"
                src={frameUrl}
                alt="Live camera view"
                style={{ width: '100%', borderRadius: '12px', marginBottom: '20px', border: '1px solid var(--category-motion)', boxShadow: '0 0 30px rgba(245, 158, 11, 0.2)' }}
              />
            ) : (
              <div style={{ width: '100%', height: '260px', background: 'var(--bg-input)', borderRadius: '12px', marginBottom: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '12px' }}>
                <div style={{ width: '32px', height: '32px', border: '3px solid var(--category-motion)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                <span>{t('liveSession.analyzing')}</span>
              </div>
            )}

            {/* Rep Counter HUD Bar */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '18px' }}>
              <div className="glass-panel" style={{ padding: '10px', textAlign: 'center', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>{t('liveSession.totalReps')}</span>
                <p id="live-session-reps" className="metric-val" style={{ fontSize: '20px', color: 'var(--text-heading)', margin: '2px 0 0 0' }}>{liveState.reps}</p>
              </div>
              <div className="glass-panel" style={{ padding: '10px', textAlign: 'center', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>{t('liveSession.perfectReps')}</span>
                <p id="live-session-good" className="metric-val" style={{ fontSize: '20px', color: 'var(--accent-primary)', margin: '2px 0 0 0' }}>{liveState.good}</p>
              </div>
              <div className="glass-panel" style={{ padding: '10px', textAlign: 'center', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>{t('liveSession.formBreak')}</span>
                <p id="live-session-bad" className="metric-val" style={{ fontSize: '20px', color: 'var(--status-error)', margin: '2px 0 0 0' }}>{liveState.bad}</p>
              </div>
            </div>

            {liveState.feedback.length > 0 && (
              <div style={{ background: 'var(--accent-primary-muted)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '10px', padding: '14px', marginBottom: '18px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--accent-primary)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                  {t('liveSession.liveFeedback')}
                </span>
                {liveState.feedback.map((message, i) => (
                  <p key={i} style={{ fontSize: '13px', color: 'var(--text-heading)', margin: 0 }}>✓ {message}</p>
                ))}
              </div>
            )}

            <button id="live-session-end-btn" onClick={handleEndSession} className="btn btn-secondary" style={{ width: '100%', borderColor: 'rgba(239, 68, 68, 0.4)', color: 'var(--status-error)' }}>
              {t('liveSession.endSession')}
            </button>
          </div>
        )}

        {phase === 'complete' && result && (
          <div className="glass-panel" style={{ padding: 'clamp(24px, 5vw, 36px)', textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'var(--accent-primary-muted)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '24px', border: '1px solid var(--accent-primary)', boxShadow: '0 0 20px var(--accent-primary-glow)' }}>
              🎯
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
              {t('liveSession.complete.title')}
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '20px' }}>
              <div className="glass-panel" style={{ padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('liveSession.totalReps')}</span>
                <p id="live-session-final-reps" className="metric-val" style={{ fontSize: '20px', color: 'var(--text-heading)', margin: '2px 0 0 0' }}>{result.reps}</p>
              </div>
              <div className="glass-panel" style={{ padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('liveSession.complete.goodReps')}</span>
                <p style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-primary)', margin: '2px 0 0 0' }}>{result.good}</p>
              </div>
              <div className="glass-panel" style={{ padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('liveSession.complete.badReps')}</span>
                <p style={{ fontSize: '20px', fontWeight: 700, color: 'var(--status-error)', margin: '2px 0 0 0' }}>{result.bad}</p>
              </div>
            </div>

            {report && <SessionReportView report={report} />}

            <a href="/exercises" id="live-session-back-link" className="btn btn-primary" style={{ display: 'inline-flex', marginTop: '20px', textDecoration: 'none' }}>
              {t('liveSession.complete.return')}
            </a>
          </div>
        )}

        {phase === 'error' && (
          <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
            <p style={{ color: '#ff80ab', fontSize: '14px', marginBottom: '18px' }}>⚠️ {error}</p>
            <button id="live-session-retry-btn" onClick={handleRetry} className="btn btn-primary">
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveSession;
