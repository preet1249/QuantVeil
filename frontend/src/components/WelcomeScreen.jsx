import { useState } from 'react'

const PILLS = [
  'Email Extraction', 'Reddit Pulse', 'GitHub Activity',
  'Crunchbase Funding', 'SWOT Analysis', 'Live News',
  'Growth Signal', 'PPT & PDF',
]

const GRID = [
  { label: 'Contact Intelligence', sub: 'Emails, phones & socials' },
  { label: 'Market Position',      sub: 'SWOT & opportunity map' },
  { label: 'Community Pulse',      sub: 'Reddit, HN & news' },
  { label: 'Tech Stack',           sub: 'CMS, frameworks, analytics' },
  { label: 'Funding & Growth',     sub: 'Crunchbase & Wayback signal' },
  { label: 'GitHub Activity',      sub: 'Open source & hiring signals' },
]

export default function WelcomeScreen({ onStart }) {
  const [url,     setUrl]     = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed || loading) return
    setLoading(true)
    await onStart(trimmed)
  }

  return (
    <div className="hero-wrap">
      <div className="hero-inner">

        <div className="hero-eyebrow">
          <span className="hero-eyebrow-chip">QuantVeil · Intelligence Platform</span>
        </div>

        <h1 className="hero-title">
          Turn any URL into<br />
          <em>market intelligence</em>
        </h1>

        <p className="hero-sub">
          Paste a company website and get contacts, Reddit sentiment, GitHub
          activity, Crunchbase funding, and a full SWOT report — in minutes.
        </p>

        <form onSubmit={handleSubmit} className="hero-form">
          <input
            className="hero-input"
            type="text"
            placeholder="basecamp.com or https://stripe.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            disabled={loading}
            autoFocus
            spellCheck={false}
            autoComplete="off"
          />
          <button className="hero-btn" type="submit" disabled={loading || !url.trim()}>
            {loading
              ? <><span className="spinner" />Scanning</>
              : 'Analyze'}
          </button>
        </form>

        <div className="hero-pills">
          {PILLS.map(p => <span className="hero-pill" key={p}>{p}</span>)}
        </div>

        <div className="hero-grid">
          {GRID.map(c => (
            <div className="hero-card" key={c.label}>
              <div className="hero-card-label">{c.label}</div>
              <div className="hero-card-sub">{c.sub}</div>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}
