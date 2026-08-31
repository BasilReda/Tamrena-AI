import { useState } from 'react';
import { Link } from 'react-router-dom';
import LangGraphPipelineDemo from '../../components/public/LangGraphPipelineDemo';

type ServiceKey = 'web' | 'workout' | 'cv' | 'nutrition';

interface ServiceDetail {
  title: string;
  badge: string;
  badgeClass: string;
  color: string;
  path: string;
  role: string;
  stack: string;
  storage: string;
  network: string;
  description: string;
  keyFeatures: string[];
}

const SERVICES: Record<ServiceKey, ServiceDetail> = {
  web: {
    title: 'Tamrena Web',
    badge: 'BFF & Primary Frontend',
    badgeClass: 'badge-data',
    color: 'var(--category-data)',
    path: 'tamreena-web/',
    role: 'Primary web client, authentication gateway, and BFF aggregation proxy',
    stack: 'React 18, TypeScript, Vite 5, FastAPI BFF, Nginx Reverse Proxy',
    storage: 'MongoDB (auth sessions, user metadata at localhost:27018)',
    network: 'Frontend: localhost:5174 | Backend BFF: localhost:8010',
    description:
      'Acts as the unified entry point for athletes. Issues shared JWT tokens, renders the global dashboard, and brokers API calls to sibling backend services without exposing direct database handles.',
    keyFeatures: [
      'Shared JWT issuance & auth validation',
      'Runtime Nginx VITE_API_BASE_URL env substitution',
      'Protected and Public routing architecture',
      'Unified Athlete Command Center dashboard',
    ],
  },
  workout: {
    title: 'Tamrena Workout',
    badge: 'AI Protocol Generation',
    badgeClass: 'badge-ai',
    color: 'var(--category-ai)',
    path: 'Tamrena-Workout/',
    role: 'Hunter Profile intake processing, OCR InBody parsing, and Training Protocol synthesis',
    stack: 'Python 3.11, FastAPI, Pydantic, AWS SDK (Boto3), Docker, AWS ECS',
    storage: 'AWS DynamoDB (migrated from Mongo with idempotent table creation)',
    network: 'Internal ECS Service-to-Service REST API',
    description:
      'The engine responsible for algorithmic periodization. Ingests user constraints, equipment availability, and OCR scan metrics to build tailored multi-day workout routines with automated progressive overload.',
    keyFeatures: [
      'Hunter Profile intake evaluation',
      'OCR InBody scan parsing for muscle asymmetry',
      'Algorithmic RPE & volume progression curves',
      'AWS DynamoDB table persistence',
    ],
  },
  cv: {
    title: 'Computer Vision (AI-GYM)',
    badge: 'Real-Time Biomechanics',
    badgeClass: 'badge-motion',
    color: 'var(--category-motion)',
    path: 'Computer-Vision/',
    role: 'Real-time 30 FPS webcam pose estimation, joint kinematics, rep stage detection & rule violation audits',
    stack: 'Python Analytics Engine (Source of Truth), BlazePose / MediaPipe, FastAPI, WebSockets',
    storage: 'Normalized JSON Session Reports (Rep analytics, angle charts, score rings)',
    network: 'WebSocket ws:// endpoint at root level + REST /api/sessions',
    description:
      'Provides real-time kinematic coaching. Tracks 33 anatomical landmarks, computes instantaneous joint angles (knee, hip, elbow, spine), detects rep transitions, and triggers audio/visual corrective cues for form errors.',
    keyFeatures: [
      '30 FPS real-time MediaPipe BlazePose skeleton overlay',
      'Real-time joint angle trigonometry (knee, hip, torso)',
      'Rule violation classifier (knee valgus, lumbar rounding)',
      'Normalized JSON session analytics with score rings',
    ],
  },
  nutrition: {
    title: 'Nutrition Plan Generation',
    badge: '7-Node Multi-Agent Pipeline',
    badgeClass: 'badge-primary',
    color: 'var(--category-nutrition)',
    path: 'Nutrition-Plan-Generation/',
    role: 'Personalized Egyptian meal plans, BMR/TDEE thermodynamics, macro balancing & explainable AI',
    stack: 'FastAPI, LangGraph 0.1+, Groq LLMs, LangSmith, React Vite UI, SSE Streaming',
    storage: 'Egyptian Culinary Vector Database + USDA macro tables',
    network: 'Server-Sent Events (SSE) streaming API at /api/nutrition/stream',
    description:
      'An advanced 7-node LangGraph multi-agent pipeline. Calculates exact metabolic energy targets, retrieves authentic Egyptian meals (Foul, Koshari, grilled meats), executes a self-correcting ±1.5% validation loop, and streams natural-language rationales.',
    keyFeatures: [
      '7-Node LangGraph multi-agent state graph',
      'Authentic Egyptian culinary vector database',
      'Deterministic BMR/TDEE Mifflin-St Jeor math',
      'Self-correcting tolerance verification loop',
      'Real-time Server-Sent Events (SSE) progress streaming',
    ],
  },
};

export default function PrdArchitecturePage() {
  const [selectedService, setSelectedService] = useState<ServiceKey>('web');
  const activeService = SERVICES[selectedService];

  return (
    <div style={{ position: 'relative' }}>
      {/* 1. HERO HEADER */}
      <section
        className="public-section"
        style={{
          paddingTop: 'clamp(36px, 6vw, 60px)',
          paddingBottom: 'clamp(30px, 5vw, 50px)',
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
            System Architecture & PRD Specification
          </span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(28px, 5vw, 56px)',
            fontWeight: 800,
            lineHeight: 1.15,
            letterSpacing: '-0.02em',
            color: 'var(--text-heading)',
            maxWidth: '960px',
            margin: '0 auto 20px',
          }}
        >
          Engineering Blueprint:{' '}
          <span className="gradient-text-emerald">4-Service Distributed AI Ecosystem</span>
        </h1>

        <p
          style={{
            fontSize: 'clamp(15px, 2vw, 18px)',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            maxWidth: '780px',
            margin: '0 auto 32px',
          }}
        >
          Tamrena-AI combines four independently deployable microservices orchestrated via a unified Backend-for-Frontend (BFF) and shared JWT authentication. Below is the complete technical architecture from our living Product Requirements Document.
        </p>

        {/* PRD Meta Data Bar */}
        <div
          className="glass-panel"
          style={{
            maxWidth: '820px',
            margin: '0 auto',
            padding: 'clamp(12px, 3vw, 16px) clamp(16px, 3vw, 24px)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px',
            fontSize: '13px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
          }}
        >
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Owner: </span>
            <strong style={{ color: 'var(--text-heading)' }}>Basil Reda</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Status: </span>
            <strong style={{ color: 'var(--accent-primary)' }}>Active Living PRD</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Cloud Target: </span>
            <strong style={{ color: 'var(--category-data)' }}>AWS ECS / ECR</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Scope: </span>
            <strong style={{ color: 'var(--text-heading)' }}>Full-Project Workspace</strong>
          </div>
        </div>
      </section>

      {/* 2. 4-SERVICE BLUEPRINT SELECTOR */}
      <section className="public-section" style={{ paddingTop: '0' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            The 4 Sibling Services
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '620px', margin: '6px auto 0' }}>
            Select a service to inspect its runtime stack, networking interfaces, data storage, and engineering roles.
          </p>
        </div>

        {/* Service Tab Switcher */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            marginBottom: '28px',
          }}
        >
          {(Object.keys(SERVICES) as ServiceKey[]).map((key) => {
            const svc = SERVICES[key];
            const isSelected = selectedService === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedService(key)}
                style={{
                  background: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                  border: `1px solid ${isSelected ? svc.color : 'var(--border)'}`,
                  borderRadius: '12px',
                  padding: '14px 16px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected ? `0 0 16px ${svc.color}33` : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', color: isSelected ? svc.color : 'var(--text-muted)', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                    {svc.path}
                  </span>
                  {isSelected && <span style={{ color: svc.color, fontSize: '14px' }}>●</span>}
                </div>
                <h4 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                  {svc.title}
                </h4>
                <p style={{ fontSize: '12px', color: isSelected ? svc.color : 'var(--text-muted)', margin: '2px 0 0' }}>
                  {svc.badge}
                </p>
              </button>
            );
          })}
        </div>

        {/* Active Service Detailed Architecture Card */}
        <div
          className="glass-panel"
          style={{
            padding: 'clamp(20px, 4vw, 36px)',
            background: 'var(--bg-card)',
            border: `1px solid ${activeService.color}`,
            borderRadius: '16px',
            boxShadow: `0 0 20px ${activeService.color}22`,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
                <h3 style={{ fontSize: 'clamp(20px, 3vw, 26px)', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                  {activeService.title}
                </h3>
                <span className={`badge ${activeService.badgeClass}`}>{activeService.badge}</span>
              </div>
              <p style={{ color: activeService.color, fontSize: '13px', margin: 0, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                Workspace Path: {activeService.path}
              </p>
            </div>

            <div
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                fontSize: '11px',
                color: 'var(--text-body)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {activeService.network}
            </div>
          </div>

          <p style={{ color: 'var(--text-body)', fontSize: '14px', lineHeight: 1.7, marginBottom: '24px' }}>
            {activeService.description}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            {/* Tech Stack Specs */}
            <div style={{ padding: '16px', background: 'var(--bg-input)', borderRadius: '10px', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
                Technology Stack
              </span>
              <p style={{ color: 'var(--text-heading)', fontSize: '13px', fontWeight: 600, marginTop: '4px', lineHeight: 1.5, margin: '4px 0 0' }}>
                {activeService.stack}
              </p>
            </div>

            {/* Storage Layer */}
            <div style={{ padding: '16px', background: 'var(--bg-input)', borderRadius: '10px', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
                Data & Storage Persistence
              </span>
              <p style={{ color: activeService.color, fontSize: '13px', fontWeight: 600, marginTop: '4px', lineHeight: 1.5, margin: '4px 0 0' }}>
                {activeService.storage}
              </p>
            </div>
          </div>

          {/* Key Capabilities */}
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-heading)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Service Capabilities & Endpoints
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
              {activeService.keyFeatures.map((feat, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'var(--bg-input)',
                    fontSize: '13px',
                    color: 'var(--text-heading)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <span style={{ color: activeService.color, fontWeight: 800 }}>✓</span>
                  <span>{feat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 3. INTEGRATION MODEL & SYSTEM DESIGN */}
      <section className="public-section" style={{ backgroundColor: 'var(--bg-card)', borderRadius: '24px', border: '1px solid var(--border)' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            System Integration
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Integration Architecture & Security Model
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {/* BFF Pattern (Data) */}
          <div className="glass-panel" style={{ padding: '24px', background: 'var(--bg-page)', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
            <div style={{ color: 'var(--category-data)', fontSize: '24px', marginBottom: '12px' }}>🛡️</div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
              BFF Pattern
            </h3>
            <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
              Frontends never query databases directly. The <code>tamreena-web</code> backend brokers and coordinates requests to sibling services, enforcing authorization and aggregation.
            </p>
          </div>

          {/* Shared Auth (Nutrition / Primary) */}
          <div className="glass-panel" style={{ padding: '24px', background: 'var(--bg-page)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <div style={{ color: 'var(--accent-primary)', fontSize: '24px', marginBottom: '12px' }}>🔑</div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
              Shared JWT Auth Handoff
            </h3>
            <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
              JWT tokens issued by <code>tamreena-web</code> are seamlessly verified by <code>Tamrena-Workout</code> via a shared <code>JWT_SECRET</code>.
            </p>
          </div>

          {/* Dual Storage (AI) */}
          <div className="glass-panel" style={{ padding: '24px', background: 'var(--bg-page)', border: '1px solid rgba(167, 139, 250, 0.3)' }}>
            <div style={{ color: 'var(--category-ai)', fontSize: '24px', marginBottom: '12px' }}>💾</div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
              DynamoDB + MongoDB Stores
            </h3>
            <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
              <code>Tamrena-Workout</code> user state is stored in AWS DynamoDB, while <code>tamreena-web</code> operates its own MongoDB instance for session metadata.
            </p>
          </div>

          {/* AWS ECS Deployment (Motion) */}
          <div className="glass-panel" style={{ padding: '24px', background: 'var(--bg-page)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            <div style={{ color: 'var(--category-motion)', fontSize: '24px', marginBottom: '12px' }}>☁️</div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '8px' }}>
              AWS ECS / ECR & Nginx Proxy
            </h3>
            <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.6, margin: 0 }}>
              Services are containerized with Docker and deployed to AWS ECS tasks with runtime <code>VITE_API_BASE_URL</code> substitution.
            </p>
          </div>
        </div>
      </section>

      {/* 4. 7-NODE LANGGRAPH PIPELINE SHOWCASE */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            Multi-Agent State Graph
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 36px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            7-Node LangGraph Nutrition Pipeline
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', maxWidth: '680px', margin: '8px auto 0' }}>
            Detailed breakdown of our 7 state graph nodes combining Groq LLMs, LangSmith observability, and Egyptian food vectors.
          </p>
        </div>

        <LangGraphPipelineDemo />
      </section>

      {/* 5. LOCAL PORTS & ENVIRONMENT SPECIFICATIONS */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span className="badge badge-slate" style={{ marginBottom: '12px' }}>
            Developer Reference
          </span>
          <h2 style={{ fontSize: 'clamp(22px, 3.5vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Local Ports & Environment Matrix
          </h2>
        </div>

        <div className="glass-panel" style={{ padding: 'clamp(14px, 3vw, 24px)', overflowX: 'auto', WebkitOverflowScrolling: 'touch', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <table className="matrix-table" style={{ minWidth: '550px' }}>
            <thead>
              <tr>
                <th>Service Component</th>
                <th>Local Dev Port</th>
                <th>Protocol</th>
                <th>Environment Config</th>
                <th>Role in Architecture</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>tamreena-web (Frontend)</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-data)' }}>localhost:5174</span></td>
                <td>HTTP / React Vite</td>
                <td><code>VITE_API_BASE_URL</code></td>
                <td>User interface, routing, live session views</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>tamreena-web (Backend BFF)</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-data)' }}>localhost:8010</span></td>
                <td>REST API / FastAPI</td>
                <td><code>JWT_SECRET, MONGO_URI</code></td>
                <td>Auth endpoints, proxy aggregation, sessions</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>tamreena-web MongoDB</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-data)' }}>localhost:27018</span></td>
                <td>MongoDB Wire Protocol</td>
                <td><code>MONGO_INITDB_ROOT_*</code></td>
                <td>Stores users, auth tokens, session reports</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Tamrena-Workout Engine</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-ai)' }}>localhost:8000</span></td>
                <td>REST API / FastAPI</td>
                <td><code>AWS_DEFAULT_REGION</code></td>
                <td>Generates AI workout routines & InBody parser</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Computer-Vision Live AI</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-motion)' }}>localhost:8001</span></td>
                <td>WebSocket + HTTP REST</td>
                <td><code>CV_CONFIDENCE_THRESHOLD</code></td>
                <td>MediaPipe BlazePose 30 FPS kinematic coach</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Nutrition Plan Generation</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', color: 'var(--category-nutrition)' }}>localhost:8000 / 8003</span></td>
                <td>SSE Streaming / LangGraph</td>
                <td><code>GROQ_API_KEY, TAVILY_API_KEY</code></td>
                <td>7-node LangGraph Egyptian nutrition generator</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 6. CTA */}
      <section className="public-section" style={{ paddingBottom: '100px', textAlign: 'center' }}>
        <div style={{ maxWidth: '640px', margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
            Ready to Build With Tamrena-AI?
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '15px', lineHeight: 1.6, marginBottom: '28px' }}>
            Start with our free athlete intake or review scalable gym licensing plans.
          </p>
          <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/signin" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '15px', borderRadius: '10px' }}>
              <span>Start Free Athlete Account</span>
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
    </div>
  );
}
