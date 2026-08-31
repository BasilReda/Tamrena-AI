import { useState } from 'react';

interface PipelineNode {
  id: number;
  title: string;
  role: string;
  inputs: string;
  outputPreview: string;
  egyptianHighlight: string;
  agentLogic: string;
}

const NODES: PipelineNode[] = [
  {
    id: 1,
    title: '1. Hunter Profile & Intake',
    role: 'Biometric & Goal Extraction',
    inputs: 'Age: 26, Weight: 82kg, Height: 180cm, Activity: High, Goal: Lean Hypertrophy',
    outputPreview: 'User Profile Context & Regional Preference = Egyptian Mediterranean',
    egyptianHighlight: 'Extracts preferred Egyptian breakfast patterns, fasting preferences, and local grocery staples.',
    agentLogic: 'Parses raw user input, normalizes target weight delta, and constructs the LangGraph system state graph.',
  },
  {
    id: 2,
    title: '2. BMR & TDEE Calculators',
    role: 'Metabolic Energy Equation Node',
    inputs: 'Mifflin-St Jeor Equation + Activity Multiplier 1.55',
    outputPreview: 'BMR: 1,840 kcal | TDEE: 2,852 kcal | Target Caloric Intake: 2,550 kcal (Surplus/Deficit tuned)',
    egyptianHighlight: 'Accounts for regional heat dissipation, physical exertion, and gym training split.',
    agentLogic: 'Executes deterministic scientific equations rather than probabilistic LLM hallucinations.',
  },
  {
    id: 3,
    title: '3. Macro Ratio Distribution',
    role: 'Macronutrient Partitioning Engine',
    inputs: 'Target: 2,550 kcal | Protein: 2.2g/kg (180g) | Fat: 0.9g/kg (74g) | Carbs: 290g',
    outputPreview: 'P: 180g (720 kcal) | C: 290g (1160 kcal) | F: 74g (670 kcal)',
    egyptianHighlight: 'Structures high-protein Egyptian distributions without relying exclusively on expensive imported powders.',
    agentLogic: 'Partitions total energy into muscle protein synthesis (MPS) thresholds across 4 daily meals.',
  },
  {
    id: 4,
    title: '4. Egyptian Food Retrieval',
    role: 'Semantic Food Database Vector Retrieval',
    inputs: 'Egyptian Nutrition Database + USDA verified macro records',
    outputPreview: 'Retrieved: Foul Medames with Olive Oil, Baladi Bread, Grilled Chicken Breast, Basmati Rice, Lentil Soup',
    egyptianHighlight: 'Authentic local dishes with exact oil/fava-bean/tahini/whole-wheat Baladi bread ratios.',
    agentLogic: 'Vector search retrieves ingredients matching macro densities and user satiety preferences.',
  },
  {
    id: 5,
    title: '5. Meal Composition Agent',
    role: 'Multi-Meal Combinatorial Assembly',
    inputs: 'Meals: Breakfast (25%), Lunch (35%), Pre/Post-Workout (20%), Dinner (20%)',
    outputPreview: 'Breakfast: 200g Foul + 1 Baladi Bread + 3 Eggs + 10g Olive Oil (680 kcal, 42g P, 65g C, 28g F)',
    egyptianHighlight: 'Builds delicious, culturally familiar meals that fit precise fitness macros seamlessly.',
    agentLogic: 'Optimizes portion sizes to hit target grams per meal while preserving culinary coherence.',
  },
  {
    id: 6,
    title: '6. Validation & Guardrail Loop',
    role: 'Self-Correction & Tolerance Verification',
    inputs: 'Sum Check: Actual 2,540 kcal vs Target 2,550 kcal (Delta: -0.39% — Within ±1.5% margin)',
    outputPreview: 'Status: PASSED (Zero hallucination, micro-nutrient RDA fulfilled, protein minimum met)',
    egyptianHighlight: 'Ensures sodium & healthy fats from olive oil and sesame tahini stay balanced.',
    agentLogic: 'If tolerance fails, triggers feedback edge back to Meal Composition to adjust portion weights automatically.',
  },
  {
    id: 7,
    title: '7. Explainable Nutrition Reasoner',
    role: 'Natural Language Transparency & Coaching',
    inputs: 'Validated Meal Plan + User Profile Goals',
    outputPreview: '"This meal plan provides 180g protein timed around your workout for optimal MPS recovery..."',
    egyptianHighlight: 'Delivers clear explanations in English & Arabic explaining why Egyptian complex carbs fuel performance.',
    agentLogic: 'Generates transparent scientific rationale with Groq LLM streaming via Server-Sent Events (SSE).',
  },
];

export default function LangGraphPipelineDemo() {
  const [activeNodeId, setActiveNodeId] = useState<number>(4);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const activeNode = NODES.find((n) => n.id === activeNodeId) || NODES[0];

  const handleSimulate = () => {
    setIsSimulating(true);
    let step = 1;
    const interval = setInterval(() => {
      setActiveNodeId(step);
      step++;
      if (step > NODES.length) {
        clearInterval(interval);
        setIsSimulating(false);
      }
    }, 900);
  };

  return (
    <div
      className="glass-panel pipeline-demo-container"
      style={{
        padding: 'clamp(18px, 4vw, 32px)',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '24px',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '18px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-primary">LangGraph & Groq Multi-Agent</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>SSE Streaming & Self-Correction</span>
          </div>
          <h3 style={{ fontSize: 'clamp(18px, 3vw, 22px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
            7-Node Egyptian Nutrition Intelligence
          </h3>
        </div>

        <button
          type="button"
          disabled={isSimulating}
          onClick={handleSimulate}
          className="btn btn-primary"
          style={{ padding: '10px 22px', fontSize: '13px' }}
        >
          {isSimulating ? (
            <>
              <span>⚙</span>
              <span>Executing Node {activeNodeId}/7...</span>
            </>
          ) : (
            <>
              <span>▶ Run Pipeline Flow</span>
            </>
          )}
        </button>
      </div>

      {/* Horizontal Step Pipeline Track */}
      <div
        className="pipeline-nodes-track"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '8px',
          marginBottom: '28px',
        }}
      >
        {NODES.map((node) => {
          const isActive = node.id === activeNodeId;
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => setActiveNodeId(node.id)}
              style={{
                background: isActive ? 'var(--accent-primary-muted)' : 'var(--bg-input)',
                border: `1px solid ${isActive ? 'var(--accent-primary)' : 'var(--border)'}`,
                borderRadius: '10px',
                padding: '12px 10px',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative',
                boxShadow: isActive ? '0 0 15px var(--accent-primary-glow)' : 'none',
                minWidth: '110px',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  marginBottom: '4px',
                }}
              >
                NODE 0{node.id}
              </div>
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: isActive ? 'var(--text-heading)' : 'var(--text-body)',
                  lineHeight: 1.3,
                }}
              >
                {node.title.split('. ')[1]}
              </div>
            </button>
          );
        })}
      </div>

      {/* Node Deep Dive Details Card */}
      <div
        className="pipeline-details-grid"
        style={{
          background: 'var(--bg-input)',
          border: '1px solid var(--border)',
          borderRadius: '14px',
          padding: 'clamp(16px, 3vw, 24px)',
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr',
          gap: '24px',
        }}
      >
        {/* Left Side: Agent Logic & Calculations */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                background: 'var(--accent-primary)',
                color: 'var(--text-on-accent)',
                fontSize: '14px',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 10px var(--accent-primary-glow)',
              }}
            >
              {activeNode.id}
            </div>
            <div>
              <h4 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                {activeNode.title}
              </h4>
              <p style={{ fontSize: '12px', color: 'var(--accent-primary)', margin: 0, fontWeight: 700 }}>
                Role: {activeNode.role}
              </p>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
              Execution & Guardrail Logic
            </span>
            <p style={{ fontSize: '14px', color: 'var(--text-body)', marginTop: '4px', lineHeight: 1.6 }}>
              {activeNode.agentLogic}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
              Inputs & Parameters
            </span>
            <div
              style={{
                marginTop: '6px',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                color: 'var(--text-body)',
                wordBreak: 'break-word',
              }}
            >
              {activeNode.inputs}
            </div>
          </div>
        </div>

        {/* Right Side: Output Telemetry & Egyptian Cuisine Integration */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Egyptian Cuisine Callout */}
          <div
            style={{
              padding: '14px 16px',
              borderRadius: '10px',
              background: 'var(--accent-primary-muted)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--category-nutrition)', fontSize: '12px', fontWeight: 800, marginBottom: '6px' }}>
              <span>🇪🇬</span> Egyptian Nutrition Specialty
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-heading)', margin: 0, lineHeight: 1.5 }}>
              {activeNode.egyptianHighlight}
            </p>
          </div>

          {/* Node Output Preview Console */}
          <div
            style={{
              flex: 1,
              padding: '14px 16px',
              borderRadius: '10px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--accent-primary)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>⚡</span> Node Output State
            </span>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '13px',
                color: 'var(--category-nutrition)',
                lineHeight: 1.5,
                wordBreak: 'break-word',
              }}
            >
              {activeNode.outputPreview}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .pipeline-details-grid {
            grid-template-columns: 1fr !important;
          }
          .pipeline-nodes-track {
            display: flex !important;
            overflow-x: auto !important;
            padding-bottom: 8px !important;
            -webkit-overflow-scrolling: touch !important;
          }
        }
      `}</style>
    </div>
  );
}
