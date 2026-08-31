import { Link } from 'react-router-dom';

export default function AboutPage() {
  const principles = [
    {
      icon: '🔬',
      title: 'Thermodynamic & Kinematic Rigor',
      description:
        'We never let AI hallucinate calorie budgets or joint physics. Core metabolic math (Mifflin-St Jeor) and kinematic angle formulas run on deterministic equations, while LLMs and neural models handle semantic retrieval, explanation, and real-time vision.',
    },
    {
      icon: '⚡',
      title: 'Zero-Lag Real-Time Feedback',
      description:
        'Biomechanical form correction is useless if delayed. Our BlazePose computer-vision engine streams skeleton telemetry at 30 FPS over WebSockets, alerting athletes to knee valgus or spinal curvature before injury occurs.',
    },
    {
      icon: '🇪🇬',
      title: 'Egyptian Cultural Nutrition Alignment',
      description:
        'Fitness technology has historically ignored Middle Eastern culinary traditions. We built an authentic database of Egyptian meals (Foul, Koshari, Baladi bread, lentils, grilled meats) calibrated to exact macronutrient and micronutrient targets.',
    },
    {
      icon: '🛡️',
      title: 'Modular Microservice Architecture & Privacy',
      description:
        'Four independently deployable sibling services connected via a unified BFF and shared JWT authentication. User biometrics, DynamoDB workout states, and MongoDB records are securely isolated and encrypted.',
    },
  ];

  const milestones = [
    {
      year: 'Phase 1',
      title: 'Computer Vision AI-GYM Prototype',
      desc: 'Developed the first standalone BlazePose webcam pose tracker capable of real-time rep counting and joint angle computation.',
    },
    {
      year: 'Phase 2',
      title: 'Hunter Profile & Workout Engine',
      desc: 'Built the algorithmic Training Protocol generator and migrated user persistence to AWS DynamoDB with idempotent table management.',
    },
    {
      year: 'Phase 3',
      title: '7-Node LangGraph Egyptian Nutrition',
      desc: 'Architected the multi-agent nutrition pipeline with Groq, LangSmith, SSE streaming, and a self-correcting ±1.5% calorie validation loop.',
    },
    {
      year: 'Phase 4',
      title: 'Unified BFF & AWS ECS Deployment',
      desc: 'Integrated all 4 services behind Tamrena-AI, containerized Docker builds, and automated ECS task orchestration with shared JWT auth.',
    },
  ];

  return (
    <div style={{ position: 'relative' }}>
      {/* 1. HERO SECTION */}
      <section
        className="public-section"
        style={{
          paddingTop: 'clamp(36px, 6vw, 60px)',
          paddingBottom: 'clamp(36px, 6vw, 60px)',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '9999px',
            background: 'var(--accent-primary-muted)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            marginBottom: '20px',
          }}
        >
          <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Mission & Vision
          </span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(30px, 5vw, 56px)',
            fontWeight: 800,
            lineHeight: 1.15,
            letterSpacing: '-0.02em',
            color: 'var(--text-heading)',
            maxWidth: '900px',
            margin: '0 auto 20px',
          }}
        >
          Democratizing Elite Sports Science &{' '}
          <span className="gradient-text-emerald">Biomechanics Through AI</span>.
        </h1>

        <p
          style={{
            fontSize: 'clamp(15px, 2vw, 18px)',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            maxWidth: '740px',
            margin: '0 auto 40px',
          }}
        >
          Tamrena-AI was founded to eradicate the fragmentation that plagues modern fitness. We believe every athlete deserves world-class biomechanical coaching, scientific progressive overload, and culturally authentic nutrition without needing a personal trainer or dietitian.
        </p>
      </section>

      {/* 2. THE PROBLEM STATEMENT */}
      <section className="public-section" style={{ paddingTop: '0' }}>
        <div
          className="glass-panel"
          style={{
            padding: 'clamp(24px, 5vw, 40px)',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '24px',
          }}
        >
          <div style={{ maxWidth: '820px' }}>
            <span className="badge badge-rose" style={{ marginBottom: '12px' }}>
              The Core Problem
            </span>
            <h2 style={{ fontSize: 'clamp(22px, 3.5vw, 28px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
              Why Conventional Fitness Solutions Fall Short
            </h2>
            <p style={{ color: 'var(--text-body)', fontSize: '15px', lineHeight: 1.7, marginBottom: '20px' }}>
              Today's fitness market is fractured into isolated silos: generic spreadsheet workout apps, disconnected form-checking utilities, and calorie counters that have no understanding of regional diets or real-time biomechanics.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginTop: '24px' }}>
              <div style={{ background: 'var(--bg-input)', padding: '18px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <h4 style={{ color: 'var(--status-error)', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>
                  ❌ Expensive Human Coaching
                </h4>
                <p style={{ color: 'var(--text-body)', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
                  Private human personal trainers cost upwards of $600-$1,200/month, making continuous feedback inaccessible to the majority of lifters.
                </p>
              </div>

              <div style={{ background: 'var(--bg-input)', padding: '18px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <h4 style={{ color: 'var(--status-error)', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>
                  ❌ Blind Workout Execution
                </h4>
                <p style={{ color: 'var(--text-body)', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
                  Workout logging apps have no eyes. They cannot tell if your back rounded on rep 5 or if your knees collapsed inward on your heavy squat.
                </p>
              </div>

              <div style={{ background: 'var(--bg-input)', padding: '18px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <h4 style={{ color: 'var(--status-error)', fontSize: '15px', fontWeight: 700, marginBottom: '6px' }}>
                  ❌ Western-Centric Diets
                </h4>
                <p style={{ color: 'var(--text-body)', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
                  Generic diet apps force lifters into unpalatable, expensive Western foods, ignoring nutritious Egyptian and Mediterranean staples like fava beans, lentils, and Baladi grains.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. THE EGYPTIAN NUTRITION PHILOSOPHY */}
      <section className="public-section">
        <div
          className="about-split-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(280px, 1.2fr) minmax(260px, 1fr)',
            gap: '40px',
            alignItems: 'center',
          }}
        >
          <div>
            <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
              Cultural Nutrition Science
            </span>
            <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px', letterSpacing: '-0.02em' }}>
              Why Egyptian Cuisine is an Athletic Powerhouse
            </h2>
            <p style={{ color: 'var(--text-body)', fontSize: '15px', lineHeight: 1.7, marginBottom: '16px' }}>
              Egyptian cuisine is naturally rich in complex, slow-digesting carbohydrates (fava beans, whole wheat Baladi grains, brown lentils), high-grade lean poultry, and nutrient-dense healthy fats like extra virgin olive oil and unrefined sesame tahini.
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1.7, marginBottom: '24px' }}>
              By pairing an authentic Egyptian culinary vector database with LangGraph multi-agent algorithms and Groq LLMs, Tamrena-AI creates meal plans that feel like home while hitting precise Muscle Protein Synthesis (MPS) targets and micronutrient RDAs.
            </p>

            <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
              <div className="glass-panel" style={{ padding: '12px 18px', background: 'var(--accent-primary-muted)', border: '1px solid rgba(16, 185, 129, 0.4)', flex: '1 1 120px' }}>
                <span className="metric-val" style={{ fontSize: '20px', color: 'var(--category-nutrition)' }}>100%</span>
                <p style={{ fontSize: '11px', color: 'var(--text-heading)', margin: '2px 0 0' }}>Authentic Dishes</p>
              </div>
              <div className="glass-panel" style={{ padding: '12px 18px', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.4)', flex: '1 1 120px' }}>
                <span className="metric-val" style={{ fontSize: '20px', color: 'var(--category-data)' }}>±1.5%</span>
                <p style={{ fontSize: '11px', color: 'var(--text-heading)', margin: '2px 0 0' }}>Calorie Error Margin</p>
              </div>
              <div className="glass-panel" style={{ padding: '12px 18px', background: 'rgba(167, 139, 250, 0.15)', border: '1px solid rgba(167, 139, 250, 0.4)', flex: '1 1 120px' }}>
                <span className="metric-val" style={{ fontSize: '20px', color: 'var(--category-ai)' }}>7 Nodes</span>
                <p style={{ fontSize: '11px', color: 'var(--text-heading)', margin: '2px 0 0' }}>Multi-Agent</p>
              </div>
            </div>
          </div>

          <div
            className="glass-panel"
            style={{
              padding: 'clamp(20px, 4vw, 28px)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
            }}
          >
            <h4 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🇪🇬</span> Sample Daily Egyptian Macro Split
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '12px', background: 'var(--bg-input)', borderRadius: '10px', borderLeft: '3px solid var(--accent-primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)', flexWrap: 'wrap', gap: '4px' }}>
                  <span>Breakfast: Foul + Eggs</span>
                  <span style={{ color: 'var(--accent-primary)' }}>680 kcal</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0' }}>42g Protein • 65g Carbs • 28g Fats</p>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-input)', borderRadius: '10px', borderLeft: '3px solid var(--category-data)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)', flexWrap: 'wrap', gap: '4px' }}>
                  <span>Lunch: Grilled Chicken & Rice</span>
                  <span style={{ color: 'var(--category-data)' }}>850 kcal</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0' }}>65g Protein • 90g Carbs • 22g Fats</p>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-input)', borderRadius: '10px', borderLeft: '3px solid var(--category-motion)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)', flexWrap: 'wrap', gap: '4px' }}>
                  <span>Pre-Workout: Baladi Bread + Peanut Butter</span>
                  <span style={{ color: 'var(--category-motion)' }}>420 kcal</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0' }}>18g Protein • 52g Carbs • 16g Fats</p>
              </div>

              <div style={{ padding: '12px', background: 'var(--bg-input)', borderRadius: '10px', borderLeft: '3px solid var(--category-ai)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, color: 'var(--text-heading)', flexWrap: 'wrap', gap: '4px' }}>
                  <span>Dinner: Egyptian Lentil Soup</span>
                  <span style={{ color: 'var(--category-ai)' }}>590 kcal</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0' }}>55g Protein • 83g Carbs • 8g Fats</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CORE PRINCIPLES */}
      <section className="public-section" style={{ backgroundColor: 'var(--bg-card)', borderRadius: '24px', border: '1px solid var(--border)' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            Our Values
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Core Engineering & Scientific Principles
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '640px', margin: '8px auto 0' }}>
            How we make architectural, biological, and user experience decisions across our 4 sibling services.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '24px' }}>
          {principles.map((item, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: 'clamp(20px, 4vw, 32px)', background: 'var(--bg-page)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '32px', marginBottom: '16px' }}>{item.icon}</div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '10px' }}>
                {item.title}
              </h3>
              <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.6, margin: 0 }}>
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. LEADERSHIP & ARCHITECT */}
      <section className="public-section">
        <div
          className="glass-panel about-leader-card"
          style={{
            padding: 'clamp(24px, 5vw, 48px)',
            display: 'grid',
            gridTemplateColumns: 'auto 1fr',
            gap: '32px',
            alignItems: 'center',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
          }}
        >
          <div
            style={{
              width: '100px',
              height: '100px',
              borderRadius: '24px',
              background: 'var(--accent-primary-muted)',
              border: '2px solid var(--accent-primary)',
              padding: '3px',
              boxShadow: '0 0 35px var(--accent-primary-glow)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
            }}
          >
            <img
              src="/Tamrena-AI.png"
              alt="Basil Reda - Tamrena-AI"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: '20px',
              }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
              <h3 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                Basil Reda
              </h3>
              <span className="badge badge-primary">Creator & Lead Architect</span>
            </div>
            <p style={{ color: 'var(--accent-primary)', fontSize: '13px', fontWeight: 700, margin: '0 0 14px' }}>
              Full-Stack AI Engineering & Biomechanics Architecture
            </p>
            <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.7, margin: 0 }}>
              "Tamrena-AI was conceived from a deep passion for strength athletics, computer vision kinematics, and distributed cloud systems. Our goal is to bring the analytical precision of an Olympic sports laboratory to every athlete's pocket."
            </p>
          </div>
        </div>
      </section>

      {/* 6. PLATFORM EVOLUTION MILESTONES */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            System Evolution
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            From Prototype to Cloud Ecosystem
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
          {milestones.map((m, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: '24px', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>
                {m.year}
              </span>
              <h4 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-heading)', margin: '8px 0' }}>
                {m.title}
              </h4>
              <p style={{ fontSize: '13px', color: 'var(--text-body)', lineHeight: 1.5, margin: 0 }}>
                {m.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 7. CTA */}
      <section className="public-section" style={{ paddingBottom: '100px', textAlign: 'center' }}>
        <div style={{ maxWidth: '640px', margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
            Ready to Elevate Your Training?
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', lineHeight: 1.6, marginBottom: '28px' }}>
            Start your free intake assessment and experience evidence-based AI workout and nutrition intelligence.
          </p>
          <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/signin" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '15px', borderRadius: '10px' }}>
              <span>Start Free Assessment</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
            </Link>
            <Link to="/pricing" className="btn btn-secondary" style={{ padding: '14px 24px', fontSize: '15px', borderRadius: '10px' }}>
              <span>View Pricing Plans</span>
            </Link>
          </div>
        </div>
      </section>

      <style>{`
        @media (max-width: 768px) {
          .about-split-grid {
            grid-template-columns: 1fr !important;
          }
          .about-leader-card {
            grid-template-columns: 1fr !important;
            text-align: center !important;
          }
          .about-leader-card > div:last-child {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
          }
        }
      `}</style>
    </div>
  );
}
