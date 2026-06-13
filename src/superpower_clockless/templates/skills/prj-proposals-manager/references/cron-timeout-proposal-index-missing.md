# Cron Timeout: proposal-index.md Missing Entry — But proposals.json Already Correct

## Scenario
A cron job fires to update a proposal's fields (e.g., `Technical Expectations: pending → timeout-approved`) and transition status (`approved_for_dev → in_dev`). The task references `proposal-index.md` but finds no entry for the target proposal ID.

## Diagnosis Flow

### Step 1 — Verify proposals.json directly
```bash
grep -A5 '"id": "P-YYYYMMDD-XXX"' /home/hermes/proposals/proposals.json
```
This is the **authoritative data source**. If the proposal exists here with correct values, the data layer is already updated.

### Step 2 — Verify the actual index path
```bash
ls -la /home/hermes/proposals/proposal-index.md
grep -n "P-YYYYMMDD-XXX" /home/hermes/proposals/proposal-index.md
```
If `grep` returns empty (0 matches), the proposal was never indexed — this is a pre-existing gap, not a new problem.

**Key insight**: The index is **derived**, not authoritative. Proposals that were never indexed will appear missing from the index regardless of their actual data state.

### Step 3 — Check if the cron path was wrong
The cron job task referenced `/home/hermes/.hermes/proposals/proposal-index.md` (wrong path).
The correct path is `/home/hermes/proposals/proposal-index.md` (without `.hermes/`).

Also verify the symlink:
```bash
ls -la /home/hermes/.hermes/proposals
# lrwxrwxrwx ... proposals -> /home/hermes/proposals
```
So `/home/hermes/.hermes/proposals/` is a symlink to `/home/hermes/proposals/`. The canonical root is `/home/hermes/proposals/`.

### Step 4 — Confirm status in proposals.json
If `proposals.json` already shows the target status (e.g., `in_dev`) and the target fields are already set correctly, **no further action is needed at the data layer**.

## Decision Tree

```
Cron fires for P-XXXXXX-XXX → proposal-index.md entry missing
        │
        ▼
Is P-XXXXXX-XXX in proposals.json with correct values?
        │
   YES  │  NO
    │   │   └── Proposal truly missing — this is a ghost proposal.
    │        Report: [DONE] {id} {action} failed — ghost proposal.
    ▼
Is status already the target status?
        │
   YES  │  NO
    │   │   └── Need API update — but index gap is separate issue.
    ▼
Data layer task already complete — report [DONE].
```

## Conclusion Protocol

When `proposals.json` already has correct values but `proposal-index.md` has no entry:
- **Do NOT** attempt to manually add an index entry
- **Do NOT** re-run API field updates (data is already correct)
- **Do NOT** run sync scripts as a corrective measure — index will regenerate
- **Report**: `[DONE] P-YYYYMMDD-XXX {field} timeout处理已完成 — proposals.json 中状态已为 in_dev，proposal-index.md 无该条目(历史遗留不同步)，数据源无需更新`

## Related
- `references/api-404-json-valid.md` — API 404 but JSON valid (orphaned in API, not index)
- `Bug Prevention` table entry: "Cron job fires but proposal not in proposal-index.md"