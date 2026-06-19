import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const CAT_BG = {
  cms:            '#edfce9',
  analytics:      '#f1f5ff',
  infrastructure: '#eeece7',
  framework:      '#edfce9',
  marketing:      'rgba(255,119,89,.09)',
  ecommerce:      '#f1f5ff',
  payments:       '#edfce9',
}
const CAT_COLOR = {
  cms:            '#003c33',
  analytics:      '#1863dc',
  infrastructure: '#616161',
  framework:      '#2d6a4f',
  marketing:      '#ff7759',
  ecommerce:      '#071829',
  payments:       '#2d6a4f',
}

const CATS = ['cms','framework','ecommerce','analytics','marketing','payments','infrastructure']

const chartOpts = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.raw} detected` } } },
  scales: {
    x: {
      ticks: { stepSize: 1, color: '#93939f', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: '#f2f2f2' }, border: { display: false },
    },
    y: {
      ticks: { color: '#616161', font: { family: 'Inter', size: 10 } },
      grid: { display: false }, border: { display: false },
    },
  },
}

export default function WebsiteCard({ data }) {
  const { engine, bytes, status, tech_stack = {} } = data
  const allTech = tech_stack.all || []
  const chartLabels = CATS.filter(c => tech_stack[c]?.length > 0)

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">🌐</div>
        <span className="card-title">Website Scan</span>
        <span className="card-badge">
          <span className="engine-badge">{engine}</span>
          {bytes > 0 && (
            <span className="byte-badge" style={{ marginLeft: 8 }}>
              {(bytes / 1024).toFixed(1)} KB · {status}
            </span>
          )}
        </span>
      </div>
      <div className="card-body">
        {allTech.length > 0 ? (
          <div className="two-col">
            <div>
              <div className="sec-label">Detected Technologies</div>
              <div className="tech-chips">
                {CATS.map(cat =>
                  (tech_stack[cat] || []).map(tech => (
                    <span
                      key={tech}
                      className="tech-chip"
                      style={{ background: CAT_BG[cat] || '#eeece7', color: CAT_COLOR[cat] || '#616161' }}
                    >
                      {tech}
                    </span>
                  ))
                )}
              </div>
            </div>
            {chartLabels.length >= 2 && (
              <div>
                <div className="sec-label">Stack Distribution</div>
                <div className="chart-wrap-sm">
                  <Bar
                    data={{
                      labels: chartLabels.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
                      datasets: [{
                        data: chartLabels.map(c => (tech_stack[c] || []).length),
                        backgroundColor: chartLabels.map(c => CAT_BG[c] || '#eeece7'),
                        borderColor:     chartLabels.map(c => CAT_COLOR[c] || '#616161'),
                        borderWidth: 1.5,
                        borderRadius: 4,
                      }],
                    }}
                    options={chartOpts}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="empty">No technologies detected from this page.</div>
        )}
      </div>
    </div>
  )
}
