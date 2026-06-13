# SOUL.md ↔ Skill Spec Alignment Checklist

When the prj-proposals-manager skill version changes (e.g. v4 → v5.0.0), profile SOUL.md files often drift behind. This reference documents the specific items to audit and the v5-baseline values to enforce.

## When to run

- After rsync'ing a new skill version into `profiles/*/skills/`
- Before declaring a session-start sync "complete"
- When troubleshooting inconsistent state machine behavior between profiles
- After creating a new profile
- When boss reports state transition errors that don't match the skill spec

## Scope: which files to audit

```bash
# All SOUL.md under hermes home and per-profile directories
find ~/.hermes ~/.hermes/profiles -maxdepth 4 -name "SOUL.md" -type f
```

Default + onepc + vedio profiles each have their own SOUL.md. All must align.

## Audit items (v5.0.0 baseline + 2026-06-13 expansion)

| # | Item | v5 baseline (correct) | Drift to flag |
|---|------|----------------------|----------------|
| 1 | Status state machine | `in_test_acceptance → test_failed/accepted → deployed → delivered` | `in_acceptance → needs_revision` (v4 era) |
| 2 | `in_tdd_test` state | **Deprecated — must be removed** | Present in pre-2026-05-24 state machine (v4 era) |
| 3 | Data source | `ai-superpower API` is authoritative | `CSV is the data source` (v4 era) |
| 4 | Field model | `stage` (coarse) + `status` (fine) dual fields | Single `status` field conflated (v4 era) |
| 5 | Proposal ID model | `PRJ-` (project) + `P-` (proposal) dual IDs | `P-` only (v4 era) |
| 6 | API tool entry | `mcp_aisp.py <tool>` (unified CLI) | `proposal_manager_cli.py` (CSV-direct, v4 era) |
| 7 | API port | `http://127.0.0.1:8000` (verify with `ss -tlnp \\| grep 8000`) | `127.0.0.1:8001` (config.toml socket path) |
| 8 | Index regeneration | `sync-proposals-to-website.py` / `mcp_aisp.py get-sync-status` auto | Manual edit of `proposal-index.md` |
| 9 | Duplicate sections | Only ONE `## 提案状态` per SOUL | Two duplicates common after partial migration |
| 10 | Changelog entry | New row at top of `## 更新日志` table dated for the spec version | Missing or dated for old spec |
| 11 | **Owner field value** | `--owner "小墨"` (matches SOUL.md COORDINATOR) | `--owner "coordinator"` (role name, not actual owner) — flagged 2026-06-13 |
| 12 | **State machine diagram completeness** | ASCII diagram must show `test_failed → in_test_acceptance` loop arrow (re-test path) | Diagram only shows `test_failed` without return arrow — flagged 2026-06-13 |
| 13 | **Unattended mode auto-approval** | All confirmation gates (Step 4 PRD, Step 5 Tech, Step 10 Research, Step 11 Deployment) must have `#### ⚡ In Unattended Mode` subsection with `prd_confirmation="timeout-approved"` / `tech_expectations="timeout-approved"` pattern | Only Step 4/5 covered; Step 10/11 missing — flagged 2026-06-13 |
| 14 | **Delivery report 4 必含字段** | SKILL.md must mention all 4: 项目链接 / 部署分支 / 项目ID / 提案ID in `## Communication Style` section + reference to `delivery-report-template.md` | Missing entire section — flagged 2026-06-13 |
| 15 | **Iteration sizing (5-30 任意)** | SKILL.md must have `## Iteration Sizing` section with range table (5/10-20/30) and "read fresh per session" rule | Missing — flagged 2026-06-13 |
| 16 | **Communication language (中文)** | SKILL.md must have `## Communication Style` section stating Chinese output for narrative text, English for code/paths | Missing — flagged 2026-06-13 |
| 17 | **MCP-only access (no aisp CLI / REST)** | All API examples use `mcp_aisp.py`; legacy `aisp proposal/project` CLI and `PUT /api/...` REST reserved for emergency only | Skill examples still use `aisp proposal get` in 4+ places — flagged 2026-06-13 |

## Pitfall: API 8001 vs 8000 confusion

`~/.ai-superpower/config.toml` has `socket_path = "127.0.0.1:8001"` as a Unix-socket placeholder, NOT the actual HTTP port. The HTTP server (`ai-superpower run`) binds 8000 by default. Both can coexist (socket mode vs HTTP mode) but for agents calling REST/MCP, **port 8000 is correct**.

```bash
ss -tlnp | grep -E '8000|8001'   # confirm actual listeners
```

## Audit procedure (SOUL.md + SKILL.md)

```bash
# 1. Scan for v4-era artifacts in any SOUL.md
for f in $(find ~/.hermes ~/.hermes/profiles -maxdepth 4 -name "SOUL.md" -type f); do
  echo "=== $f ==="
  grep -nE "in_acceptance|in_tdd_test|needs_revision|CSV 是数据源|proposal_manager_cli\.py proposal (add|update)" "$f" \
    | head -20
done

# 2. Detect duplicate state machine sections
for f in $(find ~/.hermes ~/.hermes/profiles -maxdepth 4 -name "SOUL.md" -type f); do
  count=$(grep -c "^## 提案状态" "$f")
  if [ "$count" -gt 1 ]; then
    echo "DUPLICATE in $f: $count '## 提案状态' sections"
  fi
done

# 3. Check changelog recency
for f in $(find ~/.hermes ~/.hermes/profiles -maxdepth 4 -name "SOUL.md" -type f); do
  echo "=== $f ==="
  grep -A 3 "^## 更新日志" "$f" | head -6
done

# 4. (2026-06-13) SKILL.md audit — owner field, unattended sections, delivery report fields
SKILL="$HOME/.hermes/skills/prj-proposals-manager/SKILL.md"
echo "=== $SKILL owner field check ==="
grep -n -- "--owner \"coordinator\"" "$SKILL" || echo "OK: no 'coordinator' owner"

echo "=== $SKILL state machine diagram check ==="
grep -E "test_failed.*re-test|re-test.*test_failed" "$SKILL" || echo "MISSING: test_failed loop arrow"

echo "=== $SKILL In Unattended Mode coverage ==="
grep -c "In Unattended Mode" "$SKILL"
# Should be 4+ (Step 4, 5, 10, 11)

echo "=== $SKILL 4 必含字段 check ==="
for field in "项目链接" "部署分支" "项目 ID" "项目ID" "提案 ID" "提案ID"; do
  grep -q "$field" "$SKILL" && echo "OK: $field" || echo "MISSING: $field"
done

echo "=== $SKILL Iteration Sizing section check ==="
grep -q "## Iteration Sizing" "$SKILL" && echo "OK" || echo "MISSING"

echo "=== $SKILL Communication Style section check ==="
grep -q "## Communication Style" "$SKILL" && echo "OK" || echo "MISSING"
```

## Automated audit script

For routine audits, use `scripts/skill-soul-audit.py <skill-path>` (default: `prj-proposals-manager`).
The script automates the 17-item check and prints a structured report with exit code 0 (clean) / 1 (conflicts found).

**When to run it**:
- After any new boss preference is recorded in USER.md
- After any SOUL.md update
- Before merging a new skill version
- When boss reports behavior that "doesn't match what USER.md says" (silent drift)

**Output shape** (abridged):
```
[CHECK 11/17] Owner field value...
  PASS: --owner "小墨" found in 3 places
  PASS: no --owner "coordinator" anti-pattern

[CHECK 13/17] Unattended mode auto-approval...
  PASS: 4 In Unattended Mode subsections (Step 4, 5, 10, 11)
  WARN: Step 6/7/8 do not have explicit unattended subsections (acceptable for non-gate steps)

[CHECK 17/17] MCP-only access...
  PASS: 191 mcp_aisp.py references
  WARN: 8 aisp CLI references (in 3 reverse-example docs — acceptable)
```

## Pitfall: API 8001 vs 8000 confusion

For each SOUL.md needing update, two patches are typically needed:

**Patch 1 — State machine block**

```
old:
intake → clarifying → prd_pending_confirmation → approved_for_dev
→ in_dev → in_acceptance → accepted → delivered
                                                    ↓
                                            needs_revision → in_dev

new:
intake → clarifying → prd_pending_confirmation → approved_for_dev
→ in_dev → in_test_acceptance → test_failed → in_test_acceptance
                                         ↓
                                   accepted → deployed → delivered
```

**Patch 2 — Data sync rule**

```
old:
**CSV 是数据源，proposal-index.md 是派生索引。**
每次新建/更新提案，必须**先写 proposals.csv，再用 proposal_manager_cli.py**...

new:
**ai-superpower API 是唯一权威数据源**；proposals.csv 是 `backup_api.py` 派生的备份；
proposal-index.md 是 `aisp sync-to-index` 派生的索引。
所有 CRUD 与状态机转移必须通过 API，禁止直接编辑 CSV。
```

**Patch 3 — Changelog entry (insert at top of table)**

```
| YYYY-MM-DD | 对齐 prj-proposals-manager vX.Y.Z：<具体变更> |
```

## Stage vs status field distinction (v5 新增)

`stage` is the coarse category (`proposal`, `in_dev`, `accepted`, `delivered`, etc.) — mostly metadata, auto-syncs with `status` changes.

`status` is the fine state machine (`intake`, `clarifying`, `prd_pending_confirmation`, `approved_for_dev`, `in_dev`, `in_test_acceptance`, `test_failed`, `accepted`, `deployed`, `delivered`) — authoritative, transition-enforced.

**Critical**:
- `intake` is a valid `status` value but NOT a valid `stage` value at creation.
- `mcp_aisp.py create-proposal --stage intake` returns "Invalid stage: intake".
- Use `--stage approved_for_dev` at creation; the proposal starts with `status="intake"` and the agent walks it through the state machine.

## Verified history

- **2026-06-13 (early)**: Aligned default profile (`小墨`) and onepc profile (`小白`) SOUL.md files with v5.0.0 spec
  - Found 1 duplicate state machine section in onepc (lines 60-66 + 84-91)
  - Found 1 deprecated `in_tdd_test` state in onepc
  - Found 1 port reference drift (8001 → 8000)
  - Both files patched; verified by scanning for v4-era patterns; changelog entries added
  - No conflicts found in MEMORY.md or USER.md (memory is already v5-aware via "MCP 6-layer + dedup" note from 2026-06-10)

- **2026-06-13 (later)**: Expanded checklist from 10 → 17 items to cover boss preferences and workflow completeness
  - Found 7 new conflict categories by running 2 audit sessions back-to-back on `prj-proposals-manager` SKILL.md:
    - #11 Owner field value (`coordinator` → `小墨`)
    - #12 State machine diagram completeness (missing test_failed → in_test_acceptance loop)
    - #13 Unattended mode auto-approval (Step 10/11 missing `#### ⚡ In Unattended Mode` subsections)
    - #14 Delivery report 4 必含字段 (项目链接/部署分支/项目ID/提案ID)
    - #15 Iteration sizing (5-30 任意, 缺失指引)
    - #16 Communication language (中文交流, 缺失指引)
    - #17 MCP-only access (残留 `aisp proposal get` CLI 引用)
  - All 7 conflicts fixed inline; new audit items added to this checklist
  - New support file: `scripts/skill-soul-audit.py` (automated 17-item checker)
  - Pattern: the audit-then-fix workflow is class-level (re-runnable), not one-off. Future sessions should consult this checklist and the script when boss asks for "检查 X 技能描述是否和 soul、memory、user 存在冲突的地方" — the answer is always: run the 17-item check, patch the conflicts, re-verify.

## Related

- SKILL.md § Bug Prevention table → "SOUL.md / MEMORY.md conflicts after skill sync" (parent pitfall, brief)
- `references/dual-proposal-index-architecture.md` — proposal-index.md vs proposal-docs-index.md divergence (different problem)
- `references/mcp-vs-rest-migration.md` — v4 → v5 endpoint/tool mapping (broader migration)
