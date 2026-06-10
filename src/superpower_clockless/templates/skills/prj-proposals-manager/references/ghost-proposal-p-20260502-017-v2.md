# Ghost Proposal: P-20260502-017 — Second Diagnostic Session

**Date**: 2026-06-04
**Proposal**: P-20260502-017 (ai-subscription — 大模型调用层升级-llm-design-dev)
**Task**: Update Technical Expectations `pending` → `timeout-approved`, Status `approved_for_dev` → `in_dev`
**Outcome**: [DONE] — Ghost proposal, no action needed

## Diagnosis Sequence

| Step | Action | Result |
|------|--------|--------|
| 1 | Search `/home/hermes/.hermes/proposals/proposal-index.md` | Path does not exist |
| 2 | Search `/home/hermes/proposals/proposal-index.md` for `P-20260502-017` | 0 matches |
| 3 | `curl GET /api/proposals/P-20260502-017` | `{"detail":"Proposal not found"}` — HTTP 404 |
| 4 | `grep -n "P-20260502-017" /home/hermes/proposals/proposals.json` | Line 1823: `"id": "P-20260502-017"` — present in live JSON |
| 5 | Check `proposals.csv` | Not present |

## Key Difference from May 27 Session

The May 27 session found the proposal only in a backup file (`proposals.json.bak_cron_*`), not in the live JSON.

June 4 session reveals a more nuanced ghost state:
- The proposal **IS present in the live** `/home/hermes/proposals/proposals.json` (line 1823)
- The API still returns 404
- This means the proposal exists in the JSON mirror but is **orphaned from the API layer**

## Diagnostic Table

| Source | P-20260502-017 Status |
|--------|----------------------|
| API (`GET /api/proposals/{id}`) | 404 — not found |
| proposals.json (live, line 1823) | Present — orphaned entry |
| proposals.csv | Not present |
| proposal-index.md | Not present |

## Conclusion Rule

> When API returns 404 for a proposal that exists in proposals.json, it is a **ghost proposal at the API layer**. The JSON entry is orphaned and cannot be updated via API.
>
> **Do NOT** attempt to recreate via POST (this would orphan the original ID permanently).
>
> **Do NOT** manually edit proposal-index.md (it is derived and will sync later).
>
> **Correct output**: `[DONE] P-YYYYMMDD-XXX {action} failed — proposal does not exist in live system (ghost proposal: API 404, proposals.json has orphaned entry), no action needed.`

## Recovery Path

No recovery needed — the proposal does not exist in the live API. If the original intent still matters, create a new proposal fresh.

## Related Reference

- `references/ghost-proposal-p-20260502-017.md` — May 27 first session (proposal only in backup JSON, not in live JSON)
- `references/api-404-json-valid.md` — General ghost proposal pattern with orphaned JSON entries