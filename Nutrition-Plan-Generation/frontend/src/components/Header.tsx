import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Sparkles, Cpu } from 'lucide-react';

export const Header: React.FC = () => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#34d399',
          boxShadow: '0 0 20px rgba(16, 185, 129, 0.25)'
        }}>
          <Activity size={24} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.5rem', lineHeight: '1.2' }}>
            Nutri<span className="gradient-text">Graph</span> AI
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Multi-Agent Clinical Nutrition System &bull; LangGraph &bull; Groq Llama 3.3
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <div className="badge badge-cyan">
          <Cpu size={14} />
          <span>7-Node Stateful Graph</span>
        </div>
        <div className="badge badge-violet">
          <Sparkles size={14} />
          <span>LangSmith Tracing</span>
        </div>
        <div className={`badge ${backendOnline ? 'badge-green' : 'badge-violet'}`} style={{
          borderColor: backendOnline ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.4)',
          background: backendOnline ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          color: backendOnline ? '#34d399' : '#fb7185'
        }}>
          <ShieldCheck size={14} />
          <span>FastAPI: {backendOnline === null ? 'Checking...' : backendOnline ? 'Online ✓' : 'Offline ✗'}</span>
        </div>
      </div>
    </header>
  );
};
