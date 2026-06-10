# Duplicate Project Workflow (2026-06-10)

## When to use

The duplicate scan + merge workflow is for **legacy data cleanup**. After ~6 months
of ai-superpower usage, the projects.csv had accumulated multiple entries with
the same name (different git_repos, case variants, etc.). This makes
`list-projects` noisy and proposal→project mapping ambiguous.

The exact-name-match guard (added 2026-06-10) prevents new duplicates from being
created, but existing duplicates must be merged manually via this workflow.

## Decision tree

```
Boss: "register a proposal for <X>"
   │
   ▼
Coordinator: list-projects --search "X"  +  scan-duplicate-projects
   │
   ├─ Exact-name hit → REUSE existing PRJ-ID
   │  (create-project will auto-return _existing: true)
   │
   ├─ Case-different hit ("X" vs "x", "X" vs "X ")
   │  → Present to boss: "Found 2 projects with same name:
   │      • PRJ-...  X  (created 2026-06-07, 4 proposals)
   │      • PRJ-...  x  (created 2026-06-08, 0 proposals)
   │    Which is canonical? Merge other into canonical?"
   │    Boss picks → merge-projects
   │
   └─ No hit → safe to create-project
```

## MCP CLI commands

```bash
# 1. Scan
mcp_aisp.py scan-duplicate-projects

# 2. Inspect a specific group
mcp_aisp.py list-proposals --project-id PRJ-...   # see what's in target
mcp_aisp.py get-project --project-id PRJ-...       # see metadata

# 3. Merge (with confirmation)
mcp_aisp.py merge-projects \
  --target-id PRJ-20260610-001 \
  --source-id PRJ-20260610-002 \
  --delete-source true

# 4. Verify
mcp_aisp.py get-project --project-id PRJ-20260610-002   # → 404 "Project not found"
mcp_aisp.py scan-duplicate-projects                      # count -1
```

## REST API (for SPA / Web UI)

```bash
# List duplicate groups
curl -H "X-API-Key: $KEY" \
  "http://127.0.0.1:8765/api/projects/duplicates?case_insensitive=true"

# Merge
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"target_id":"PRJ-...","source_id":"PRJ-...","delete_source":true}' \
  "http://127.0.0.1:8765/api/projects/merge"
```

## Web UI workflow

1. Open http://127.0.0.1:8765/web/projects
2. Click **🔍 Scan Duplicates** button (top-right)
3. Modal shows all duplicate groups with target/source radio buttons
4. For each group, pick:
   - **Keep (target)** = the canonical project to keep
   - **Merge from (source)** = the project to absorb and delete
5. Click **🔀 Merge source → target** (red button)
6. Confirm in dialog
7. Modal auto-rescans; group disappears

## What gets moved during merge

| Item | Behavior |
|---|---|
| Proposals from source | `project_id` updated to target_id, `last_update` set to today |
| Source project row | Deleted (when `--delete-source true`, default) |
| Audit log | UPDATE events per moved proposal + DELETE event per removed project |
| Target project | Untouched (existing proposals/fields stay) |
| Other projects | Untouched |

## Edge cases

| Case | Behavior |
|---|---|
| `target_id == source_id` | ValueError |
| `target_id` not found | ValueError "Target project not found" |
| `source_id` not found | ValueError "Source project not found" |
| Source has 0 proposals | `merged_proposals: 0`, source still deleted (if requested) |
| Source has been deleted between scan and merge | 404 from get_project; safe to retry |
| `delete_source: false` | Source row kept (with 0 proposals, since they all moved) |

## MCP/REST tool reference

| Path | Method | Tool name | Purpose |
|---|---|---|---|
| `/api/projects/duplicates` | GET | `scan_duplicate_projects` | List duplicate groups |
| `/api/projects/merge` | POST | `merge_projects` | Move proposals + delete source |
