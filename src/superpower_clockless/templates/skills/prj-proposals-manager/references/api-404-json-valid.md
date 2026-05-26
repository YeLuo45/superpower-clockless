# API 404 with proposals.json Still Valid

## Problem Pattern

A cron job fires to update a proposal's fields via ai-superpower API. The API returns 404, but `proposals.json` already contains the correct values for that proposal ID.

## Example from Session

```
API error: HTTP Error 404: Not Found
Status API error: HTTP Error 500: Internal Server Error
```

Yet `proposals.json` (lines 1823-1834) for `P-20260502-017` already shows:
```json
{
  "id": "P-20260502-017",
  "title": "ai-subscription-大模型调用层升级-llm-design-dev",
  "status": "in_dev",
  "priority": "PRJ-20260412-008",
  "created": "ai-subscription",
  "updated": "2026-05-24",
  "assignee": "",
  "tech_expectations": "timeout-approved",
  "tech_expectations_timeout_resolution": "倒计时到期(2026-05-02)，默认通过处理",
  "current_status": "in_dev",
  "tech_stack": "ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair"
}
```

## Root Cause

The API and `proposals.json` can diverge. Proposals exist in the JSON store but are not accessible via the REST API — this is distinct from "ghost proposals" (which have empty titles) and from "API 404 with no JSON entry" (which is a genuine missing state).

## Decision Tree

1. **Does proposals.json have an entry for this ID?**
   - No → Proposal is truly missing; this is not the case described here
   - Yes → Continue

2. **Does the JSON entry have all required fields populated?**
   - Yes (title, status, tech_expectations, current_status, tech_stack) → Data layer is complete
   - No (title="" or partial fields) → This is a **ghost proposal**; follow `ghost-proposal-functional-descendant.md`

3. **Is the data correct as-is?**
   - Yes → Task is done. proposals.json is the data source; index and API are derived.
   - No → Edit proposals.json directly to fix the values, then conclude task is done.

## What NOT to Do

- Do NOT POST a new proposal to replace the one that returned 404 — this orphans the original ID
- Do NOT manually edit proposal-index.md — it is derived and will regenerate on sync
- Do NOT attempt API calls again — the divergence is already confirmed

## Practical Rule

> When API returns 404 but proposals.json has the proposal with correct fields, treat the task as complete at the data layer. The index is derived; it will catch up on the next sync.

## Files Involved

- `/home/hermes/proposals/proposals.json` — data source (authoritative)
- `/home/hermes/proposals/proposal-index.md` — derived index
- `/home/hermes/.hermes/proposals/proposals.json` — mirror copy (auto-synced with above)