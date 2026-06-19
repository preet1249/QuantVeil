import { useState, useEffect, useRef } from 'react'
import Topbar from './components/Topbar'
import Sidebar from './components/Sidebar'
import WelcomeScreen from './components/WelcomeScreen'
import ProgressPanel from './components/ProgressPanel'
import ResultsPanel from './components/ResultsPanel'

const STEPS = [
  { id: 'website',      label: 'Scraping website'       },
  { id: 'contacts',     label: 'Extracting contacts'    },
  { id: 'intelligence', label: 'News · GitHub · Wayback' },
  { id: 'reddit',       label: 'Reddit intelligence'    },
  { id: 'ai',           label: 'AI market analysis'     },
]

export default function App() {
  const [jobId,     setJobId]     = useState(null)
  const [sections,  setSections]  = useState({})
  const [stepState, setStepState] = useState({})
  const [stepMsgs,  setStepMsgs]  = useState({})
  const [isDone,    setIsDone]    = useState(false)
  const [elapsed,   setElapsed]   = useState(null)
  const [error,     setError]     = useState(null)
  const [status,    setStatus]    = useState('idle')
  const [pptMode,   setPptMode]   = useState(false)
  const [research,  setResearch]  = useState(true)
  const [scannedUrl, setScannedUrl] = useState('')
  const esRef = useRef(null)

  const handleStart = async (url) => {
    setSections({})
    setStepState({})
    setStepMsgs({})
    setIsDone(false)
    setElapsed(null)
    setError(null)
    setScannedUrl(url)
    setStatus('scanning')

    const res = await fetch('/api/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, options: { research } }),
    })
    const { job_id } = await res.json()
    setJobId(job_id)
  }

  const handleReset = () => {
    if (esRef.current) esRef.current.close()
    setSections({})
    setStepState({})
    setStepMsgs({})
    setIsDone(false)
    setElapsed(null)
    setError(null)
    setStatus('idle')
    setJobId(null)
    setScannedUrl('')
  }

  useEffect(() => {
    if (!jobId) return
    if (esRef.current) esRef.current.close()
    const es = new EventSource(`/api/stream/${jobId}`)
    esRef.current = es

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      if (msg.type === 'progress') {
        setStepState(prev => {
          const next = { ...prev }
          Object.keys(next).forEach(k => { if (next[k] === 'running') next[k] = 'done' })
          next[msg.step] = 'running'
          return next
        })
        setStepMsgs(prev => ({ ...prev, [msg.step]: msg.message }))
      }
      if (msg.type === 'result') {
        setSections(prev => ({ ...prev, [msg.section]: msg.data }))
      }
      if (msg.type === 'error') {
        setError(msg.message)
        setStatus('done')
        es.close()
      }
      if (msg.type === 'complete' || msg.type === 'done') {
        setIsDone(true)
        setElapsed(msg.elapsed || null)
        setStatus('done')
        setStepState(prev => {
          const next = { ...prev }
          Object.keys(next).forEach(k => { next[k] = 'done' })
          return next
        })
        es.close()
      }
    }
    es.onerror = () => {
      setError('Connection lost — the scan may still be running.')
      es.close()
    }
    return () => es.close()
  }, [jobId])

  const quickStats = isDone ? {
    emails:  sections.contacts?.emails?.length  ?? 0,
    phones:  sections.contacts?.phones?.length  ?? 0,
    socials: Object.keys(sections.contacts?.socials ?? {}).length,
    news:    sections.news?.news?.length ?? 0,
    elapsed,
  } : null

  return (
    <div className="app">
      <Topbar status={status} domain={scannedUrl} />
      <div className="layout">
        <Sidebar
          scanning={status === 'scanning'}
          pptMode={pptMode}
          onPptToggle={() => setPptMode(v => !v)}
          research={research}
          onResearchToggle={() => setResearch(v => !v)}
          quickStats={quickStats}
          scannedUrl={scannedUrl}
          onReset={handleReset}
          isDone={isDone}
        />
        <main className="main">
          {status === 'idle' ? (
            <WelcomeScreen onStart={handleStart} />
          ) : (
            <div className="main-scroll">
              <ProgressPanel
                steps={STEPS}
                stepState={stepState}
                stepMsgs={stepMsgs}
              />
              {error && (
                <div style={{
                  background:'var(--danger-bg)',color:'var(--danger)',
                  padding:'12px 18px',borderRadius:'var(--radius-sm)',
                  fontSize:'13px',border:'1px solid',borderColor:'var(--danger)',
                }}>
                  {error}
                </div>
              )}
              {Object.keys(sections).length > 0 && (
                <ResultsPanel
                  sections={sections}
                  jobId={jobId}
                  isDone={isDone}
                  pptMode={pptMode}
                />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
