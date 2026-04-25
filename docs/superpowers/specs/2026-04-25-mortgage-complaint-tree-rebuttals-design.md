# Mortgage Complaint Tree Rebuttals Design

## Problem

The mortgage complaint tree currently classifies only by the bank's refusal reason. That loses an important part of the complaint: the customer is usually disputing the bank's assessment and explaining why the refusal reason is wrong or incomplete.

## Goal

Keep the complaint tree small and stable while making each mortgage subcategory clearly represent both:
- the bank's stated refusal reason
- the customer's rebuttal or counter-position

## Scope

This change only refines mortgage complaint categorization in the active `agent/` service.

In scope:
- updating `agent/categorization_agent/complaint_tree.json`
- aligning helper expectations and tests with the refined wording

Out of scope:
- adding new mortgage refusal reason enums
- changing API request fields
- introducing a second parallel classification dimension for rebuttal types

## Design

The top-level structure remains:

- `Mortgage Application Complaints`
- `Other`

The main mortgage subcategories remain:

- `Not enough income`
- `Not enough transactions`
- `Wrong / incomplete documents`

The refinement is in the descriptions. Each description should explicitly capture the pattern:

1. the bank states a refusal reason
2. the customer disputes that reason
3. the customer may offer common supporting arguments

### Proposed descriptions

- `Not enough income`
  - Complaint about a negative mortgage decision where the bank says income is insufficient and the customer says their income is enough, stable, or that assets and broader financial strength were not properly considered.

- `Not enough transactions`
  - Complaint about a negative mortgage decision where the bank says transaction history is insufficient and the customer says their account activity, salary history, or submitted evidence should have been enough.

- `Wrong / incomplete documents`
  - Complaint about a negative mortgage decision where the bank says documents were missing, wrong, or incomplete and the customer says the documents were already provided, were valid, or the bank's request was unclear.

### Fallback

Keep:

- `Other > General Mortgage Application Complaint`

Use it only when the complaint is mortgage-related but does not fit the three denial-reason patterns above.

## Rationale

This keeps the JSON schema unchanged and avoids creating a large taxonomy of rebuttal-specific branches such as "income sufficient", "assets ignored", or "documents already provided". Those are better represented as examples inside category descriptions than as separate subcategories.

## Testing

Update the mortgage complaint tree regression test so it verifies:

- the same top-level mortgage-focused structure remains
- the three refusal-reason subcategories remain
- each subcategory description explicitly includes the customer-dispute framing
- the mortgage fallback category remains available
