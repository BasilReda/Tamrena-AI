import React from 'react';
import type { StreamEvent } from '../types';
import { CheckCircle2, Loader2, Cpu, ArrowDown, ShieldCheck, Sparkles, Calculator, Database, Utensils, Bot, Layers } from 'lucide-react';

interface GraphProgressProps {
  events: StreamEvent[];
  activeRunId: string | null;
  isComplete: boolean;
  hasError: boolean;
}

// ── Shared nodes (always present) ────────────────────────────────────────────
const SHARED_NODES = [
  { id: 'profile',   label: '1. Profile Agent (LLM Node)',  desc: 'Normalises biometrics & clinical goals via LLM',        icon: Cpu },
  { id: 'calories',  label: '2. Calories Calculator',        desc: 'Deterministic Mifflin-St Jeor BMR & TDEE formula',      icon: Calculator },
  { id: 'macros',    label: '3. Macro Calculator',           desc: 'Computes target Protein, Carbs & Fat splits',           icon: Calculator },
];

// ── Mode-specific pipeline nodes ──────────────────────────────────────────────
const DATASET_NODES = [
  { id: 'retrieve_foods', label: '4. Food Retrieval Layer',     desc: 'Filters allergens & ranks Egyptian foods by preference', icon: Database },
  { id: 'compose_meal',   label: '5. Meal Composition Agent',   desc: 'LLM synthesizes 4 balanced meals meeting macros',        icon: Utensils },
];

const LLM_ARABIC_NODES = [
  { id: 'meal_distributor',         label: '4. Meal Distributor',                desc: 'Splits daily macros into per-slot budgets (B/L/D/S)',             icon: Calculator },
  { id: 'compose_meals_iterative',  label: '5. Iterative Arabic Agent (3×4 LLM)', desc: 'Fires 3 LLM calls per slot → 3 Arabic meal plan options',        icon: Bot },
];

const PARQUET_NODES = [
  { id: 'meal_distributor',               label: '4. Meal Distributor',                  desc: 'Splits daily macros into per-slot budgets',                              icon: Calculator },
  { id: 'compose_meals_parquet_arabic',   label: '5. Parquet Retrieval + Arabic LLM',    desc: 'Fetches real foods from parquet per slot → 3 Arabic LLM options',        icon: Layers },
];

// ── Shared tail nodes ─────────────────────────────────────────────────────────
const TAIL_NODES = [
  { id: 'validate', label: '6. Validation Engine',    desc: 'Checks ±10% calorie/protein targets & allergen safety', icon: ShieldCheck },
  { id: 'explain',  label: '7. Explanation Agent',    desc: 'Generates clinical rationale & human guidance',          icon: Sparkles },
];

/** Detect which pipeline mode is running from the event stream node IDs. */
function detectMode(events: StreamEvent[]): 'dataset' | 'llm_arabic' | 'llm_arabic_parquet' {
  for (const e of events) {
    if (e.node === 'compose_meals_parquet_arabic') return 'llm_arabic_parquet';
    if (e.node === 'compose_meals_iterative') return 'llm_arabic';
  }
  return 'dataset'; // default until we see mode-specific events
}

export const GraphProgress: React.FC<GraphProgressProps> = ({ events, activeRunId, isComplete, hasError }) => {
  const detectedMode = detectMode(events);

  const modeNodes = detectedMode === 'llm_arabic_parquet'
    ? PARQUET_NODES
    : detectedMode === 'llm_arabic'
      ? LLM_ARABIC_NODES
      : DATASET_NODES;

  const ALL_NODES = [...SHARED_NODES, ...modeNodes, ...TAIL_NODES];

  const getStatus = (nodeId: string) => {
    if (isComplete) return 'completed';
    for (let i = events.length - 1; i >= 0; i--) {
      if (events[i].node === nodeId) {
        if (events[i].status === 'started') return hasError ? 'error' : 'active';
        if (events[i].status === 'completed') return 'completed';
        if (events[i].status === 'failed' || events[i].status === 'error') return 'error';
      }
    }
    return 'pending';
  };

  /** Color theme per mode */
  const modeAccent =
    detectedMode === 'llm_arabic_parquet' ? '#fbbf24' :
    detectedMode === 'llm_arabic'         ? '#a78bfa' :
    '#34d399';

  const modeBadge =
    detectedMode === 'llm_arabic_parquet' ? '🗄️ Parquet + Arabic LLM' :
    detectedMode === 'llm_arabic'         ? '🇪🇬 LLM Arabic (Free-form)' :
    '📊 Dataset Mode';

  return (
    <div className="glass-card" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} className="gradient-text" /> LangGraph Execution Monitor
          </h2>
          {activeRunId && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'monospace' }}>
              Run ID: {activeRunId}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
          {isComplete ? (
            <span className="badge badge-green">Pipeline Completed ✓</span>
          ) : activeRunId ? (
            <span className="badge badge-cyan animate-pulse">Streaming Live Graphs...</span>
          ) : (
            <span className="badge badge-violet">Ready for Execution</span>
          )}
          {/* Mode indicator — only shown once we detect the mode from events */}
          {events.length > 0 && (
            <span style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '2px 9px',
              borderRadius: '20px',
              color: modeAccent,
              background: `${modeAccent}18`,
              border: `1px solid ${modeAccent}40`,
            }}>
              {modeBadge}
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {ALL_NODES.map((node, index) => {
          const status = getStatus(node.id);
          const IconComponent = node.icon;

          // Per-node accent color: parquet node gets amber, arabic node gets violet
          const activeColor =
            (node.id === 'compose_meals_parquet_arabic') ? '#fbbf24' :
            (node.id === 'compose_meals_iterative')       ? '#a78bfa' :
            '#34d399';
          const activeBorder =
            (node.id === 'compose_meals_parquet_arabic') ? 'rgba(245,158,11,0.5)' :
            (node.id === 'compose_meals_iterative')       ? 'rgba(139,92,246,0.5)' :
            'rgba(16, 185, 129, 0.5)';
          const activeBg =
            (node.id === 'compose_meals_parquet_arabic') ? 'rgba(245,158,11,0.1)' :
            (node.id === 'compose_meals_iterative')       ? 'rgba(139,92,246,0.1)' :
            'rgba(16, 185, 129, 0.1)';

          return (
            <React.Fragment key={node.id}>
              <div className={`node-item ${status}`} style={{
                border: status === 'active'
                  ? `1px solid ${activeBorder}`
                  : status === 'completed' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid transparent',
                background: status === 'active'
                  ? activeBg
                  : status === 'completed' ? 'rgba(255, 255, 255, 0.04)' : 'rgba(255, 255, 255, 0.015)'
              }}>
                <div className="node-icon" style={{
                  background: status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : status === 'active' ? `${activeColor}22` : 'rgba(255, 255, 255, 0.05)',
                  color: status === 'completed' ? '#34d399' : status === 'active' ? activeColor : 'var(--text-dim)'
                }}>
                  {status === 'completed' ? (
                    <CheckCircle2 size={16} />
                  ) : status === 'active' ? (
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <IconComponent size={16} />
                  )}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    color: status === 'completed' ? '#f8fafc' : status === 'active' ? activeColor : 'var(--text-muted)'
                  }}>
                    {node.label}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: status === 'active' ? '#cbd5e1' : 'var(--text-dim)' }}>
                    {node.desc}
                  </div>
                </div>

                {status === 'active' && (
                  <span className="badge animate-pulse" style={{
                    fontSize: '0.65rem',
                    background: `${activeColor}22`,
                    color: activeColor,
                    border: `1px solid ${activeColor}44`,
                    padding: '3px 8px',
                    borderRadius: '20px',
                    fontWeight: 700,
                  }}>
                    Executing...
                  </span>
                )}
                {status === 'completed' && (
                  <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>
                    Done
                  </span>
                )}
              </div>

              {index < ALL_NODES.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '-4px 0', opacity: 0.3 }}>
                  <ArrowDown size={14} color="var(--text-muted)" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Legend */}
      {events.length > 0 && detectedMode !== 'dataset' && (
        <div style={{
          marginTop: '16px',
          padding: '10px 14px',
          borderRadius: '10px',
          background: `${modeAccent}0d`,
          border: `1px solid ${modeAccent}30`,
          fontSize: '0.75rem',
          color: modeAccent,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          {detectedMode === 'llm_arabic_parquet' ? (
            <>
              <Layers size={14} />
              <span>Parquet pipeline: <strong>793 real foods</strong> filtered per meal slot → LLM generates <strong>3 Arabic option</strong> sets in parallel</span>
            </>
          ) : (
            <>
              <Bot size={14} />
              <span>Free-form Arabic pipeline: LLM generates <strong>3 diverse meal plan options</strong> per slot in parallel</span>
            </>
          )}
        </div>
      )}
    </div>
  );
};
