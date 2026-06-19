export default function Sidebar({
  scanning, pptMode, onPptToggle, research, onResearchToggle,
  quickStats, scannedUrl, onReset, isDone,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-inner">

        {/* Brand mark */}
        <div style={{ marginBottom: 4 }}>
          <div style={{
            fontFamily: "'EB Garamond', Baskerville, serif",
            fontSize: 13, fontWeight: 300, color: 'rgba(247,241,222,.45)',
            letterSpacing: '.02em', lineHeight: 1.4,
          }}>
            QuantVeil<br />
            <span style={{ color: 'rgba(176,186,153,.5)', fontSize: 10, letterSpacing: '.12em', textTransform: 'uppercase', fontFamily: "'Open Sans', sans-serif", fontWeight: 400 }}>
              Intelligence Platform
            </span>
          </div>
        </div>

        <div className="sidebar-hr" />

        {/* Options */}
        <div>
          <div className="sec-lbl">Analysis Options</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div className="toggle-row">
              <span className="toggle-text">AI Market Research</span>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={research}
                  onChange={onResearchToggle}
                  disabled={scanning}
                />
                <span className="toggle-sl" />
              </label>
            </div>
            <div className="toggle-row">
              <span className="toggle-text">PPT Export Mode</span>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={pptMode}
                  onChange={onPptToggle}
                  disabled={scanning}
                />
                <span className="toggle-sl" />
              </label>
            </div>
          </div>
        </div>

        {/* Scanned target */}
        {scannedUrl && (
          <>
            <div className="sidebar-hr" />
            <div>
              <div className="sec-lbl">Current Target</div>
              <div className="sidebar-domain">{scannedUrl}</div>
              {(isDone || !scanning) && (
                <button className="btn-new" style={{ marginTop: 10 }} onClick={onReset}>
                  New Analysis
                </button>
              )}
            </div>
          </>
        )}

        {/* Quick stats */}
        {quickStats && (
          <>
            <div className="sidebar-hr" />
            <div>
              <div className="sec-lbl">Results</div>
              {[
                { label: 'Emails',   val: quickStats.emails  },
                { label: 'Phones',   val: quickStats.phones  },
                { label: 'Socials',  val: quickStats.socials },
                { label: 'News',     val: quickStats.news    },
                { label: 'Time',     val: quickStats.elapsed ? `${quickStats.elapsed}s` : '—' },
              ].map(item => (
                <div className="qs-row" key={item.label}>
                  <span className="qs-lbl">{item.label}</span>
                  <span className="qs-val">{item.val}</span>
                </div>
              ))}
            </div>
          </>
        )}

      </div>
    </aside>
  )
}
