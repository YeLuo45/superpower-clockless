# CLI vs API Data Source Divergence

## Problem

`proposal_manager_cli.py` (CLI) and `ai-superpower` API serve the same proposal management purpose but read from **different data sources**:

| Tool | Data Source | Behavior |
|------|-------------|----------|
| CLI `proposal_manager_cli.py` | `/home/hermes/.hermes/proposals/project_proposal_mapping.csv` (84 bytes, headers only — empty) | Reports "No projects", "Project does not exist" |
| API `http://127.0.0.1:8001` | `proposals.json` | Returns projects and proposals correctly |

This means:
- `ai-superpower project list` → "No projects" (CLI)
- `GET /api/projects` → returns project objects (API)
- `proposal_manager_cli.py proposal add --project-id PRJ-YYYYMMDD-XXX` → "Project does not exist" (CLI)
- `GET /api/proposals?project_id=PRJ-YYYYMMDD-XXX` → may return 0 items even though project exists (API inconsistency)

## Symptoms

1. CLI reports project doesn't exist, but API confirms it does:
   ```
   [proposal-manager] ERROR: 项目不存在: PRJ-20260412-008
   ```
2. API proposal queries by project_id return 0 items despite project existing with `proposal_count > 0`
3. CLI JSON output fails to parse (`exit 2`)

## Root Cause

- CLI reads from `project_proposal_mapping.csv` which is empty (84-byte header-only file)
- API reads from `proposals.json` which has full data
- These two data stores are not synchronized

## Implication for Workflow

When the skill says to use the CLI, the CLI may not work because its data source is empty/out-of-sync. The API should be used as the authoritative source. The CLI is essentially non-functional when `project_proposal_mapping.csv` is empty.

## Resolution Path

1. **Always use the API** for proposal CRUD operations (create, update, status transitions)
2. **Do not rely on CLI** for proposal management — it is broken when its CSV is empty
3. **Investigate** why `project_proposal_mapping.csv` is empty — the sync mechanism between API (proposals.json) and CLI (CSV) is broken
4. **CLI project list** exits with code 0 but prints "暂无项目" — this is a silent failure, not an error code that indicates a real problem