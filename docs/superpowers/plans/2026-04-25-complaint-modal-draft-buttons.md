# Complaint Modal Draft Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the draft-generation buttons in `ComplaintModal` follow the current AI recommendation and clearly show the override action.

**Architecture:** Keep the change local to `frontend/src/components/ComplaintModal.jsx`. Derive the recommended decision and the opposite decision once from `complaint.recommendation`, then reuse those values for both button labels and `onGenerateDraft(...)` calls so UI copy and behavior cannot drift apart.

**Tech Stack:** React 18, Vite 6, JSX

---

## File Structure

- **Modify:** `frontend/src/components/ComplaintModal.jsx` — derive recommendation-aware decision state and replace the hard-coded draft button labels and click handlers.
- **Reference only:** `frontend/src/pages/Dashboard.jsx` — keep the existing `handleGenerateDraft(complaintId, decision)` callback contract unchanged.
- **Verify:** `frontend/package.json` — use the existing `build` script; do not add a new test runner for this change.

## Notes Before Execution

- There is no existing frontend test harness in this repo (`vitest`, `jest`, and frontend `*.test.*` / `*.spec.*` files are absent).
- For this scoped UI change, follow the existing repo reality: make the smallest safe code change and verify it with `npm run build`.
- Treat any recommendation other than `NEGATIVE` as `POSITIVE` so the modal stays deterministic if recommendation data is missing or malformed.

### Task 1: Derive recommendation-aware decisions

**Files:**
- Modify: `frontend/src/components/ComplaintModal.jsx`

- [ ] **Step 1: Confirm the current modal uses hard-coded draft decisions**

Run:

```bash
cd /Users/kamil.kwapisz/code/HACKATHON && rg -n "Accept \\(Positive\\)|Reject \\(Negative\\)|onGenerateDraft\\(complaint.id, 'POSITIVE'\\)|onGenerateDraft\\(complaint.id, 'NEGATIVE'\\)" frontend/src/components/ComplaintModal.jsx
```

Expected:

```text
lines showing the current hard-coded POSITIVE/NEGATIVE handlers and labels in ComplaintModal.jsx
```

- [ ] **Step 2: Add local derived decision constants near the existing `name` constant**

Insert:

```jsx
  const recommendedDecision =
    complaint.recommendation === 'NEGATIVE' ? 'NEGATIVE' : 'POSITIVE'
  const alternateDecision =
    recommendedDecision === 'POSITIVE' ? 'NEGATIVE' : 'POSITIVE'
  const alternateDecisionLabel =
    alternateDecision === 'POSITIVE' ? 'Override to Positive' : 'Override to Negative'
```

So the component has one source of truth for both actions and labels.

- [ ] **Step 3: Save only the derivation change**

The relevant section should read:

```jsx
  const name =
    complaint.customerName ||
    [complaint.customerFirstName, complaint.customerLastName].filter(Boolean).join(' ') ||
    `Customer #${complaint.customerId}`

  const recommendedDecision =
    complaint.recommendation === 'NEGATIVE' ? 'NEGATIVE' : 'POSITIVE'
  const alternateDecision =
    recommendedDecision === 'POSITIVE' ? 'NEGATIVE' : 'POSITIVE'
  const alternateDecisionLabel =
    alternateDecision === 'POSITIVE' ? 'Override to Positive' : 'Override to Negative'
```

- [ ] **Step 4: Commit the focused derivation change**

```bash
git add frontend/src/components/ComplaintModal.jsx
git commit -m "refactor: derive complaint modal draft decisions"
```

### Task 2: Make button copy and behavior recommendation-aware

**Files:**
- Modify: `frontend/src/components/ComplaintModal.jsx`

- [ ] **Step 1: Replace the left button handler and label**

Change the left button to:

```jsx
                <button
                  className="btn btn--accent"
                  style={{ flex: 1 }}
                  onClick={() => onGenerateDraft(complaint.id, recommendedDecision)}
                  disabled={generating}
                >
                  {generating ? 'Generating…' : 'Maintain recommendation'}
                </button>
```

- [ ] **Step 2: Replace the right button handler and label**

Change the right button to:

```jsx
                <button
                  className="btn btn--outline"
                  style={{ flex: 1 }}
                  onClick={() => onGenerateDraft(complaint.id, alternateDecision)}
                  disabled={generating}
                >
                  {generating ? 'Generating…' : alternateDecisionLabel}
                </button>
```

- [ ] **Step 3: Keep the surrounding modal behavior unchanged**

The section wrapper should remain:

```jsx
        {isRecommendationReady && onGenerateDraft && (
          <>
            <hr className="modal__divider" />
            <div className="modal__section">
              <div className="modal__label">Generate Draft Response</div>
```

Do not change visibility, loading state wiring, approval flow, or the parent callback contract.

- [ ] **Step 4: Commit the button behavior update**

```bash
git add frontend/src/components/ComplaintModal.jsx
git commit -m "feat: align complaint modal draft buttons"
```

### Task 3: Verify the frontend build and semantic result

**Files:**
- Verify: `frontend/src/components/ComplaintModal.jsx`
- Verify: `frontend/package.json`

- [ ] **Step 1: Run the existing frontend build**

```bash
cd /Users/kamil.kwapisz/code/HACKATHON/frontend && npm run build
```

Expected:

```text
vite v6.x.x building for production...
✓ built in <time>
```

- [ ] **Step 2: Sanity-check the two recommendation paths in code**

Run:

```bash
cd /Users/kamil.kwapisz/code/HACKATHON && sed -n '39,170p' frontend/src/components/ComplaintModal.jsx
```

Expected semantic result:

```text
Recommendation = POSITIVE
- Maintain recommendation -> sends POSITIVE
- Override to Negative -> sends NEGATIVE

Recommendation = NEGATIVE
- Maintain recommendation -> sends NEGATIVE
- Override to Positive -> sends POSITIVE
```

- [ ] **Step 3: Commit after verification**

```bash
git add frontend/src/components/ComplaintModal.jsx
git commit -m "chore: verify complaint modal draft buttons"
```

