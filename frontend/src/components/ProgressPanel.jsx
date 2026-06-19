export default function ProgressPanel({ steps, stepState, stepMsgs }) {
  const doneCount = Object.values(stepState).filter(s => s === 'done').length

  return (
    <div className="progress-panel">
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
        <div className="progress-title">Gathering Intelligence</div>
        <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: "'JetBrains Mono',monospace" }}>
          {doneCount}/{steps.length}
        </div>
      </div>
      <div className="steps">
        {steps.map((step, i) => {
          const state = stepState[step.id] || 'pending'
          return (
            <div className="step" key={step.id}>
              <div className={`step-dot ${state}`}>
                {state === 'done'    ? '✓' :
                 state === 'running' ? '●' : String(i + 1)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className={`step-text ${state}`}>{step.label}</div>
                {state === 'running' && stepMsgs[step.id] && (
                  <div className="step-msg">{stepMsgs[step.id]}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
