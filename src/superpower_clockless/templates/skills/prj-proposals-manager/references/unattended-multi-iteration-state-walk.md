# Unattended Multi-Iteration State Walk Pattern

> **🚫 v5.0.0+: All API operations go through `mcp_aisp.py` (MCP).** This document previously used `urllib`; it has been rewritten to use `mcp_aisp.py` exclusively. The old `urllib` patterns are preserved in `references/api-python-urllib-quick-ref.md` for one-off cron diagnostics only.

When boss says "无人值守模式" (unattended mode) and "进行 N 次迭代后停止" (do N iterations then stop), the coordinator must:

1. **Auto-approve all confirmation gates immediately** (no cron countdowns, no boss wait)
2. Create N separate proposals (one per iteration)
3. Walk each proposal through the full status state machine
4. Update each proposal's status via `mcp_aisp.py` between phases

This pattern was validated 2026-06-04 in ai-novel-assistant Round 7 (9-iteration Direction A) and refined 2026-06-13 to use MCP exclusively.

## ⚡ Unattended Mode: PRD/Tech Gate Auto-Approval

**This is the most important rule for unattended mode.** At `create-proposal` time:

```bash
# Set both gates to timeout-approved in the same create call
mcp_aisp.py create-proposal \
  --title "Direction A Iter N: <feature>" \
  --owner "coordinator" \
  --project-id "PRJ-XXXXXXXX-XXX" \
  --stage "approved_for_dev" \
  --prd-confirmation "timeout-approved" \
  --tech-expectations "timeout-approved" \
  --notes "mode: unattended | Round N | Direction A"
```

**Effect**:
- No 5-minute PRD confirmation countdown cron fires
- No 3 rounds of tech-expectations clarifying questions
- No 5-minute tech-expectations countdown cron
- The proposal is "born approved" — coordinator can proceed directly to dev

**Boss override**: re-set `prd_confirmation="pending"` or `tech_expectations="pending"` in the next session, and the proposal re-enters the interactive flow.

## API Status State Machine (must walk in order)

```
intake → clarifying → prd_pending_confirmation → approved_for_dev
       → in_dev → in_test_acceptance → accepted
```

Each transition uses `mcp_aisp.py update-proposal-status` with the next state. **The state machine is enforced** — direct jumps like `intake → in_dev` return HTTP 400 `Invalid status transition: intake → in_dev`.

### `stage` vs `status` — both fields must be set correctly

| Field | Set at | Valid values at creation |
|-------|--------|--------------------------|
| `stage` | At creation **and** via `mcp_aisp.py update-proposal-fields` | `"approved_for_dev"`, `"proposal"`, etc. (NOT `"intake"`) |
| `status` | Walked via `mcp_aisp.py update-proposal-status` only | `"intake"`, `"clarifying"`, etc. |

At creation, the safest combo is `stage="approved_for_dev"` + `status="intake"`. Then walk status forward, never touching stage again.

## Iteration Loop (one cycle) — MCP-only

```bash
# 1. Find next free ID for today (the API auto-assigns on create, but pre-checking helps)
TODAY=$(date +%Y%m%d)
PREFIX="P-${TODAY}-"
EXISTING=$(mcp_aisp.py list-proposals --project-id PRJ-XXXXXXXX-XXX 2>/dev/null \
            | grep -oE "${PREFIX}[0-9]{3}" | sort -u)
MAX_N=$(echo "$EXISTING" | sed "s/${PREFIX}//" | sort -n | tail -1)
NEW_N=$(printf "%03d" $(( ${MAX_N:-0} + 1 )))

# 2. Create proposal with unattended-friendly defaults (auto-approve gates)
RESULT=$(mcp_aisp.py create-proposal \
  --title "Direction A Iter N: <feature>" \
  --owner "coordinator" \
  --project-id "PRJ-XXXXXXXX-XXX" \
  --stage "approved_for_dev" \
  --prd-confirmation "timeout-approved" \
  --tech-expectations "timeout-approved" \
  --notes "mode: unattended | Round N | Direction A")
ACTUAL_ID=$(echo "$RESULT" | grep -oE "P-${TODAY}-[0-9]{3}" | head -1)
# ⚠️ API may rewrite the ID — always read the actual ID from the response

# 3. Walk state machine: intake → ... → accepted
for NEXT in clarifying prd_pending_confirmation approved_for_dev in_dev in_test_acceptance accepted; do
  echo "  → $NEXT"
  mcp_aisp.py update-proposal-status --proposal-id "$ACTUAL_ID" --status "$NEXT"
done

# 4. Set acceptance & notes via fields (separate from status)
mcp_aisp.py update-proposal-fields \
  --proposal-id "$ACTUAL_ID" \
  --acceptance "accepted" \
  --notes "V${N} <feature>. ${TESTS_PASSED} tests, ${PASS_RATE}% pass."
```

## What Goes Wrong If You Skip Steps

| Skip | Symptom |
|------|---------|
| Set `stage: "intake"` at creation | HTTP 422 `"Invalid stage: intake"` — `intake` is a status, not a stage |
| Try `status: "in_dev"` from `intake` | HTTP 400 `"Invalid status transition: intake → in_dev"` — must walk forward |
| Try `update-proposal-fields` with `status: "..."` | Field update silently ignores `status` (only `update-proposal-status` accepts it) |
| Skip `prd-confirmation: "timeout-approved"` | 5-min cron countdown fires; proposal blocks waiting for boss (defeats unattended mode) |
| Skip `tech-expectations: "timeout-approved"` | 3 rounds of clarifying questions + 5-min cron countdown (defeats unattended mode) |

## When To Stop the Loop

```bash
# Boss says "进行 9 次迭代后停止" (stop after 9 iterations)
REMAINING=$(( TARGET_N - ITERATION_COUNT ))
if [ "$REMAINING" -le 0 ]; then
  echo "✅ $TARGET_N iterations complete. Stopping."
  exit 0
else
  echo "剩余 $REMAINING 次迭代。自动选择方向 A 继续..."
  # Continue the loop
fi
```

In unattended mode, after each delivery you auto-select the first option (Direction A) and continue. The loop terminates when boss says "停止" (stop) or when N iterations are complete.

## Reference Implementation: 9-Iteration Round 7 (ai-novel-assistant)

| Iter | Proposal ID | Stage | Direction | 6-design fusion |
|------|-------------|-------|-----------|-----------------|
| 1 | P-20260604-004 | accepted | Direction A: nanobot + thunderbolt | async MessageBus + pipeline |
| 2 | (next) | pending | Direction B: chatdev | role specialization |
| 3 | (next) | pending | Direction C: claude-code | tool/permission system |
| 4 | (next) | pending | Direction D: generic-agent | autonomous goal pursuit |
| 5 | (next) | pending | Direction E: ruflo | hierarchical decomposition |
| 6 | (next) | pending | Unified | orchestrator integrating 5 designs |
| 7 | (next) | pending | E2E test | pipeline + chaos test, ≥99% coverage |
| 8 | (next) | pending | Perf | build size + runtime optimization |
| 9 | (next) | pending | Deploy | docs + GitHub Pages verification |

Each iteration:
1. Read existing code in target module (avoid breaking existing tests)
2. Write new module + comprehensive tests (≥99% coverage, 100% pass)
3. Verify build doesn't break (`npx tsc --noEmit` for type checks, `npx vitest run` for unit tests)
4. `git add + commit` with V{N} prefix
5. Update proposal status through `mcp_aisp.py` to `accepted`
6. Auto-select next direction (A) and continue

## Why MCP and not direct CLI/REST?

`mcp_aisp.py` is the unified CLI that wraps all 18 ai-superpower MCP tools. Every call goes through `aisp mcp --transport=stdio`, which:
- Enforces auth, lifespan, lock management, state machine validation
- Logs every operation to the audit log via JSON-RPC frames
- Provides a single canonical path for SPA + agent + cron

Direct `urllib`/REST is no longer the recommended access path. It's preserved in `references/api-python-urllib-quick-ref.md` for **cron diagnostic scripts only** (e.g., `scripts/check-proposal-cron-state.py` reads key from `~/.ai-superpower/config.toml` when MCP is unreachable).
