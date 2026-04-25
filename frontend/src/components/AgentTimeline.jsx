import { useState, useEffect, useCallback } from 'react'
import { getAgentLogs } from '../api'
import useInterval from '../utils/useInterval'

const TERMINAL_STATUSES = ['Draft Created', 'Completed']

const blinkingStyle = `
  @keyframes blink {
    0%, 49% { opacity: 1; }
    50%, 100% { opacity: 0; }
  }
  .live-data-badge {
    animation: blink 1s infinite;
  }
`

if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = blinkingStyle
  document.head.appendChild(style)
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function tryFormatJSON(str) {
  if (!str) return null
  try {
    const parsed = typeof str === 'string' ? JSON.parse(str) : str
    return JSON.stringify(parsed, null, 2)
  } catch {
    return str
  }
}

export default function AgentTimeline({ complaintId, complaintStatus }) {
  const [expanded, setExpanded] = useState(false)
  const [logs, setLogs] = useState([])
  const [expandedLogId, setExpandedLogId] = useState(null)

  const isTerminal = TERMINAL_STATUSES.includes(complaintStatus)

  const fetchLogs = useCallback(async () => {
    try {
      const data = await getAgentLogs(complaintId)
      setLogs(Array.isArray(data) ? data : [])
    } catch {
      // silently ignore polling errors
    }
  }, [complaintId])

  // Fetch immediately when expanded
  useEffect(() => {
    if (expanded) fetchLogs()
  }, [expanded, fetchLogs])

  // Poll every 3s while expanded and not terminal
  useInterval(fetchLogs, expanded && !isTerminal ? 3000 : null)

  const toggleDetail = (logId) => {
    setExpandedLogId((prev) => (prev === logId ? null : logId))
  }

  return (
    <>
      <hr className="modal__divider" />
      <button
        className="agent-timeline__toggle"
        onClick={() => setExpanded((prev) => !prev)}
      >
        <span>🤖 {expanded ? 'Hide' : 'Show'} AI Activity</span>
        {logs.length > 0 && (
          <span className="agent-timeline__toggle-count">{logs.length}</span>
        )}
        {!isTerminal && expanded && (
          <span className="live-data-badge" style={{ marginLeft: 'auto', fontSize: 12, color: 'red', fontWeight: 'bold' }}>
            Live data
          </span>
        )}
      </button>

      {expanded && (
        <div className="agent-timeline__container">
          {logs.map((log) => (
            <div key={log.id} className="agent-timeline__node">
              <div className="agent-timeline__dot" />
              <div
                className="agent-timeline__header"
                onClick={() => toggleDetail(log.id)}
              >
                <span className="agent-timeline__agent-name">{log.agentName}</span>
                <span className="agent-timeline__action">{log.actionType}</span>
                <span className="agent-timeline__time">{formatTime(log.createdDttm)}</span>
              </div>

              {expandedLogId === log.id && (
                <div className="agent-timeline__detail">
                  <div className="agent-timeline__detail-label">Reasoning</div>
                  <div>{log.reasoningProcess || '—'}</div>
                  {log.outputContext && (
                    <>
                      <div className="agent-timeline__detail-label">Output</div>
                      <div>{tryFormatJSON(log.outputContext)}</div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}

          {!isTerminal && (
            <div className="agent-timeline__processing">
              <div className="agent-timeline__dot agent-timeline__dot--active" />
              <span>Processing next step…</span>
            </div>
          )}

          {logs.length === 0 && isTerminal && (
            <div style={{ fontSize: 13, color: 'var(--color-text-muted)', padding: '8px 0' }}>
              No agent logs recorded.
            </div>
          )}
        </div>
      )}
    </>
  )
}
