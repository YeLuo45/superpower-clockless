# Ghost Proposal: P-20260502-017 Diagnostic Session

**Date**: 2026-06-02
**Proposal**: P-20260502-017 (ai-subscription — 大模型调用层升级-llm-design-dev)
**Task**: Update Technical Expectations from `pending` to `timeout-approved` + Status `approved_for_dev` → `in_dev`
**Outcome**: [DONE] — Ghost proposal, no action needed

## Diagnosis Sequence

| Step | Action | Result |
|------|--------|--------|
| 1 | Search `proposal-index.md` for `P-20260502-017` | 0 matches |
| 2 | Check `proposals.csv` for `P-20260502-017` | Not found |
| 3 | Check `proposals.json` (main) | `{"projects": [...], "lastUpdate": "..."}` structure; 0 proposals in array |
| 4 | Check `proposals.json.bak_cron_20260527050204` | Structure confirmed; proposal found in backup but status already `in_dev` |
| 5 | API `GET /api/proposals/P-20260502-017` | HTTP 404 — proposal does not exist in API |

## Key Findings

1. **proposals.json is project-centric, not flat**: Top-level keys are `["projects", "lastUpdate"]`, not `{"proposals": [...]}`. Proposals are nested inside each project object.

2. **Ghost proposal confirmed**: All four sources agree the proposal ID does not exist in the live system:
   - proposal-index.md: no entry
   - proposals.csv: no record
   - proposals.json: 0 proposals (empty array in project-centric structure)
   - API: 404 Not Found

3. **Backup file is stale**: The backup `proposals.json.bak_cron_20260527050204` contains a stale snapshot from May 27 where the proposal existed in the backup JSON but was already removed from the live API.

4. **proposals.csv is a derived backup**: It has far fewer lines (32) than total API proposals, confirming it is not the authoritative source.

## Conclusion Rule

> When a cron fires for a proposal ID that returns 404 from the API AND is not found in the live `proposals.json`, it is a **ghost proposal** — a proposal that existed historically but was cleaned up or never fully registered. Output: `[DONE] {id} {action} failed — proposal does not exist in system (ghost proposal), no action needed.`

## Recovery

No recovery needed — the proposal does not exist in the live system. If the original intent still matters, a new proposal should be created fresh.

## Reference: proposals.json Structure

```
{
  "projects": [          # ← NOT "proposals"
    {
      "id": "PRJ-20260412-008",
      "name": "ai-subscription",
      ...
      "proposals": [     # ← proposals nested inside project
        {
          "id": "P-20260502-017",
          "title": "ai-subscription-大模型调用层升级-llm-design-dev",
          "status": "in_dev",
          ...
        }
      ]
    }
  ],
  "lastUpdate": "2025-05-24"
}
```

To find a proposal by ID, you must:
1. Iterate over `projects[]`
2. Within each project, iterate over its inner `proposals[]`
3. Match on `proposal.id === target`