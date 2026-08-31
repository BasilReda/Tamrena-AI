import { useEffect, useRef, useState } from 'react';
import { getCoachHistory, sendCoachMessage, type CoachMessage } from '../../lib/api';

interface DisplayMessage extends CoachMessage {
  id: string;
  error?: string;
}

function CoachChat() {
  const [messages, setMessages] = useState<DisplayMessage[] | undefined>(undefined);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCoachHistory()
      .then((history) => setMessages(history.map((m, i) => ({ ...m, id: `history-${i}` }))))
      .catch((err) => setLoadError(err instanceof Error ? err.message : 'Failed to load chat history'));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, sending]);

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || sending) return;

    const userMessageId = `local-${Date.now()}`;
    setMessages((prev) => [...(prev ?? []), { id: userMessageId, role: 'user', content: text }]);
    setDraft('');
    setSending(true);

    try {
      const reply = await sendCoachMessage(text);
      setMessages((prev) => [...(prev ?? []), { id: `${userMessageId}-reply`, role: 'assistant', content: reply }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message';
      setMessages((prev) =>
        (prev ?? []).map((m) => (m.id === userMessageId ? { ...m, error: message } : m)),
      );
    } finally {
      setSending(false);
    }
  };

  if (loadError) {
    return (
      <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(255, 23, 68, 0.12)', border: '1px solid rgba(255, 23, 68, 0.3)', color: '#ff80ab' }}>
        ⚠️ {loadError}
      </div>
    );
  }

  if (messages === undefined) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>Connecting to AI Coach Neural Stream...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', maxWidth: '760px', margin: '0 auto' }}>
      <div
        ref={scrollRef}
        className="glass-panel"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'clamp(14px, 3vw, 24px)',
          marginBottom: '14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px' }}>
            <span style={{ fontSize: '32px', display: 'block', marginBottom: '8px' }}>🤖</span>
            <p style={{ fontSize: '14px', color: 'var(--text-body)' }}>Ask me about your workout routine, Egyptian macros, or form cues.</p>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div
              style={{
                maxWidth: '85%',
                padding: '12px 16px',
                borderRadius: '12px',
                fontSize: '13.5px',
                lineHeight: 1.5,
                background: m.role === 'user' ? 'var(--accent-primary-muted)' : 'var(--bg-input)',
                border: m.role === 'user' ? '1px solid var(--accent-primary)' : '1px solid var(--border)',
                color: 'var(--text-heading)',
                whiteSpace: 'pre-wrap',
                overflowWrap: 'break-word',
                boxShadow: m.role === 'user' ? '0 0 15px var(--accent-primary-glow)' : 'none',
              }}
            >
              {m.content}
              {m.error && (
                <p style={{ color: 'var(--status-error)', fontSize: '12px', marginTop: '6px', marginBottom: 0 }}>⚠️ {m.error}</p>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                padding: '10px 16px',
                borderRadius: '12px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                color: 'var(--accent-primary)',
                fontSize: '13px',
                fontStyle: 'italic',
              }}
            >
              AI Coach analyzing…
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask about your workout or nutrition plan..."
          className="form-input"
          style={{
            flex: 1,
            background: 'rgba(10, 20, 56, 0.85)',
            borderColor: 'rgba(0, 255, 255, 0.25)',
            borderRadius: '12px',
            height: '46px',
            fontSize: '13.5px',
          }}
        />
        <button
          onClick={handleSend}
          disabled={sending || !draft.trim()}
          className="btn btn-primary"
          style={{ padding: '0 22px', height: '46px', fontSize: '14px' }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default CoachChat;
