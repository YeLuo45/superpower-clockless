# Cron Timeout: proposal-index.md Missing Entry

## Symptoms
- A cron job fires to "update proposal-index.md" for a proposal (e.g., `P-YYYYMMDD-XXX`)
- `proposal-index.md` has no entry for that proposal
- But `proposals.json` already has the correct data

## Root Cause
`proposals.json` is the **data source**. `proposal-index.md` is a **derived index**. If the cron fired but `proposals.json` already had correct values, the task was already done — the index sync is a no-op.

## Decision Tree

```
1. Read lines around P-YYYYMMDD-XXX in /home/hermes/proposals/proposals.json
   └── If correct values already present → TASK ALREADY DONE. Skip index edit.
   └── If values missing or wrong → Go to step 2.

2. Edit /home/hermes/proposals/proposals.json directly to set correct fields:
   - tech_expectations: "timeout-approved"
   - tech_expectations_timeout_resolution: "倒计时到期(...)，默认通过处理"
   - current_status: "in_dev"
   - tech_stack: "ai SDK + @ai-sdk/openai + ..."

3. Verify edit took effect by re-reading proposals.json
```

## Key Files
| Path | Role |
|------|------|
| `/home/hermes/proposals/proposals.json` | Data source (editable) |
| `/home/hermes/proposals/proposal-index.md` | Derived index (do not edit directly) |
| `/home/hermes/.hermes/proposals/proposals/proposals.json` | Auto-synced mirror of above |

## What NOT to Do
- Do NOT run `sync-proposals-to-website.py` — it may not exist and is not needed
- Do NOT edit `proposal-index.md` directly — it's derived, edits will be overwritten
- Do NOT create a new proposal via POST — this orphans the original ID

## Example: Reading proposals.json for a proposal
```python
# Read around line 1823 where P-20260502-017 was found
with open("/home/hermes/proposals/proposals.json") as f:
    lines = f.readlines()
# lines[1823] = '          "id": "P-20260502-017",'
# lines[1825] = '          "status": "in_dev",'
```