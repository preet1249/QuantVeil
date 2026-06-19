import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const TREND = {
  growing:  { icon: '↑', color: 'var(--success)',      bg: 'var(--success-bg)',  label: 'Growing'   },
  shrinking:{ icon: '↓', color: 'var(--danger)',        bg: 'var(--danger-bg)',   label: 'Shrinking' },
  stable:   { icon: '→', color: 'var(--body-muted)',    bg: 'var(--soft-stone)',  label: 'Stable'    },
  unknown:  { icon: '?', color: 'var(--muted)',         bg: 'var(--soft-stone)',  label: 'Unknown'   },
}

const barOpts = {
  indexAxis: 'y',
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.raw} pts` } } },
  scales: {
    x: {
      grid: { color: '#f2f2f2' }, border: { display: false },
      ticks: { color: '#93939f', font: { family: 'JetBrains Mono', size: 9 } },
    },
    y: {
      grid: { display: false }, border: { display: false },
      ticks: { color: '#616161', font: { family: 'Inter', size: 9 } },
    },
  },
}

export default function NewsCard({ newsData = {}, wayback = {} }) {
  const newsItems = newsData.news     || []
  const hnPosts   = newsData.hn_posts || []
  const wb        = wayback || {}
  const t         = TREND[wb.trend] || TREND.unknown

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">📰</div>
        <span className="card-title">News · HN · Growth</span>
        <span className="card-badge">{newsItems.length} articles · {hnPosts.length} HN</span>
      </div>
      <div className="card-body">

        {/* Wayback growth signal */}
        {wb.trend && wb.trend !== 'unknown' && (
          <div className="growth-box" style={{ borderColor: t.color }}>
            <span className="growth-icon" style={{ color: t.color, fontSize: 18, fontWeight: 600, minWidth: 18 }}>
              {t.icon}
            </span>
            <div>
              <div className="growth-summary" style={{ color: t.color }}>
                {t.label} · {wb.summary || ''}
              </div>
              <div className="growth-meta">
                {wb.old_avg_kb} KB (6–12 mo ago) → {wb.new_avg_kb} KB (recent)
                {wb.first_seen && ` · First archived ${wb.first_seen.slice(0, 4)}`}
              </div>
            </div>
          </div>
        )}

        <div className="two-col">
          {/* Google News */}
          <div>
            <div className="sec-label">Google News</div>
            {newsItems.length > 0 ? newsItems.slice(0, 7).map((n, i) => (
              <div className="news-item" key={i}>
                <div className="news-meta">
                  <span className="news-src">{n.source}</span>
                  {n.source && n.date && ' · '}
                  <span>{(n.date || '').slice(0, 10)}</span>
                </div>
                <div className="news-headline">{n.title}</div>
              </div>
            )) : (
              <div className="empty">No recent news</div>
            )}
          </div>

          {/* Hacker News */}
          <div>
            <div className="sec-label">Hacker News</div>
            {hnPosts.length > 0 ? (
              <>
                {hnPosts.slice(0, 5).map((h, i) => (
                  <div className="hn-item" key={i}>
                    <span className="hn-pts">{h.points}</span>
                    <a href={h.hn_url || '#'} target="_blank" rel="noopener noreferrer" className="hn-title">
                      {h.title}
                    </a>
                  </div>
                ))}
                {hnPosts.length >= 2 && (
                  <>
                    <div className="sec-label" style={{ marginTop: 18 }}>Points</div>
                    <div className="chart-wrap-sm">
                      <Bar
                        data={{
                          labels: hnPosts.slice(0, 5).map(h =>
                            h.title.length > 28 ? h.title.slice(0, 28) + '…' : h.title
                          ),
                          datasets: [{
                            data: hnPosts.slice(0, 5).map(h => h.points),
                            backgroundColor: '#003c33',
                            borderColor: '#003c33',
                            borderRadius: 4, borderSkipped: false,
                          }],
                        }}
                        options={barOpts}
                      />
                    </div>
                  </>
                )}
              </>
            ) : (
              <div className="empty">No HN mentions found</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
