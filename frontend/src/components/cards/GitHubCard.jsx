export default function GitHubCard({ data }) {
  const {
    has_org, org, profile_url, total_stars = 0,
    repos = [], top_languages = [], open_source_health = 'unknown',
    hiring_signals = [],
  } = data

  const HEALTH_COLOR = {
    active: 'tag-green', moderate: 'tag-gold', minimal: 'tag-gray', unknown: 'tag-gray',
  }

  if (!has_org) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-icon">🐙</div>
          <span className="card-title">GitHub Intelligence</span>
          <span className="card-badge">Not Found</span>
        </div>
        <div className="card-body">
          <div className="empty">No public GitHub organization found for this company.</div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">🐙</div>
        <span className="card-title">GitHub Intelligence</span>
        <span className={`card-badge tag ${HEALTH_COLOR[open_source_health]}`}>
          {open_source_health.toUpperCase()}
        </span>
      </div>
      <div className="card-body">
        {/* Hero stats */}
        <div className="gh-hero">
          <div className="gh-stat-block">
            <div className="gh-stat-num">{repos.length}</div>
            <div className="gh-stat-lbl">Repositories</div>
          </div>
          <div className="gh-div" />
          <div className="gh-stat-block">
            <div className="gh-stat-num">{total_stars.toLocaleString()}</div>
            <div className="gh-stat-lbl">Total Stars</div>
          </div>
          <div className="gh-div" />
          <div className="gh-stat-block">
            <a href={profile_url} target="_blank" rel="noopener noreferrer"
              style={{ color: 'var(--navy)', fontSize: 12, fontWeight: 600 }}>
              @{org}
            </a>
            <div className="gh-stat-lbl">Organization</div>
          </div>
        </div>

        {/* Languages */}
        {top_languages.length > 0 && (
          <>
            <div className="sec-label">Primary Languages</div>
            <div className="lang-chips">
              {top_languages.slice(0, 8).map(l => (
                <span className="lang-chip" key={l}>{l}</span>
              ))}
            </div>
          </>
        )}

        {/* Repo table */}
        {repos.length > 0 && (
          <>
            <div className="divider" />
            <div className="sec-label">Top Repositories</div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Repository</th><th>Language</th><th>Stars</th><th>Forks</th>
                </tr>
              </thead>
              <tbody>
                {repos.slice(0, 6).map(r => (
                  <tr key={r.name}>
                    <td>
                      <a href={r.html_url} target="_blank" rel="noopener noreferrer"
                        style={{ color: 'var(--navy)', fontWeight: 500 }}>
                        {r.name}
                      </a>
                    </td>
                    <td>{r.language ? <span className="lang-chip">{r.language}</span> : '—'}</td>
                    <td><span className="stars-mono">★ {(r.stargazers_count || 0).toLocaleString()}</span></td>
                    <td>{(r.forks_count || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {/* Hiring signals */}
        {hiring_signals.length > 0 && (
          <>
            <div className="divider" />
            <div className="sec-label">Hiring Signals</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {hiring_signals.map(s => (
                <span className="tag tag-gold" key={s}>{s}</span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
