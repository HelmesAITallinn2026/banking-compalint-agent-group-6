# Agent Debug Console — Design Spec

**Date:** 2026-04-24
**Goal:** Add a real-time "AI Activity" timeline inside the ComplaintModal that shows agent processing steps as they happen via interval polling. WOW factor for hackathon demo.

## Approach

Self-contained `AgentTimeline` React component with a `useInterval` custom hook. Polls the existing `GET /api/complaints/{id}/agent-logs` endpoint every 3 seconds. Zero new dependencies.

## Components

### 1. `useInterval` hook — `frontend/src/utils/useInterval.js`

- Wraps `setInterval` with proper React lifecycle management
- Accepts `callback` and `delay` (ms). Pass `delay = null` to pause.
- Uses a ref for callback to avoid stale closures
- Clears interval on unmount

### 2. `AgentTimeline` component — `frontend/src/components/AgentTimeline.jsx`

**Props:**
- `complaintId: string` — ID to fetch logs for
- `complaintStatus: string` — current complaint status (determines if still processing)

**State:**
- `expanded: boolean` — default `false`
- `logs: AgentLog[]` — fetched from API
- `expandedLogId: number | null` — which log node is detail-expanded

**Behavior:**
- Toggle button: "🤖 Show AI Activity (N)" where N = log count
- When `expanded` is `true`, polls `getAgentLogs(complaintId)` every 3 seconds
- When `expanded` is `false` or component unmounts, polling stops (delay = null)
- Polling also stops when `complaintStatus` is a terminal status (`Draft Created` or `Completed`)
- On each poll, replaces the full log array (simple, no diffing needed)
- Does an immediate fetch when first expanded (don't wait 3s)

**Terminal statuses** (no pulsing dot, no polling):
- `Draft Created`
- `Completed`

**Timeline rendering:**
- Vertical timeline with a left-border connector line
- Each log entry is a "node" with:
  - Status dot (green ● for completed steps)
  - `agentName` — bold
  - `actionType` — secondary text
  - `createdAt` timestamp — right-aligned, formatted as HH:MM:SS
- Clicking a node toggles its detail panel:
  - `reasoningProcess` — shown in a pre-wrap block
  - `outputContext` — shown if present, parsed JSON displayed formatted
- If complaint is still processing (non-terminal status), show a pulsing blue dot at the bottom with "Processing next step…" label

### 3. Integration into `ComplaintModal.jsx`

- Import `AgentTimeline`
- Place it after the attachments section, before the action buttons (generate draft / approve)
- Pass `complaint.id` and `complaint.status` as props
- No other changes to the modal needed

### 4. CSS — added to `frontend/src/index.css`

All styles scoped under `.agent-timeline` prefix:

- `.agent-timeline__toggle` — toggle button styled as a subtle badge/pill
- `.agent-timeline__container` — max-height 400px, overflow-y auto, smooth expand
- `.agent-timeline__line` — vertical left-border connecting nodes
- `.agent-timeline__node` — flex row with dot, content, timestamp
- `.agent-timeline__dot` — 10px circle, green for completed
- `.agent-timeline__dot--active` — pulsing blue with `@keyframes pulse` animation
- `.agent-timeline__detail` — expandable reasoning/output section, monospace text
- `.agent-timeline__processing` — bottom "processing" indicator with pulsing dot

**Animations:**
- `@keyframes pulse` — scale 1→1.4→1 with opacity change, 1.5s infinite
- Expand/collapse: CSS transition on max-height

## Data Shape (from existing API)

```json
{
  "id": 1,
  "agentName": "Extraction Agent",
  "actionType": "data_extraction",
  "inputContext": "...",
  "reasoningProcess": "Analyzed uploaded PDF...",
  "outputContext": "{...}",
  "createdDttm": "2026-04-24T10:42:15"
}
```

## File Changes Summary

| File | Change |
|------|--------|
| `frontend/src/utils/useInterval.js` | **New** — custom hook |
| `frontend/src/components/AgentTimeline.jsx` | **New** — timeline component |
| `frontend/src/components/ComplaintModal.jsx` | **Edit** — add AgentTimeline |
| `frontend/src/index.css` | **Edit** — add timeline styles |

## Out of Scope

- No backend changes needed (API already exists)
- No SSE/WebSocket — polling is sufficient for demo
- No new npm dependencies
- No changes to agent pipeline or logging
