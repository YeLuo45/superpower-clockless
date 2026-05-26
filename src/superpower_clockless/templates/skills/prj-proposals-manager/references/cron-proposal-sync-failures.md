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
4. **Check ai-superpower API** — `curl http://127.0.0.1:8001/api/proposals/<id>` (NOT port 8000 — server binds to 8001)

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

Instead:
1. Output `[SILENT]` if nothing to report
2. Log the failed cron trigger with timestamp
3. The coordinator should investigate why the proposal is missing

## Critical Distinction: proposals.json vs proposal-index.md

- `proposals.json` is the **authoritative data source** (updated first, then index is derived)
- `proposal-index.md` is a **derived index** — can be missing even when JSON has the proposal
- When diagnosing missing proposals, always check `proposals.json` first

**If cron fires but proposal not in proposal-index.md:**
1. Verify proposal exists and has correct fields in `proposals.json`
2. Update fields directly in `proposals.json`
3. Do NOT attempt to run a sync script that may not exist

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