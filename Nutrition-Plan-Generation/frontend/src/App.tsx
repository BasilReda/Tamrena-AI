import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ProfileForm } from './components/ProfileForm';
import { GraphProgress } from './components/GraphProgress';
import { PlanDisplay } from './components/PlanDisplay';
import type { GenerateNutritionRequest, StreamEvent, NutritionPlanResponse } from './types';
import { AlertCircle, RefreshCw } from 'lucide-react';
import './index.css';

export const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [planData, setPlanData] = useState<NutritionPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGraphComplete, setIsGraphComplete] = useState(false);

  const fetchFinalResult = async (runId: string, retries = 8): Promise<boolean> => {
    for (let i = 0; i < retries; i++) {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/nutrition/result/${runId}`);
        if (res.ok) {
          const data: NutritionPlanResponse = await res.json();
          if (data.meal_plan) {
            setPlanData(data);
            setIsGraphComplete(true);
            setIsLoading(false);
            setError(null);
            return true;
          }
        }
        if (res.status !== 404 && !res.ok) {
          throw new Error('Failed to fetch final nutrition plan.');
        }
      } catch (err: any) {
        if (i === retries - 1) {
          setError(err.message || 'Error fetching result');
          setIsLoading(false);
        }
      }
      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, 600));
    }
    return false;
  };

  const handleStartGeneration = async (request: GenerateNutritionRequest) => {
    setIsLoading(true);
    setError(null);
    setPlanData(null);
    setStreamEvents([]);
    setIsGraphComplete(false);
    setActiveRunId(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/nutrition/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Server error initiating nutrition generation');
      }

      const resData = await response.json();
      const runId = resData.run_id;
      setActiveRunId(runId);

      // Connect to SSE stream
      const eventSource = new EventSource(`http://localhost:8000/api/v1/nutrition/stream/${runId}`);

      eventSource.onmessage = (event) => {
        try {
          const parsed: StreamEvent = JSON.parse(event.data);
          setStreamEvents((prev) => [...prev, parsed]);

          if (parsed.status === 'error' || parsed.status === 'failed') {
            setError((parsed as any).reason || parsed.data?.message || 'Error reported by LangGraph node.');
            eventSource.close();
            setIsLoading(false);
          }

          if (parsed.node === 'workflow' && parsed.status === 'completed') {
            eventSource.close();
            fetchFinalResult(runId);
          } else if (parsed.node === 'explain' && parsed.status === 'completed') {
            // Proactively try fetching result once explain finishes
            fetchFinalResult(runId);
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        // Fallback check if SSE closed
        setTimeout(() => {
          if (!planData && !isGraphComplete) fetchFinalResult(runId);
        }, 1000);
      };

    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during generation.');
      setIsLoading(false);
    }
  };

  // Check if activeRunId completes via fallback polling if stream missed anything
  useEffect(() => {
    if (!activeRunId || isGraphComplete) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/nutrition/result/${activeRunId}`);
        if (res.ok) {
          const data: NutritionPlanResponse = await res.json();
          if (data.meal_plan && data.explanation) {
            setPlanData(data);
            setIsGraphComplete(true);
            setIsLoading(false);
            setError(null);
            clearInterval(interval);
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeRunId, isGraphComplete]);

  return (
    <div className="app-container">
      <Header />

      {/* Left Column: Patient Profile & Biometrics Form */}
      <div>
        <ProfileForm onSubmit={handleStartGeneration} isLoading={isLoading} />
      </div>

      {/* Right Column: Live Graph Execution Monitor & Generated Plan */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {error && (
          <div className="glass-card fade-in" style={{
            padding: '20px',
            background: 'rgba(244, 63, 94, 0.15)',
            borderColor: 'rgba(244, 63, 94, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AlertCircle size={28} color="#fb7185" />
              <div>
                <h4 style={{ color: '#fb7185', fontSize: '1.1rem' }}>LangGraph Pipeline Error</h4>
                <p style={{ fontSize: '0.9rem', color: '#fecdd3', marginTop: '4px' }}>{error}</p>
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              className="btn btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <RefreshCw size={14} /> Dismiss
            </button>
          </div>
        )}

        {/* Always display the Graph Progress Tracker if a run started */}
        {(activeRunId || isLoading || streamEvents.length > 0) && (
          <GraphProgress
            events={streamEvents}
            activeRunId={activeRunId}
            isComplete={isGraphComplete}
            hasError={!!error}
          />
        )}

        {/* Display Final Plan once completed */}
        {planData && isGraphComplete && (
          <PlanDisplay planData={planData} />
        )}

        {/* Welcome Placeholder state if nothing started yet */}
        {!activeRunId && !isLoading && !planData && !error && (
          <div className="glass-card fade-in" style={{
            padding: '48px 32px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(139, 92, 246, 0.2))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px',
              color: '#34d399',
              boxShadow: '0 0 30px rgba(16, 185, 129, 0.2)'
            }}>
              <span style={{ fontSize: '2rem' }}>🥗</span>
            </div>
            <h3 style={{ fontSize: '1.6rem', marginBottom: '10px' }}>
              Ready to Run <span className="gradient-text">Clinical Multi-Agent Pipeline</span>
            </h3>
            <p style={{ maxWidth: '480px', color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: '1.6' }}>
              Fill in the patient biometrics on the left or click one of the ⚡ <b>One-Click Demo Profiles</b> to instantly generate a medically validated, macro-targeted Egyptian daily meal plan.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
