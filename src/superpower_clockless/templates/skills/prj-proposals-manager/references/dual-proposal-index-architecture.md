# Dual Index Architecture: proposal-index.md vs proposal-docs-index.md

## Problem Statement

When searching for proposals by ID (e.g., `P-20260419-005`, `P-20250416-003`), `grep` searches on `proposal-index.md` return **no results**, but the proposals clearly exist as PRD files in `workspace-pm/proposals/`.

## Root Cause: Two Separate Indexes

The system maintains **two parallel indexes** with different purposes:

| File | Location | Count | Authority | Purpose |
|------|----------|-------|-----------|---------|
| `proposal-index.md` | `/home/hermes/proposals/proposal-index.md` | 267 entries | Derived (ai-superpower API sync) | Active proposal tracking |
| `proposal-docs-index.md` | `/home/hermes/proposals/proposal-docs-index.md` | ~1000 entries | Standalone archive | PRD document registry |

**Key insight**: Proposals can appear in `proposal-docs-index.md` but NOT in `proposal-index.md` — meaning the PRD was registered as a document but never entered the ai-superpower API tracking system, or was dropped from it.

## Search Protocol (Mandatory)

When a proposal ID is not found in `proposal-index.md`, follow this order:

```bash
# Step 1: Check main index (authoritative for active proposals)
grep "P-20260419-005" /home/hermes/proposals/proposal-index.md
# Expected: either results (found) or no output (not in main index)

# Step 2: Check archive index
grep "P-20260419-005" /home/hermes/proposals/proposal-docs-index.md
# If found here → proposal exists as PRD but not in main tracking

# Step 3: Check PRD file existence
ls /home/hermes/proposals/workspace-pm/proposals/P-20260419-005-prd.md
# If file exists → PRD is valid, proposal needs to enter ai-superpower system

# Step 4: Check proposals.json (data source)
grep "P-20260419-005" /home/hermes/proposals/proposals.json
# If found → proposal is in data store but not indexed
```

## Decision Tree

```
proposal-index.md has entry?
  YES → Proposal is active. Use ai-superpower API for updates.
  NO
    └── proposal-docs-index.md has entry?
        YES → Proposal exists as PRD but not in main tracking.
              Check workspace-pm/proposals/ for PRD file.
              Decision: either (a) enter into ai-superpower, or (b) archive.
        NO
            └── workspace-pm/proposals/P-YYYYMMDD-XXX-prd.md exists?
                YES → PRD file exists but never registered in any index.
                      Proposal is orphaned. Needs investigation.
                NO → Proposal does not exist. Ghost request.
```

## Case Study from 2026-05-28

| Proposal | proposal-index.md | proposal-docs-index.md | PRD File |
|----------|-------------------|------------------------|----------|
| P-20260419-005 | ❌ Not found | ✅ Found (line 95) | ✅ Exists |
| P-20250416-003 | ❌ Not found | ✅ Found (line 15) | ✅ Exists |

Both proposals have valid PRD files in `workspace-pm/proposals/`, both appear in the archive index, but neither is in the main index. This means:
- P-20260419-005: Status `prd_pending_confirmation` (created 4/19, never confirmed or progressed)
- P-20250416-003: Status `active` (created 4/16, APK never built)

Neither was synced into the ai-superpower tracking system properly.

## Corrective Actions

### For proposals with valid PRD files but missing from main index:

1. **Option A**: Enter proposal into ai-superpower system properly
   ```bash
   ai-superpower proposal create --title "..." --owner "..." --project-id "..." --stage "intake"
   ```

2. **Option B**: Archive the proposal (if no longer pursuing)
   - Update proposal-docs-index.md with `[ARCHIVED]` tag
   - Do NOT delete the PRD file

### Do NOT:
- Create a new proposal ID for a document that already has a valid P-YYYYMMDD-XXX
- Manually edit `proposal-index.md` to add a missing entry (creates index/store divergence)
- Delete the PRD file assuming the proposal is gone

## Related

- `references/proposal-index-missing-entry.md` — Covers the case where a proposal IS in proposals.json but not in proposal-index.md
- `references/proposals-json-structure.md` — proposals.json as data source