# ai-superpower API Quick Reference

## Why Python urllib over curl
- curl frequently times out even with `--max-time 10`
- Python urllib `timeout=10` is stable (0.2-0.5s response)
- API responses are JSON, urllib handles it cleanly

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

1. **curl vs urllib**: Always prefer Python urllib via `execute_code` tool
2. **/fields 400 Bad Request**: Multi-field updates fail if ANY field fails validation. Single-field updates succeed more often.
3. **prd_confirmation/tech_expectations**: Don't include special characters (Chinese, spaces, `≥`, etc.) — causes 400
4. **Project /fields**: `/api/projects/{id}/fields` → 404. Use PUT `/api/projects/{id}` with single field
5. **Proposal creation stage**: Only `approved_for_dev` works. Others return 422.
6. **page_size max**: 200 works; 500 returns 422 Unprocessable Entity