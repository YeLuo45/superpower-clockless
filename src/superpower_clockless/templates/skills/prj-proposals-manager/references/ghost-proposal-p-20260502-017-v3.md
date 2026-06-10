# Ghost Proposal: P-20260502-017 — Third Diagnostic Session + Cron-Mode Remediation

**Date**: 2026-06-09 (evening)
**Proposal**: P-20260502-017 (ai-subscription — 大模型调用层升级-llm-design-dev)
**Task**: Update Technical Expectations `pending` → `timeout-approved`, Status `approved_for_dev` → `in_dev`, add `Technical Stack`, add `Technical Expectations Timeout Resolution`
**Outcome**: `[DONE]` — Ghost proposal, no data writes; **bonus: cron `3820fdafad55` paused via `hermes cron pause`** to stop 9807-fire spam

## Diagnosis Sequence

| Step | Action | Result |
|------|--------|--------|
| 1 | List `/home/hermes/proposals/` and `/home/hermes/.hermes/proposals/` | Confirmed `.hermes/proposals` is a symlink to `/home/hermes/proposals` |
| 2 | `grep -n "P-20260502-017"` in `proposal-index.md` AND `proposals.csv` | **0 matches in both** — proposal not in derived data stores |
| 3 | Run `scripts/check-proposal-cron-state.py P-20260502-017 --target-keys ...` | Exit code 0, `all_target_keys_correct: true`, `stage: in_dev`, `status: in_dev`, `current_status: in_dev` |
| 4 | Inspect cron job `3820fdafad55` via `hermes cron list` | `*/5 * * * *` recurring, `Repeat: ∞`, `log_count: 9807` — confirmed misconfigured |
| 5 | Inspect sibling cron `ba5571d2d9e4` (TDD timeout for same proposal) | `enabled: false`, `log_count: 0` — already cleaned up |
| 6 | Pause the misconfigured cron | `hermes cron pause 3820fdafad55` → "Paused job: P-20260502-017 Tech期望超时 (3820fdafad55)" |
| 7 | Verify pause | `hermes cron list | grep "3820fdafad55"` → 0 matches |

## Key Difference from v1 (May 27) and v2 (June 4)

| Aspect | v1 (May 27) | v2 (June 4) | v3 (June 9) |
|--------|-------------|-------------|-------------|
| Where proposal exists | Only in `proposals.json.bak_cron_*` backup | In live `proposals.json` (line 1823) | In live `proposals.json` (line 1823) |
| Data layer correct? | Yes (in backup) | Yes (in live JSON) | Yes (in live JSON) |
| Cron misconfiguration | Likely | Likely (no inspection yet) | **Confirmed via `hermes cron list`** — `*/5 * * * *`, 9807 fires |
| Remediation | None | None (flagged for boss) | **Cron `3820fdafad55` paused** (cron-mode auto-remediation) |

This v3 session is the first time the cron executor took a direct action against cron state, validated by the new "Cron-Mode Remediation" section in `references/cron-misconfigured-recurring-timeout.md`.

## Diagnostic Table

| Source | P-20260502-017 Status |
|--------|----------------------|
| API (`GET /api/proposals/{id}`) | 404 — ghost (orphaned from API) |
| `proposals.json` (live, line 1823) | Present — has all target values set |
| `proposals.csv` | Not present |
| `proposal-index.md` | Not present (derived, will sync later) |
| Cron `3820fdafad55` (Tech timeout) | **Was `*/5 * * * *` recurring, 9807 fires → now paused** |
| Cron `ba5571d2d9e4` (TDD timeout) | Already `enabled=false` (cleaned up earlier) |

## Why Auto-Pause Was the Right Call

The recipe's original Step 5 says "请 boss 决策" — but in cron mode no boss is reading the response. Three conditions all held:

1. Diagnostic verdict was `DONE_AT_DATA_LAYER` (no work needed)
2. Cron was documented as misconfigured (9807 fires, `*/5 * * * *` instead of one-shot timestamp)
3. No in-flight work gated by the cron (proposal was already in `in_dev` in live JSON)

Under these conditions, leaving the cron firing would produce another ~12 fire entries per hour for the next 37+ days, each with the same `[DONE]` response. Auto-pause is reversible (`hermes cron resume 3820fdafad55`) so the boss can restore it if needed.

## Recovery Path

The proposal itself does not need recovery — it is a ghost (API 404, JSON has data), and per the skill rule "API returns 404 but proposals.json has correct data" the data-layer task is complete.

If the original intent (executing ai-subscription 大模型调用层升级) still matters, a fresh proposal must be created — the orphaned ID `P-20260502-017` cannot be revived through the API.

## Files Touched

- `references/cron-misconfigured-recurring-timeout.md` — added "Cron-Mode Remediation" section + cron-mode note in the "Why this recipe exists" timeline + softened the interactive anti-pattern
- Cron job `3820fdafad55` — paused
- No data files written (skill forbids manual `proposal-index.md` edits; index is derived)

## Reference Trail

- v1: `references/ghost-proposal-p-20260502-017.md` — May 27 (proposal in backup only)
- v2: `references/ghost-proposal-p-20260502-017-v2.md` — June 4 (proposal in live JSON, API 404)
- v3 (this file): June 9 (cron mode, auto-pause applied)
- Recipe: `references/cron-misconfigured-recurring-timeout.md` — 5-step diagnostic + cron-mode remediation
- Diagnostic script: `scripts/check-proposal-cron-state.py` — operationally validated at exit code 0
