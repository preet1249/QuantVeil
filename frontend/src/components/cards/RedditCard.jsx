import { useMemo } from 'react'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend)

function parseSentiment(aiSummary = '', posts = []) {
  const text = (aiSummary || '').toLowerCase()
  const neg = ['frustrat','complaint','broken','terrible','hate','worst','bad','annoying','problem','issue','awful','disappoint']
  const pos = ['love','great','excellent','recommend','perfect','best','amazing','helpful','simple','reliable','awesome','good','fantastic']
  let n = neg.reduce((s, w) => s + (text.match(new RegExp(w, 'g')) || []).length, 0)
  let p = pos.reduce((s, w) => s + (text.match(new RegExp(w, 'g')) || []).length, 0)
  const avgScore = posts.length ? posts.reduce((s, x) => s + (x.score || 0), 0) / posts.length : 0
  if (avgScore > 50) p += 3
  else if (avgScore < 5 && posts.length > 3) n += 2
  const total = Math.max(n + p, 3)
  const posP = Math.min(75, Math.round(p / total * 100))
  const negP = Math.min(65, Math.round(n / total * 100))
  return { positive: posP, negative: negP, neutral: Math.max(5, 100 - posP - negP) }
}

const chartOpts = {
  cutout: '70%',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        font: { size: 10, family: 'Inter' },
        color: '#616161', padding: 10, boxWidth: 8, boxHeight: 8,
      },
    },
    tooltip: { callbacks: { label: ctx => ` ${ctx.raw}%` } },
  },
}

export default function RedditCard({ data }) {
  const { ai_summary = '', posts = [] } = data
  const sentiment = useMemo(() => parseSentiment(ai_summary, posts), [ai_summary, posts])

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">💬</div>
        <span className="card-title">Reddit Intelligence</span>
        <span className="card-badge">{posts.length} posts</span>
      </div>
      <div className="card-body">
        <div className="two-col">
          {/* Left: summary + posts */}
          <div>
            {ai_summary ? (
              <>
                <div className="sec-label">AI Summary</div>
                <div className="ai-summary">{ai_summary}</div>
              </>
            ) : (
              <div className="empty">No Reddit summary available.</div>
            )}

            {posts.length > 0 && (
              <>
                <div className="sec-label" style={{ marginTop: 16 }}>Top Posts</div>
                {posts.slice(0, 6).map((p, i) => (
                  <a
                    key={i} href={p.permalink} target="_blank"
                    rel="noopener noreferrer" style={{ textDecoration: 'none', display: 'block' }}
                  >
                    <div className="post-item">
                      <span className="post-score">{p.score}</span>
                      <div>
                        <div className="post-sub">{p.subreddit}</div>
                        <div className="post-title">{p.title}</div>
                      </div>
                    </div>
                  </a>
                ))}
              </>
            )}
          </div>

          {/* Right: sentiment doughnut */}
          <div>
            <div className="sec-label">Community Sentiment</div>
            <div style={{ height: 170 }}>
              <Doughnut
                data={{
                  labels: ['Positive', 'Negative', 'Neutral'],
                  datasets: [{
                    data: [sentiment.positive, sentiment.negative, sentiment.neutral],
                    backgroundColor: ['#003c33', '#ff7759', '#eeece7'],
                    borderColor:     ['#003c33', '#ff7759', '#d9d9dd'],
                    borderWidth: 1.5,
                    hoverOffset: 4,
                  }],
                }}
                options={chartOpts}
              />
            </div>
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { label: 'Positive', val: sentiment.positive, cls: 'tag-green' },
                { label: 'Negative', val: sentiment.negative, cls: 'tag-gold'  },
                { label: 'Neutral',  val: sentiment.neutral,  cls: 'tag-gray'  },
              ].map(s => (
                <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--body-muted)' }}>{s.label}</span>
                  <span className={`tag ${s.cls}`}>{s.val}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
