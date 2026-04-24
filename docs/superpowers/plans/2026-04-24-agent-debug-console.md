# Agent Debug Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real-time "AI Activity" timeline inside the ComplaintModal that polls agent logs every 3 seconds and visualizes each agent step as a vertical timeline with expandable detail — a WOW factor for the hackathon demo.

**Architecture:** New `useInterval` hook handles polling lifecycle. New `AgentTimeline` component owns all fetching, state, and rendering. It gets mounted inside the existing `ComplaintModal` and receives `complaintId` + `complaintStatus` as props. All styles go in the existing `index.css`.

**Tech Stack:** React 18, Axios (existing), CSS animations, no new dependencies.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/utils/useInterval.js` | **Create** | Reusable `setInterval` hook with pause support |
| `frontend/src/components/AgentTimeline.jsx` | **Create** | Timeline UI, polling logic, expand/collapse |
| `frontend/src/components/ComplaintModal.jsx` | **Modify** | Mount AgentTimeline after attachments |
| `frontend/src/index.css` | **Modify** | All `.agent-timeline*` styles + pulse animation |

---

### Task 1: Create `useInterval` Hook

**Files:**
- Create: `frontend/src/utils/useInterval.js`

- [ ] **Step 1: Create the hook file**

```js
import { useEffect, useRef } from 'react'

export default function useInterval(callback, delay) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (delay === null) return
    const id = setInterval(() => savedCallback.current(), delay)
    return () => clearInterval(id)
  }, [delay])
}
```

- [ ] **Step 2: Verify no syntax errors**

Run: `cd frontend && npx vite build --logLevel error 2>&1 | head -20`
Expected: No errors (hook isn't imported yet, just validating syntax).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/utils/useInterval.js
git commit -m "feat: add useInterval hook for polling support"
```

---

### Task 2: Add Timeline CSS to `index.css`

**Files:**
- Modify: `frontend/src/index.css` (append after the `.spinner` section, before `/* ── Home page */`)

- [ ] **Step 1: Add timeline styles**

Insert the following CSS block in `frontend/src/index.css` **before** the `/* ── Home page */` comment (after line 269, after the `@keyframes spin` block):

```css
/* ── Agent Timeline ─────────────────────── */
.agent-timeline__toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  font-family: var(--font);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.agent-timeline__toggle:hover {
  border-color: var(--color-text);
}
.agent-timeline__toggle-count {
  background: var(--color-text);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.agent-timeline__container {
  max-height: 400px;
  overflow-y: auto;
  margin-top: 12px;
  padding: 4px 0 4px 20px;
  border-left: 2px solid var(--color-border);
  position: relative;
}

.agent-timeline__node {
  position: relative;
  padding: 0 0 20px 16px;
}
.agent-timeline__node:last-child {
  padding-bottom: 0;
}

.agent-timeline__dot {
  position: absolute;
  left: -27px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #2c6415;
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 2px var(--color-border);
}
.agent-timeline__dot--active {
  background: #0007cb;
  animation: agent-pulse 1.5s ease-in-out infinite;
}

@keyframes agent-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.5); opacity: 0.6; }
}

.agent-timeline__header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.agent-timeline__header:hover .agent-timeline__agent-name {
  text-decoration: underline;
}
.agent-timeline__agent-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}
.agent-timeline__action {
  font-size: 12px;
  color: var(--color-text-muted);
}
.agent-timeline__time {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-left: auto;
  white-space: nowrap;
}

.agent-timeline__detail {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Code', monospace;
  color: var(--color-text);
  max-height: 200px;
  overflow-y: auto;
}
.agent-timeline__detail-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
  font-family: var(--font);
}
.agent-timeline__detail-label:not(:first-child) {
  margin-top: 10px;
}

.agent-timeline__processing {
  position: relative;
  padding: 4px 0 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--color-text-muted);
  font-style: italic;
}
.agent-timeline__processing .agent-timeline__dot {
  top: 6px;
}
```

- [ ] **Step 2: Verify CSS parses correctly**

Run: `cd frontend && npx vite build --logLevel error 2>&1 | head -20`
Expected: Build succeeds (no CSS parse errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: add agent timeline CSS styles with pulse animation"
```

---

### Task 3: Create `AgentTimeline` Component

**Files:**
- Create: `frontend/src/components/AgentTimeline.jsx`

- [ ] **Step 1: Create the component**

```jsx
import { useState, useEffect, useCallback } from 'react'
import { getAgentLogs } from '../api'
import useInterval from '../utils/useInterval'

const TERMINAL_STATUSES = ['Draft Created', 'Completed']

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
          <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--color-text-muted)' }}>
            Polling every 3s
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
```

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend && npx vite build --logLevel error 2>&1 | head -20`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AgentTimeline.jsx
git commit -m "feat: add AgentTimeline component with polling and expandable detail"
```

---

### Task 4: Integrate `AgentTimeline` into `ComplaintModal`

**Files:**
- Modify: `frontend/src/components/ComplaintModal.jsx`

- [ ] **Step 1: Add import**

Add this import at the top of `ComplaintModal.jsx`, after the existing import from `'../api'`:

```jsx
import AgentTimeline from './AgentTimeline'
```

- [ ] **Step 2: Add AgentTimeline to the modal body**

In `ComplaintModal.jsx`, find the line (around line 138):
```jsx
        {/* Generate Draft buttons — shown when recommendation is ready */}
```

Insert the following **before** that comment:

```jsx
        {/* Agent activity timeline */}
        <AgentTimeline complaintId={complaint.id} complaintStatus={complaint.status} />
```

- [ ] **Step 3: Verify it compiles**

Run: `cd frontend && npx vite build --logLevel error 2>&1 | head -20`
Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ComplaintModal.jsx
git commit -m "feat: integrate AgentTimeline into ComplaintModal"
```

---

### Task 5: Manual Smoke Test

- [ ] **Step 1: Start the frontend dev server**

Run: `cd frontend && npm run dev`

- [ ] **Step 2: Verify the timeline renders**

1. Open `http://localhost:5173/dashboard`
2. Click any complaint card to open the modal
3. Verify the "🤖 Show AI Activity" toggle button appears above the action buttons
4. Click the toggle — timeline should expand
5. If the complaint has agent logs, they should appear as timeline nodes
6. Click a node to expand its reasoning detail
7. If the complaint is still processing, a pulsing blue dot should appear at the bottom

- [ ] **Step 3: Verify polling works**

1. Open a complaint that is in `Submitted` or `Data Extracted` status
2. Expand the AI Activity section
3. Watch for 3–9 seconds — if the agent pipeline is running, new nodes should appear automatically
4. The "Polling every 3s" label should be visible in the top-right of the toggle button

- [ ] **Step 4: Final commit (if any tweaks needed)**

```bash
git add -A
git commit -m "feat: agent debug console — complete implementation"
```
