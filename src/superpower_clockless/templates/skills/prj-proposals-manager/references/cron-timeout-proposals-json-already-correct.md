# Cron Timeout: proposals.json Already Correct (v4 era)

> ⚠️ **v5 MIGRATION NOTE (2026-06-08, updated 2026-06-13)**: This file documents v4 cron timeout diagnostics where `proposals.json` (GitHub mirror) was the data layer. In v5.0.0, the equivalent pattern is **"proposals.csv already correct"** — the diagnostic logic is identical, but verification uses `grep -n "P-..." /home/hermes/proposals/proposals.csv` (CSV) and `mcp_aisp.py get-proposal --proposal-id P-...` (MCP, via unified CLI). The "data is source of truth, skip API/index writes when correct" architecture still holds.
> 
> See `references/mcp-vs-rest-migration.md` for the verification command mapping.
> 
> ---

## The Pattern

A cron job fires to update proposal fields (e.g., `Technical Expectations: timeout-approved`, `Current Status: in_dev`). The agent searches `proposal-index.md` for the entry, doesn't find it, then checks `proposals.json` — and discovers **all target fields are already correct**.

## Root Cause

- `proposal-index.md` is a **derived index**, rebuilt from `proposals.json` via sync scripts
- `proposals.json` is the **authoritative data store** for all proposal fields
- A cron can fire while the index hasn't been regenerated yet — this is normal, not an error
- The index entry will appear on the next sync; manual index editing is prohibited

## Diagnostic Sequence

```
1. Cron job specifies /home/hermes/.hermes/proposals/proposal-index.md
   → path does not exist, canonical path is /home/hermes/proposals/proposal-index.md

2. search_files proposals.json for P-YYYYMMDD-XXX
   → find proposal in projects[].proposals[]

3. Read all target fields:
   - technical_expectations / tech_expectations
   - technical_expectations_timeout_resolution
   - current_status / status
   - technical_stack / tech_stack
   - stage

4. If ALL target fields match the cron instruction's desired values:
   → Task is done at data layer. Output "[DONE]" without touching API or index.
   → The index will sync on the next scheduled run.
```

## Ghost Proposal Functional Descendant

If the cron-triggered proposal ID is not found in `proposals.json` at all (ghost proposal), and a **functional descendant** exists (e.g., a V2 iteration of the same feature), see `references/ghost-proposal-functional-descendant.md` for the correct state machine stepping pattern.

## Session Log

| Date | Proposal | What cron asked | What was found |
|------|----------|-----------------|----------------|
| 2026-05-29 | P-20260502-017 | Update tech_expectations→timeout-approved, current_status→in_dev | proposals.json already had all fields correct: tech_expectations=timeout-approved, tech_expectations_timeout_resolution=倒计时到期(2026-05-02)默认通过处理, current_status=in_dev, tech_stack=ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair, stage=in_dev |
| 2026-06-05 | P-20260502-017 | Same as above (re-fire of `P-20260502-017-tech-confirm` cron) | proposals.json still has all fields correct, project PRJ-20260412-008 ai-subscription is entirely missing from proposal-index.md. Output `[DONE]` again. Second occurrence in 7 days — cron job itself likely misconfigured as recurring. |

## Key Rule

> **Never edit proposal-index.md manually.** If `proposals.json` has correct values, the index will follow. The only exception is if a functional descendant exists — follow the ghost proposal recovery path.

## Recurring Fire Pattern

If the same cron (e.g. `P-YYYYMMDD-XXX-tech-confirm`) re-fires on the same proposal more than once, the data-layer answer does not change — output `[DONE]` every time. After the **3rd re-fire**, the cron job itself is almost certainly misconfigured (treated as recurring instead of one-shot, or auto-resolution never cleared the schedule). In that case:

1. Still output `[DONE]` — do not escalate to manual edits
2. Mention the re-fire count in the response so the next reader sees the pattern
3. Do NOT attempt to clean up the cron from inside the cron prompt — that's an external tooling action, not a data-layer one
4. The boss/main agent should review the cron schedule after the session to prevent further re-fires

**Do not** keep "fixing" the same [DONE] outcome — it is correct. The fix lives outside the cron prompt.