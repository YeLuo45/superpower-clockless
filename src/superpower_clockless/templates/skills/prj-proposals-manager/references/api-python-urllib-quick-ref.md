# ai-superpower API Quick Reference (Python urllib) — **DEPRECATED v5.0.0+**

> 🚫 **DEPRECATED in v5.0.0+.** The recommended access method is **`mcp_aisp.py`** (MCP protocol). This file is preserved for **cron diagnostic scripts only** (e.g., `scripts/check-proposal-cron-state.py` reads the key from `~/.ai-superpower/config.toml` and uses urllib when the MCP server is unreachable).
>
> **For all new code: use `mcp_aisp.py <tool>`** — see `references/mcp-aisp-cli.md` for the unified CLI reference. One CLI call replaces all urllib/curl/requests code in this file.
>
> If you find yourself reaching for urllib outside of a cron diagnostic, **stop and switch to `mcp_aisp.py`**. Reasons: MCP enforces auth, lifespan, lock management, state machine validation, and audit logging — direct REST/urllib bypasses all of these.
> 
> ---

## Migration Cheat Sheet (urllib → mcp_aisp.py)

| urllib pattern | mcp_aisp.py replacement |
|----------------|--------------------------|
| `api_get("/api/proposals?page_size=200")` | `mcp_aisp.py list-proposals --page-size 200` |
| `api_get(f"/api/proposals/{pid}")` | `mcp_aisp.py get-proposal --proposal-id <pid>` |
| `api_put(f"/api/proposals/{pid}/fields", {...})` | `mcp_aisp.py update-proposal-fields --proposal-id <pid> --field1 val1 --field2 val2` |
| `api_post("/api/proposals", {...})` | `mcp_aisp.py create-proposal --title "..." --owner "..." --project-id "..." --stage "..."` |
| `api_put(f"/api/proposals/{pid}/status", {"status": "..."})` | `mcp_aisp.py update-proposal-status --proposal-id <pid> --status <status>` |

**Single-line rule**: any time the v4 urllib code in this file is mentioned, the modern replacement is one `mcp_aisp.py` call. No state, no auth header, no URL encoding.

---

## Why Python urllib over curl (v4 era — still works for smoke tests)

> **Note**: This section is kept for historical context. In v5.0.0+, the default is `mcp_aisp.py`. urllib/curl is reserved for cron diagnostic scripts (see file header).

- Python urllib `timeout=10` is stable (0.2-0.5s response)
- API responses are JSON, urllib handles it cleanly
- `~/.ai-superpower/config.toml` has the key — read directly (no need to source a missing env file)

## Core Pattern

```python
import urllib.request, json

API_KEY = "dfd374c2e1c2443292ec8f8c791a92a5"
BASE = "http://127.0.0.1:8000"

def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"X-API-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def api_put(path, data):
    req = urllib.request.Request(f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        method="PUT")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def api_post(path, data):
    req = urllib.request.Request(f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())
```

## Key Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| List proposals (paginated) | `/api/proposals?page_size=200` | GET |
| Get single proposal | `/api/proposals/{id}` | GET |
| Update proposal fields | `/api/proposals/{id}/fields` | PUT |
| Create proposal | `/api/proposals` | POST |
| Get project | `/api/projects/{id}` | GET |
| Update project fields | `/api/projects/{id}/fields` | PUT |

## Common Operations

### List proposals for a project
```python
data = api_get("/api/proposals?page_size=200")
items = data.get('items', [])
culty = [p for p in items if p.get('project_id') == 'PRJ-20260516-002']
from collections import Counter
print(Counter(p.get('stage') for p in culty))
```

### Update proposal (single field — most reliable)
```python
api_put(f"/api/proposals/{pid}/fields", {"stage": "accepted"})
```

### Update proposal (multiple fields)
```python
api_put(f"/api/proposals/{pid}/fields", {
    "stage": "accepted",
    "acceptance": "accepted",
    "last_update": "2026-05-27",
    "notes": "V97 complete, commit 7992c9c"
})
```

### Create proposal
```python
api_post("/api/proposals", {
    "title": "cultivation-simulator V98 ...",
    "owner": "小墨",
    "status": "intake",
    "project_id": "PRJ-20260516-002",
    "project_name": "cultivation-simulator",
    "stage": "approved_for_dev",  # only this stage works at creation
    "notes": "无人值守模式 | Direction A | ...",
    "last_update": "2026-05-27"
})
```

## Known Limitations

1. **curl vs urllib vs mcp_aisp.py**: Always prefer `mcp_aisp.py` for new code. urllib via `execute_code` tool is reserved for cron diagnostic scripts (when MCP server is down). curl is for one-off debugging only.
2. **/fields 400 Bad Request**: Multi-field updates fail if ANY field fails validation. Single-field updates succeed more often.
3. **prd_confirmation/tech_expectations**: Don't include special characters (Chinese, spaces, `≥`, etc.) — causes 400
4. **Project /fields**: `/api/projects/{id}/fields` → 404. Use PUT `/api/projects/{id}` with single field
5. **Proposal creation stage**: Only `approved_for_dev` works. Others return 422.
6. **page_size max**: 200 works; 500 returns 422 Unprocessable Entity