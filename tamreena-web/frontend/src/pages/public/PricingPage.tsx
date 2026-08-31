import { useState } from 'react';
import { Link } from 'react-router-dom';

interface FaqItem {
  q: string;
  a: string;
}

const FAQS: FaqItem[] = [
  {
    q: 'Do I need special gym hardware or expensive cameras?',
    a: 'Not at all. Tamrena-AI is built to run directly on standard laptop webcams, tablet cameras, or smartphone cameras. You can also record a set at the gym and upload the video for full biomechanical breakdown.',
  },
  {
    q: 'How does the Egyptian nutrition database work?',
    a: 'Unlike Western apps that only understand oatmeal and chicken breast, our vector database includes authentic Egyptian dishes like Foul Mudammas, Taameya, Koshari, grilled chicken with spiced rice, and Baladi whole-wheat bread, all with laboratory-verified macro distributions.',
  },
  {
    q: 'Can I cancel or change my plan at any time?',
    a: 'Yes, you can upgrade, downgrade, or cancel your subscription at any moment with zero hidden penalties. If you cancel, you will maintain access until the end of your current billing period.',
  },
  {
    q: 'How is my workout and biometric data protected?',
    a: 'We take data privacy very seriously. We use shared JWT authentication with end-to-end token encryption. Workout routines are stored securely in AWS DynamoDB and frontend data in MongoDB with isolated credentials.',
  },
  {
    q: 'What is the benefit of Annual billing over Monthly?',
    a: 'Annual billing provides a 25% discount across all paid tiers — effectively giving you 2 full months free every year.',
  },
  {
    q: 'Can personal trainers and gym coaches use Tamrena-AI for clients?',
    a: 'Yes! The Elite Coach & Gym plan provides multi-client capacity, priority ECS compute queues for zero-lag CV analysis, and full JSON kinematics data export.',
  },
];

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  const proPrice = isAnnual ? '14' : '19';
  const elitePrice = isAnnual ? '36' : '49';

  return (
    <div style={{ position: 'relative' }}>
      {/* 1. HERO SECTION */}
      <section
        className="public-section"
        style={{
          paddingTop: 'clamp(36px, 6vw, 60px)',
          paddingBottom: 'clamp(24px, 4vw, 40px)',
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
            Transparent & Scalable Pricing
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
          Simple, Predictable Plans for{' '}
          <span className="gradient-text-emerald">Every Athletic Ambition</span>.
        </h1>

        <p
          style={{
            fontSize: 'clamp(15px, 2vw, 18px)',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            maxWidth: '700px',
            margin: '0 auto 32px',
          }}
        >
          Start with our free baseline intake assessment or unlock unlimited real-time computer vision form tracking and 7-node Egyptian nutrition intelligence.
        </p>

        {/* Monthly vs Annual Toggle */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            background: 'var(--bg-card)',
            padding: '6px 10px',
            borderRadius: '9999px',
            border: '1px solid var(--border)',
            marginBottom: '32px',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          <span
            onClick={() => setIsAnnual(false)}
            style={{
              fontSize: '13px',
              fontWeight: !isAnnual ? 700 : 500,
              color: !isAnnual ? 'var(--text-heading)' : 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px 14px',
              borderRadius: '9999px',
              backgroundColor: !isAnnual ? 'var(--bg-card-hover)' : 'transparent',
              transition: 'all 0.2s',
            }}
          >
            Monthly Billing
          </span>

          <span
            onClick={() => setIsAnnual(true)}
            style={{
              fontSize: '13px',
              fontWeight: isAnnual ? 700 : 500,
              color: isAnnual ? 'var(--accent-primary)' : 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px 14px',
              borderRadius: '9999px',
              backgroundColor: isAnnual ? 'var(--accent-primary-muted)' : 'transparent',
              border: isAnnual ? '1px solid var(--accent-primary)' : '1px solid transparent',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>Annual Billing</span>
            <span className="badge badge-primary" style={{ padding: '2px 8px', fontSize: '10px' }}>
              SAVE 25%
            </span>
          </span>
        </div>
      </section>

      {/* 2. THREE PRICING TIER CARDS */}
      <section className="public-section" style={{ paddingTop: '0' }}>
        <div className="pricing-cards-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '28px', alignItems: 'stretch' }}>
          {/* Tier 1: Starter Athlete */}
          <div
            className="glass-panel"
            style={{
              padding: 'clamp(24px, 4vw, 36px) clamp(20px, 3vw, 30px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                  Starter Athlete
                </h3>
                <span className="badge badge-slate">Free Forever</span>
              </div>

              <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.5, marginBottom: '20px' }}>
                Essential AI workout generation and baseline metabolic calculations for beginners.
              </p>

              <div style={{ marginBottom: '28px' }}>
                <span className="metric-val" style={{ fontSize: '44px', color: 'var(--text-heading)' }}>$0</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px', marginLeft: '4px' }}>/ month</span>
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: 'var(--text-body)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)' }}>✓</span> 1 AI Workout Protocol / month
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)' }}>✓</span> Baseline BMR / TDEE calculator
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)' }}>✓</span> Standard Exercise Directory
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)' }}>
                  <span>✗</span> Real-time CV pose tracking
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)' }}>
                  <span>✗</span> 7-node Egyptian nutrition pipeline
                </li>
              </ul>
            </div>

            <Link
              to="/signin"
              className="btn btn-outline"
              style={{ width: '100%', padding: '14px', fontSize: '14px', marginTop: '32px' }}
            >
              Get Started Free
            </Link>
          </div>

          {/* Tier 2: Pro Athlete (FEATURED - EMERALD) */}
          <div
            className="glass-panel pricing-pro-card"
            style={{
              padding: 'clamp(28px, 4vw, 36px) clamp(20px, 3vw, 30px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-card)',
              border: '2px solid var(--accent-primary)',
              boxShadow: '0 0 45px var(--accent-primary-glow)',
              position: 'relative',
              zIndex: 2,
            }}
          >
            {/* Top Most Popular Tag */}
            <div
              style={{
                position: 'absolute',
                top: '-14px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'var(--accent-primary)',
                color: 'var(--text-on-accent)',
                fontSize: '11px',
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: '9999px',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                boxShadow: '0 0 20px var(--accent-primary-glow)',
                whiteSpace: 'nowrap',
              }}
            >
              ★ Most Recommended
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', marginTop: '6px' }}>
                <h3 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                  Pro Athlete
                </h3>
                <span className="badge badge-primary">Unlimited AI</span>
              </div>

              <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.5, marginBottom: '20px' }}>
                Full access to real-time computer vision form tracking, InBody scans, and 7-node Egyptian nutrition.
              </p>

              <div style={{ marginBottom: '28px' }}>
                <span className="metric-val" style={{ fontSize: '48px', color: 'var(--accent-primary)' }}>${proPrice}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px', marginLeft: '4px' }}>/ month</span>
                {isAnnual && <span style={{ fontSize: '12px', color: 'var(--accent-primary)', display: 'block', fontWeight: 700 }}>Billed annually ($168/yr)</span>}
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: 'var(--text-heading)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 800 }}>✓</span> Unlimited AI Workout Protocols
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 800 }}>✓</span> InBody Scan OCR & Asymmetry Tracking
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 800 }}>✓</span> 30 FPS Computer Vision Live Coaching
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 800 }}>✓</span> Full 7-Node Egyptian Nutrition Generator
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 800 }}>✓</span> 24/7 AI Coach Chat Assistant
                </li>
              </ul>
            </div>

            <Link
              to="/signin"
              className="btn btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '15px', marginTop: '32px' }}
            >
              Start 14-Day Free Pro Trial
            </Link>
          </div>

          {/* Tier 3: Elite Coach & Gym (Data Blue) */}
          <div
            className="glass-panel"
            style={{
              padding: 'clamp(24px, 4vw, 36px) clamp(20px, 3vw, 30px)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'var(--bg-card)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-heading)', margin: 0 }}>
                  Elite Coach & Gym
                </h3>
                <span className="badge badge-data">Team / Gym</span>
              </div>

              <p style={{ color: 'var(--text-body)', fontSize: '13px', lineHeight: 1.5, marginBottom: '20px' }}>
                Designed for powerlifting coaches, gym owners, and athletes needing priority compute and telemetry export.
              </p>

              <div style={{ marginBottom: '28px' }}>
                <span className="metric-val" style={{ fontSize: '44px', color: 'var(--category-data)' }}>${elitePrice}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px', marginLeft: '4px' }}>/ month</span>
                {isAnnual && <span style={{ fontSize: '12px', color: 'var(--category-data)', display: 'block', fontWeight: 700 }}>Billed annually ($432/yr)</span>}
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: 'var(--text-body)' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--category-data)', fontWeight: 800 }}>✓</span> Everything included in Pro Athlete
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--category-data)', fontWeight: 800 }}>✓</span> Priority AWS ECS GPU compute queue
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--category-data)', fontWeight: 800 }}>✓</span> Raw Kinematics JSON Data Export
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--category-data)', fontWeight: 800 }}>✓</span> Multi-athlete management (up to 10 profiles)
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: 'var(--category-data)', fontWeight: 800 }}>✓</span> Dedicated Sports Science Consultation
                </li>
              </ul>
            </div>

            <Link
              to="/signin"
              className="btn btn-secondary"
              style={{ width: '100%', padding: '14px', fontSize: '14px', marginTop: '32px' }}
            >
              Get Elite Membership
            </Link>
          </div>
        </div>
      </section>

      {/* 3. FEATURE COMPARISON MATRIX TABLE */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <span className="badge badge-slate" style={{ marginBottom: '12px' }}>
            Feature Matrix
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Compare Plan Capabilities
          </h2>
        </div>

        <div className="glass-panel" style={{ padding: 'clamp(16px, 3vw, 24px)', overflowX: 'auto', WebkitOverflowScrolling: 'touch', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <table className="matrix-table" style={{ minWidth: '550px' }}>
            <thead>
              <tr>
                <th style={{ width: '40%' }}>Core Capabilities</th>
                <th style={{ width: '20%' }}>Starter ($0)</th>
                <th style={{ width: '20%', color: 'var(--accent-primary)' }}>Pro Athlete (${proPrice})</th>
                <th style={{ width: '20%', color: 'var(--category-data)' }}>Elite Gym (${elitePrice})</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>AI Workout Protocol Generation</td>
                <td>1 Plan / mo</td>
                <td style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>Unlimited</td>
                <td style={{ color: 'var(--category-data)', fontWeight: 700 }}>Unlimited + Custom Splits</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>InBody OCR Scan & Asymmetry Analysis</td>
                <td style={{ color: 'var(--text-muted)' }}>✗</td>
                <td style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>✓ Unlimited</td>
                <td style={{ color: 'var(--category-data)', fontWeight: 700 }}>✓ Unlimited + History</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Real-Time 30 FPS Computer Vision Coaching</td>
                <td style={{ color: 'var(--text-muted)' }}>✗</td>
                <td style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>✓ Live Webcam & Video</td>
                <td style={{ color: 'var(--category-data)', fontWeight: 700 }}>✓ Priority ECS Queue</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>7-Node Egyptian Nutrition Multi-Agent</td>
                <td style={{ color: 'var(--text-muted)' }}>Basic Macros</td>
                <td style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>✓ Full Meal Plans</td>
                <td style={{ color: 'var(--category-data)', fontWeight: 700 }}>✓ Custom Recipe Integration</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Raw Biomechanical Kinematics JSON Export</td>
                <td style={{ color: 'var(--text-muted)' }}>✗</td>
                <td style={{ color: 'var(--text-muted)' }}>✗</td>
                <td style={{ color: 'var(--category-data)', fontWeight: 700 }}>✓ Full Joint Angle Stream</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700, color: 'var(--text-heading)' }}>Shared JWT Authentication & Security</td>
                <td style={{ color: 'var(--accent-primary)' }}>✓</td>
                <td style={{ color: 'var(--accent-primary)' }}>✓</td>
                <td style={{ color: 'var(--accent-primary)' }}>✓</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. INTERACTIVE FAQ ACCORDION */}
      <section className="public-section">
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <span className="badge badge-primary" style={{ marginBottom: '12px' }}>
            Frequently Asked Questions
          </span>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.02em' }}>
            Everything You Need to Know
          </h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '820px', margin: '0 auto' }}>
          {FAQS.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={idx} className="faq-item">
                <div className="faq-question" onClick={() => toggleFaq(idx)} style={{ padding: 'clamp(14px, 3vw, 20px) clamp(16px, 3vw, 24px)' }}>
                  <span style={{ fontSize: 'clamp(14px, 2.5vw, 16px)' }}>{faq.q}</span>
                  <span style={{ fontSize: '18px', color: isOpen ? 'var(--accent-primary)' : 'var(--text-muted)', transition: 'transform 0.2s', transform: isOpen ? 'rotate(45deg)' : 'none' }}>
                    +
                  </span>
                </div>
                {isOpen && <div className="faq-answer" style={{ padding: '0 clamp(16px, 3vw, 24px) 20px', fontSize: '14px' }}>{faq.a}</div>}
              </div>
            );
          })}
        </div>
      </section>

      {/* 5. CALL TO ACTION */}
      <section className="public-section" style={{ paddingBottom: '100px', textAlign: 'center' }}>
        <div style={{ maxWidth: '680px', margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(24px, 4vw, 34px)', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
            Ready to Experience the Future of Fitness?
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '16px', lineHeight: 1.6, marginBottom: '32px' }}>
            Create your account now to start your free intake assessment and see your custom AI workout protocol.
          </p>
          <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/signin" className="btn btn-primary" style={{ padding: '16px 36px', fontSize: '16px', borderRadius: '10px' }}>
              <span>Create Athlete Account</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
            </Link>
            <Link to="/about" className="btn btn-secondary" style={{ padding: '16px 28px', fontSize: '16px', borderRadius: '10px' }}>
              <span>Learn About Tamrena-AI</span>
            </Link>
          </div>
        </div>
      </section>

      <style>{`
        @media (min-width: 860px) {
          .pricing-pro-card {
            transform: scale(1.03);
          }
        }
      `}</style>
    </div>
  );
}
