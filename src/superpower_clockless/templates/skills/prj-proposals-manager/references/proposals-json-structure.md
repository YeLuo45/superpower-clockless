# proposals.json Structure & Ghost Proposal Diagnosis (v4 era)

> ⚠️ **v5 MIGRATION NOTE (2026-06-08)**: This file documents v4 `proposals.json` structure (project-centric JSON mirror in `YeLuo45/proposals-manager` GitHub repo). In v5.0.0, **proposals.json is retired** and the data lives in **ai-superpower's `~/.ai-superpower/proposals.csv`** (one row per proposal, flat CSV with audit log + flock). The "ghost proposal" pattern still exists but with a different verification path.
> 
> v5 equivalent diagnostic for ghost proposals:
> 1. Verify in CSV: `grep -n "P-..." /home/hermes/proposals/proposals.csv`
> 2. Verify via MCP: `mcp_aisp.py get-proposal --proposal-id P-...`
> 3. If CSV has it but MCP says 404 → proposal is "orphaned" in MCP database but valid in CSV → conclude `[DONE]` without re-creating (would orphan original ID)
> 
> See `references/mcp-connection-troubleshooting.md` for the full v5 ghost-proposal flow.
> 
> ---

## File Structure

`proposals.json` is NOT a flat list of proposals. It is a **project-centric mirror** with two physical copies that stay in sync:

```json
{
  "projects": [          // top-level key is "projects" (plural)
    {
      "id": "PRJ-20260412-008",
      "name": "ai-subscription",
      "proposals": [      // proposals are nested inside each project
        {
          "id": "P-20260502-017",
          "title": "",
          "status": "in_dev",
          ...
        }
      ]
    }
  ],
  "lastUpdate": "2025-05-24"
}
```

**Physical locations** (both auto-synced, edit either one):
- `/home/hermes/proposals/proposals.json` — main working copy
- `/home/hermes/.hermes/proposals/proposals/proposals.json` — mirrored copy

**Reading it**: Iterate `data['projects']`, then `project['proposals']`.

**Writing it**: Requires finding the parent project, locating the proposal entry, and writing back the whole projects array.

## Ghost Proposal: What the Investigation Found

| Check | Result |
|-------|--------|
| `proposals.json` | Contains `P-20260502-017` entry with `status: in_dev` |
| `GET /api/proposals/P-20260502-017` | `404 Not Found` — not in live API |
| `PUT /api/proposals/P-20260502-017/fields` | `404 Not Found` — cannot update |
| `proposal-index.md` | No entry for `P-20260502-017` |
| Backup CSV (`proposals.csv`) | `P-20260502-017` not present — never backed up to CSV |

**Conclusion**: `P-20260502-017` is a ghost — exists in local JSON mirror only, never reached the live API.

## Working API Patterns (Python)

### Read API key from config
```python
api_key = open("/home/hermes/.ai-superpower/config.toml").read().split('key = "')[1].split('"')[0]
```

### GET single proposal (will 404 if ghost)
```python
import urllib.request, json
api_key = open("/home/hermes/.ai-superpower/config.toml").read().split('key = "')[1].split('"')[0]
url = "http://127.0.0.1:8001/api/proposals/P-20260502-017"
req = urllib.request.Request(url, headers={'X-API-Key': api_key})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
```

### PUT fields (will 404 if ghost)
```python
payload = json.dumps({"tech_expectations": "timeout-approved"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/proposals/P-20260502-017/fields",
    data=payload, method='PUT',
    headers={'X-API-Key': api_key, 'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
```

### PUT status (state machine transition)
```python
payload = json.dumps({"status": "in_dev"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/proposals/P-20260502-017/status",
    data=payload, method='PUT',
    headers={'X-API-Key': api_key, 'Content-Type': 'application/json'}
)
```

### List proposals for a project
```python
url = "http://127.0.0.1:8001/api/proposals?project_id=PRJ-20260412-008&page_size=200"
req = urllib.request.Request(url, headers={'X-API-Key': api_key})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
for p in data['items']:
    print(p['id'], p['status'])
```

### Search proposals (URL-encode Chinese characters)
```python
import urllib.parse
search_term = urllib.parse.quote("大模型")
url = f"http://127.0.0.1:8001/api/proposals?search={search_term}&page_size=200"
```

## Quick Ghost Diagnosis (Single Shot)

```python
import urllib.request, json
api_key = open("/home/hermes/.ai-superpower/config.toml").read().split('key = "')[1].split('"')[0]
for pid in ['P-20260502-017']:
    url = f'http://127.0.0.1:8001/api/proposals/{pid}'
    req = urllib.request.Request(url, headers={'X-API-Key': api_key})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            print(f'{pid}: API {r.status}')
    except urllib.error.HTTPError as e:
        print(f'{pid}: API {e.code} HTTPError (GHOST)')
```

## Key Lesson

`proposals.json` is a **local mirror** — it can contain entries that were never synced to the live API. The API is the only source of truth for updates. When JSON and API diverge, believe the API error and follow the ghost proposal resolution path.