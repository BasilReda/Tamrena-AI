import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { CvSessionReport } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

interface DotProps {
  cx?: number;
  cy?: number;
  payload?: { good: boolean };
}

function VerdictDot({ cx = 0, cy = 0, payload }: DotProps) {
  return <circle cx={cx} cy={cy} r={5} fill={payload?.good ? 'var(--accent-primary)' : 'var(--status-error)'} stroke="#050c24" strokeWidth={2} />;
}

/**
 * Renders the CV engine's own report (score-per-rep + rule-failure
 * breakdown) on the tamrena-web completion screen.
 */
function SessionReportView({ report }: { report: CvSessionReport }) {
  const { t } = useTranslation();
  const points = (report.history ?? []).map((r) => ({ rep: r.number, score: r.score, good: r.good }));
  const errorEntries = Object.entries(report.summary?.common_errors ?? {});
  const ruleByName = new Map(report.rules.map((r) => [r.name, r]));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
      <div className="glass-panel" style={{ padding: '20px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
        <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', marginBottom: '12px' }}>
          {t('liveSession.complete.scorePerRep')}
        </span>
        <div style={{ height: '220px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid vertical={false} stroke="rgba(112, 128, 144, 0.2)" strokeDasharray="3 3" />
              <XAxis dataKey="rep" tick={{ fontSize: 11, fill: '#64748B' }} tickLine={false} axisLine={false} tickFormatter={(v: number) => `#${v}`} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748B' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#131A2B', border: '1px solid var(--accent-primary)', borderRadius: 10, boxShadow: '0 0 20px rgba(16, 185, 129, 0.25)' }}
                labelStyle={{ color: '#F1F5F9' }}
              />
              <Line type="monotone" dataKey="score" stroke="var(--accent-primary)" strokeWidth={3} dot={<VerdictDot />} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '20px', background: 'var(--bg-input)', border: '1px solid var(--border)' }}>
        <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', marginBottom: '12px' }}>
          {t('liveSession.complete.mistakesBreakdown')}
        </span>
        {errorEntries.length === 0 ? (
          <p style={{ fontSize: '13.5px', color: 'var(--accent-primary)', margin: 0, fontWeight: 700 }}>
            {t('liveSession.complete.perfectForm')}
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {errorEntries.map(([rule, count]) => (
              <div key={rule} style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '10px', background: 'rgba(239, 68, 68, 0.12)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13.5px' }}>
                  <span style={{ color: 'var(--text-heading)', fontWeight: 600 }}>{rule}</span>
                  <span style={{ color: 'var(--category-motion)', fontWeight: 700 }}>{count}×</span>
                </div>
                {ruleByName.get(rule)?.message && (
                  <p style={{ fontSize: '12px', color: 'var(--status-error)', margin: 0 }}>{ruleByName.get(rule)!.message}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default SessionReportView;
