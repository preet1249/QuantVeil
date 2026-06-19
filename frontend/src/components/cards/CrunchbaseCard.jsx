export default function CrunchbaseCard({ data }) {
  const {
    url, description, founded, headquarters, employee_count,
    funding_total, funding_rounds = [], investors = [], categories = [],
  } = data

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">💰</div>
        <span className="card-title">Crunchbase Funding</span>
        <span className="card-badge">
          {funding_total || 'Funding Unknown'}
        </span>
      </div>
      <div className="card-body">
        {description && (
          <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text)', marginBottom: 16 }}>
            {description}
          </p>
        )}

        {/* Key metrics */}
        <div className="cb-grid">
          {founded && (
            <div className="cb-cell">
              <div className="cb-cell-label">Founded</div>
              <div className="cb-cell-value">{founded}</div>
            </div>
          )}
          {headquarters && (
            <div className="cb-cell">
              <div className="cb-cell-label">HQ</div>
              <div className="cb-cell-value" style={{ fontSize: 13 }}>{headquarters}</div>
            </div>
          )}
          {employee_count && (
            <div className="cb-cell">
              <div className="cb-cell-label">Employees</div>
              <div className="cb-cell-value">{employee_count}</div>
            </div>
          )}
        </div>

        {/* Funding rounds */}
        {funding_rounds.length > 0 && (
          <>
            <div className="sec-label">Funding Rounds</div>
            <table className="data-table">
              <thead>
                <tr><th>Round</th><th>Amount</th><th>Date</th></tr>
              </thead>
              <tbody>
                {funding_rounds.map((r, i) => (
                  <tr key={i}>
                    <td><span className="tag tag-navy">{r.round || '—'}</span></td>
                    <td style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>
                      {r.amount || '—'}
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{r.date || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {/* Investors */}
        {investors.length > 0 && (
          <>
            <div className="divider" />
            <div className="sec-label">Investors</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {investors.map(inv => (
                <span className="tag tag-navy" key={inv}>{inv}</span>
              ))}
            </div>
          </>
        )}

        {/* Categories */}
        {categories.length > 0 && (
          <>
            <div className="divider" />
            <div className="sec-label">Categories</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {categories.map(c => (
                <span className="tag tag-gray" key={c}>{c}</span>
              ))}
            </div>
          </>
        )}

        {url && (
          <div style={{ marginTop: 14, textAlign: 'right' }}>
            <a href={url} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 11, color: 'var(--navy)', fontWeight: 600 }}>
              View on Crunchbase →
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
