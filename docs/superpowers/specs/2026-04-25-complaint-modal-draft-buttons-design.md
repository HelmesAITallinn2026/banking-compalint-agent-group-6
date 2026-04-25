# Complaint Modal Draft Buttons Design

## Problem

`frontend/src/components/ComplaintModal.jsx` currently shows fixed draft-generation buttons:

- left button always sends `POSITIVE`
- right button always sends `NEGATIVE`
- labels do not reflect the current AI recommendation

That makes the negative-recommendation path misleading because the "accept" action can still send the opposite decision.

## Proposed Approach

Keep the change local to `frontend/src/components/ComplaintModal.jsx`.

Derive two local values from `complaint.recommendation`:

- `recommendedDecision`
- `alternateDecision`

Use those values as the single source of truth for:

- the left button click handler
- the right button click handler
- the right button label

This keeps copy and behavior aligned without changing parent components or introducing a shared helper.

## Alternatives Considered

### 1. Inline ternaries everywhere

Use recommendation checks directly inside both labels and both click handlers.

**Trade-off:** fastest to write, but duplicates logic and makes it easier for copy and behavior to drift later.

### 2. Local derived constants in `ComplaintModal` (recommended)

Compute recommendation-aware decisions once near the existing `name` constant and reuse them.

**Trade-off:** slightly more setup than inline ternaries, but it stays readable and keeps the modal self-contained.

### 3. Shared helper extraction

Move decision derivation into a helper file.

**Trade-off:** unnecessary indirection for a one-component change with no current reuse.

## Design

### Component scope

Only `frontend/src/components/ComplaintModal.jsx` changes.

`frontend/src/pages/Dashboard.jsx` already passes `handleGenerateDraft(complaintId, decision)`, so the parent contract stays unchanged.

### Derived decision model

Near the existing `name` constant, add:

- `recommendedDecision`
- `alternateDecision`

`recommendedDecision` should resolve to:

- `NEGATIVE` when `complaint.recommendation === 'NEGATIVE'`
- `POSITIVE` for any other value

This preserves deterministic behavior if recommendation data is unexpectedly missing or malformed.

`alternateDecision` should always be the opposite of `recommendedDecision`.

### Button behavior

Inside the existing `Generate Draft Response` section:

- left button means "follow the AI recommendation"
- right button means "override the AI recommendation"

The left button calls:

`onGenerateDraft(complaint.id, recommendedDecision)`

The right button calls:

`onGenerateDraft(complaint.id, alternateDecision)`

### Button copy

Keep the current two-button layout and loading behavior.

Use concise operator-facing copy:

- left button: `Maintain recommendation`
- right button: `Override to Positive` or `Override to Negative`

The right button label should be derived from `alternateDecision` so the outcome is explicit without the longer sentence from `frontend/src/components/plan2.md`.

When `generating` is true, both buttons should continue to show `Generating…`.

### Visibility and surrounding behavior

Do not change the existing visibility guard:

`isRecommendationReady && onGenerateDraft`

Do not change:

- modal layout
- loading state behavior
- approval flow
- draft display
- parent callback contract

## Error Handling

No new error path is introduced.

The existing guard already prevents this section from rendering before recommendation readiness. If recommendation data is still unexpected, the fallback behavior is to treat it as `POSITIVE` rather than adding a new UI error state.

## Validation

Use the existing frontend verification path only:

`npm run build` from `frontend/`

Expected semantic result:

- if recommendation is `POSITIVE`, buttons read `Maintain recommendation` and `Override to Negative`
- if recommendation is `NEGATIVE`, buttons read `Maintain recommendation` and `Override to Positive`

## Implementation Boundary

This design intentionally keeps the change in one component because there is no evidence that other frontend surfaces reuse this decision-button logic.
