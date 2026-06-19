import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function MarketCard({ coldOutreach = '', marketResearch = '' }) {
  const [tab, setTab] = useState(marketResearch ? 'full' : 'brief')

  return (
    <div className="card accent-top">
      <div className="card-header">
        <div className="card-icon">📊</div>
        <span className="card-title">Market Research & AI Analysis</span>
        <span className="card-badge">JP Morgan Intelligence</span>
      </div>
      <div className="card-body" style={{ padding: 0 }}>
        {/* Tabs */}
        <div className="mkt-tabs" style={{ padding: '0 20px' }}>
          {coldOutreach && (
            <button
              className={`mkt-tab ${tab === 'brief' ? 'active' : ''}`}
              onClick={() => setTab('brief')}
            >
              ⚡ Cold Outreach Brief
            </button>
          )}
          {marketResearch && (
            <button
              className={`mkt-tab ${tab === 'full' ? 'active' : ''}`}
              onClick={() => setTab('full')}
            >
              📋 Full SWOT Analysis
            </button>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: '16px 20px 20px', overflowY: 'auto', maxHeight: 560 }}>
          {tab === 'brief' && coldOutreach && (
            <div className="md">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {coldOutreach}
              </ReactMarkdown>
            </div>
          )}
          {tab === 'full' && marketResearch && (
            <div className="md">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {marketResearch}
              </ReactMarkdown>
            </div>
          )}
          {!coldOutreach && !marketResearch && (
            <div className="empty">AI analysis is being generated…</div>
          )}
        </div>
      </div>
    </div>
  )
}
