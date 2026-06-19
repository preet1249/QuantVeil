import { useState } from 'react'

export default function DownloadsCard({ jobId, pptMode }) {
  const [downloading, setDownloading] = useState({})

  const download = async (type, endpoint) => {
    setDownloading(prev => ({ ...prev, [type]: true }))
    try {
      const res = await fetch(`/api/download/${endpoint}/${jobId}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = res.headers.get('content-disposition')?.match(/filename="?([^"]+)"?/)?.[1] || `report.${type}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Download failed. The file may still be generating.')
    } finally {
      setDownloading(prev => ({ ...prev, [type]: false }))
    }
  }

  return (
    <div className="card accent-top">
      <div className="card-header">
        <div className="card-icon">📥</div>
        <span className="card-title">Download Report</span>
        <span className="card-badge" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>
          Ready
        </span>
      </div>
      <div className="card-body">
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
          Download your complete intelligence report in your preferred format.
        </p>
        <div className="dl-row">
          <button
            className="btn-dl primary"
            onClick={() => download('pdf', 'pdf')}
            disabled={downloading.pdf}
          >
            {downloading.pdf ? '⏳' : '📄'} Download Report PDF
          </button>

          {pptMode && (
            <>
              <button
                className="btn-dl gold"
                onClick={() => download('pptx', 'ppt')}
                disabled={downloading.pptx}
              >
                {downloading.pptx ? '⏳' : '📊'} Download PPTX
              </button>
              <button
                className="btn-dl ghost"
                onClick={() => download('pdf', 'slides-pdf')}
                disabled={downloading['slides-pdf']}
              >
                {downloading['slides-pdf'] ? '⏳' : '🖼'} Slides as PDF
              </button>
            </>
          )}
        </div>

        <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--navy-100)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--navy)', marginBottom: 4 }}>
            Report includes:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {[
              'Contact Intelligence', 'Reddit Sentiment', 'Google News',
              'Tech Stack Analysis', 'GitHub Activity', 'Wayback Growth',
              ...(pptMode ? ['SWOT Slides', 'Competitor Slide', 'Outreach Slide'] : ['Full SWOT Analysis']),
            ].map(f => (
              <span className="tag tag-navy" key={f}>{f}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
