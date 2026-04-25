# Mortgage Complaint Tree Rebuttals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the mortgage complaint tree so each refusal-reason category also captures the customer's dispute position in clear, test-backed wording.

**Architecture:** Keep the existing JSON tree shape and refusal-reason subcategories unchanged. Update only the subcategory descriptions in `agent/categorization_agent/complaint_tree.json`, and strengthen the mortgage regression test so it proves each description includes the customer-dispute framing described in the spec.

**Tech Stack:** Python 3.12, pytest, JSON complaint taxonomy in `agent/categorization_agent/complaint_tree.json`

---

## File Structure

- Modify: `agent/categorization_agent/complaint_tree.json`
  - Holds the mortgage complaint taxonomy consumed by the categorization agent.
- Modify: `agent/tests/test_mortgage_rules.py`
  - Holds the regression test that locks the complaint tree structure and wording.

### Task 1: Refine mortgage complaint descriptions

**Files:**
- Modify: `agent/tests/test_mortgage_rules.py:95-106`
- Modify: `agent/categorization_agent/complaint_tree.json:1-18`
- Test: `agent/tests/test_mortgage_rules.py`

- [ ] **Step 1: Write the failing test**

Update `agent/tests/test_mortgage_rules.py` so the tree regression test verifies the rebuttal-oriented wording, not just the subcategory names.

```python
def test_complaint_tree_matches_mortgage_application_domain():
    complaint_tree = json.loads(COMPLAINT_TREE_PATH.read_text(encoding="utf-8"))["complaint_tree"]

    assert set(complaint_tree) == {"Mortgage Application Complaints", "Other"}
    assert set(complaint_tree["Mortgage Application Complaints"]["subcategories"]) == {
        "Not enough income",
        "Not enough transactions",
        "Wrong / incomplete documents",
    }

    subcategories = complaint_tree["Mortgage Application Complaints"]["subcategories"]
    assert "customer says their income is enough" in subcategories["Not enough income"].lower()
    assert "assets" in subcategories["Not enough income"].lower()
    assert "customer says their account activity" in subcategories["Not enough transactions"].lower()
    assert "salary history" in subcategories["Not enough transactions"].lower()
    assert "customer says the documents were already provided" in subcategories["Wrong / incomplete documents"].lower()
    assert "request was unclear" in subcategories["Wrong / incomplete documents"].lower()

    assert complaint_tree["Other"]["subcategories"] == {
        "General Mortgage Application Complaint": "General mortgage application issue not covered by specific refusal reasons"
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kamil.kwapisz/code/HACKATHON/agent && uv run pytest -q tests/test_mortgage_rules.py::test_complaint_tree_matches_mortgage_application_domain`

Expected: `FAIL` because the current JSON descriptions mention only the bank's refusal reason and do not yet include the explicit customer rebuttal phrases.

- [ ] **Step 3: Write minimal implementation**

Update the three mortgage subcategory descriptions in `agent/categorization_agent/complaint_tree.json` to encode both the bank's reason and the customer's rebuttal.

```json
{
  "complaint_tree": {
    "Mortgage Application Complaints": {
      "description": "Complaints about negative mortgage application decisions",
      "subcategories": {
        "Not enough income": "Complaint about a negative mortgage decision where the bank says income is insufficient and the customer says their income is enough, stable, or that assets and broader financial strength were not properly considered.",
        "Not enough transactions": "Complaint about a negative mortgage decision where the bank says transaction history is insufficient and the customer says their account activity, salary history, or submitted evidence should have been enough.",
        "Wrong / incomplete documents": "Complaint about a negative mortgage decision where the bank says documents were missing, wrong, or incomplete and the customer says the documents were already provided, were valid, or the bank's request was unclear."
      }
    },
    "Other": {
      "description": "Mortgage application complaints not fitting the main refusal reasons",
      "subcategories": {
        "General Mortgage Application Complaint": "General mortgage application issue not covered by specific refusal reasons"
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kamil.kwapisz/code/HACKATHON/agent && uv run pytest -q tests/test_mortgage_rules.py::test_complaint_tree_matches_mortgage_application_domain`

Expected: `1 passed`

- [ ] **Step 5: Run the mortgage regression suite**

Run: `cd /Users/kamil.kwapisz/code/HACKATHON/agent && uv run pytest -q tests/test_mortgage_rules.py`

Expected: all mortgage rule tests pass, confirming the refined wording did not break the existing mortgage categorization helpers.

- [ ] **Step 6: Commit**

```bash
cd /Users/kamil.kwapisz/code/HACKATHON
git add agent/categorization_agent/complaint_tree.json agent/tests/test_mortgage_rules.py
git commit -m "feat: refine mortgage complaint wording" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
