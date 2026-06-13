# Cron-Triggered Proposal Updates: Diagnosis & Handling

## The Problem

A cron job fires with a proposal ID (e.g., `P-20260502-017-tech-confirm`) but the proposal:
- Is not in `proposals.json` (the authoritative data store)
- Has no entry in `proposal-index.md` (derived index — may lag)
- Doesn't appear in any backup

This means the cron was created but the proposal was never successfully registered, or was removed.

## Diagnostic Checklist

1. **Check proposals.json** — search for the ID directly (nested structure: `projects[].proposals[]`)
2. **Check proposal-index.md** — search for the ID directly (may be missing even when JSON has it)
3. **Check backups** — `grep -r "<id>" backups/`
4. **Check ai-superpower API** — `GET http://127.0.0.1:8000/api/proposals/{id}` (port 8000 confirmed; 8001 only in config, server binds to 8000)

## Possible Causes

| Cause | Evidence | Resolution |
|-------|----------|------------|
| Proposal never registered | Not in JSON, not in index | Log as failed cron, notify coordinator |
| Proposal registered but JSON lost | In index, not in JSON | Restore from backup or re-register |
| Proposal rolled back | Not in current state | Check rollback history |
| Cron created for proposal that failed intake | Index has entry, no JSON | Check if intake step completed |
| Wrong proposal ID in cron name | N/A | Correct the cron name pattern |

## What to Do When Proposal Doesn't Exist

**Do NOT** create the proposal inline from the cron task. A cron job should not be the registration mechanism.

**Output format:**
- If the task was to update fields on a non-existent proposal → output `[DONE] {proposal_id} {target action} failed — proposal does not exist in system (ghost proposal), no action needed.` This is a valid outcome to report, not a failure.
- If nothing to report → output `[SILENT]`

**Protocol:**
1. Verify proposal exists in ai-superpower API via `GET /api/proposals/{id}` (returns 404 if gone)
2. Verify proposal exists in `proposals.csv` (grep for ID)
3. Verify proposal exists in `proposal-index.md` (grep for ID)
4. If all three checks return nothing → proposal is a ghost (never registered or fully removed)
5. Log the ghost proposal with timestamp
6. Output `[DONE]` with the explanation

## Ghost Proposal Diagnosis (2026-05-27 Session)

**Session:** cron P-20260502-017-tech-confirm fired but proposal P-20260502-017 does not exist anywhere.

**Verification steps performed:**
- API `GET /api/proposals/P-20260502-017` → 404 Not Found
- `proposals.csv` grep → ID not found (only 32 lines, total ~270 proposals in API)
- `proposal-index.md` grep → ID not found
- API paginated listing (270 total) → no P-20260502-017 in any page

**Conclusion:** Proposal was never registered. The cron was created against a proposal that failed to persist at intake. This is a ghost proposal — no action possible or needed.

## Critical Distinction: proposals.json vs proposal-index.md

- `proposals.json` is the **authoritative data source** (updated first, then index is derived)
- `proposal-index.md` is a **derived index** — can be missing even when JSON has the proposal
- When diagnosing missing proposals, always check `proposals.json` first

**If cron fires but proposal not in proposal-index.md:**
1. Verify proposal exists and has correct fields in `proposals.json`
2. Update fields directly in `proposals.json`
3. Do NOT attempt to run a sync script that may not exist

**If the specified proposal-index.md path does not exist:**
- Cron task may reference `/home/hermes/.hermes/proposals/proposal-index.md` (non-existent path)
- The actual path is `/home/hermes/proposals/proposal-index.md`
- Search: `find /home/hermes -name "proposal-index.md" 2>/dev/null` if path is unclear

## Cron Naming Convention

The cron name encodes: `{proposal_id}-{stage-transition}`  
Examples:
- `P-20260502-017-prd-confirm` — PRD confirmation timeout
- `P-20260502-017-tech-confirm` — Technical expectations timeout

If the cron fires but the proposal doesn't exist, the cron was created against a proposal that was not successfully persisted.

## Pre-Cron-Trigger Validation (For Coordinators)

Before creating a cron for a proposal:
1. Confirm the proposal exists in `proposals.json` via direct read or ai-superpower API
2. Confirm the proposal has an entry in `proposal-index.md` (if required for downstream)
3. Log the cron creation as part of the proposal record

This prevents orphaned cron jobs that have nothing to act on.
