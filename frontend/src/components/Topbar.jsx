export default function Topbar({ status, domain }) {
  const dotClass   = status === 'scanning' ? 'scanning' : status === 'done' ? 'done' : ''
  const statusText = status === 'scanning' ? 'Scanning' : status === 'done' ? 'Complete' : 'Ready'

  return (
    <nav className="topbar">
      <div className="topbar-logo">
        <div className="topbar-mark">QV</div>
        <span className="topbar-brand">QuantVeil</span>
        <div className="topbar-divider" />
        <span className="topbar-sub">Market Intelligence Platform</span>
      </div>
      <div className="topbar-right">
        {domain && status !== 'idle' && (
          <span style={{
            fontSize: 11, color: 'var(--text-light)',
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {domain.replace(/^https?:\/\//, '')}
          </span>
        )}
        <div className="topbar-status">
          <span className={`status-dot ${dotClass}`} />
          {statusText}
        </div>
      </div>
    </nav>
  )
}
