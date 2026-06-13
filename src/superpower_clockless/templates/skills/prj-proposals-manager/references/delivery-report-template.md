# Delivery Report Template (boss required format)

> Boss requires every end-of-session delivery report to contain the four mandatory fields below. Reports missing any of them are considered incomplete and may be rejected.

## Mandatory fields (4)

| 字段 (Field) | 含义 | 示例 |
|---|---|---|
| **项目链接** (Project link) | The live URL the user/boss can visit | `https://yeluo45.github.io/prj-proposals-manager/` |
| **开发分支 / 部署分支** (Deploy branch) | The branch that triggered deployment, or that contains the final code | `master` (auto-deploys to gh-pages) / `gh-pages` (direct) |
| **项目 ID** (Project ID) | The project entity ID | `PRJ-20260422-001` |
| **提案 ID** (Proposal ID) | The proposal iteration ID(s) — one or more for multi-iter | `P-20260604-004`, `P-20260605-005` (etc.) |

## Format: Concise table + version list + Git chain

Boss prefers **table-based** reports, not walls of text. The minimum structure:

```
## 交付汇总 (Delivery Summary)

| 字段 | 值 |
|---|---|
| 项目链接 | https://... |
| 部署分支 | master (→ gh-pages via workflow) |
| 项目 ID | PRJ-... |
| 提案 ID | P-... |
| 完成时间 | 2026-06-13 14:30 |
| 模式 | 无人值守 / 交互 |

## 版本列表 (Version List)

| Version | Direction | 6-design fusion | 状态 |
|---|---|---|---|
| V1 | A: claude-code | ... | accepted |
| V2 | B: nanobot | ... | accepted |
| ... |

## Git 链 (Git Chain)

- master: <commit-sha> ← <commit-sha-1> ← <commit-sha-2>
- gh-pages: <commit-sha> (auto-deployed from master)
```

## 语言 / Style

- **Language**: 中文 (Chinese) for narrative text. Code, file paths, tool names, and command output stay in English.
- **No verbose process narration** — skip the "step 1, step 2, step 3" walkthrough. Show inputs, actions, and outputs in tables.
- **End every report with**: the next-iteration options (Direction A/B/C/D), auto-selected as Direction A in unattended mode.

## Why this format

Boss's audit/audit-mind preference means every delivery must be:
1. **Reproducible** — Git chain + commit SHAs lets boss verify the exact state
2. **Locatable** — Project ID + Proposal ID lets boss look up the proposal in proposal-index.md / audit log
3. **Deployable** — Deploy branch + Project link lets boss visit the live result
4. **Concise** — Table-based, no paragraph walls

## Reference

This template is referenced from:
- `SKILL.md` § Communication Style (boss preference)
- `SKILL.md` § Step 11 In Unattended Mode (auto-generate this report)
- `references/soul-alignment-checklist.md` (SOUL drift audit — verify all SOUL.md files mention this template)
