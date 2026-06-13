# Ghost Proposal: Functional Descendant Recovery

When a cron job fires for `P-YYYYMMDD-XXX` but the API returns 404, yet `proposals.json` has a minimal entry (`title=""`, only `id/status/priority/created` fields), the original proposal is a **ghost**. However, a **functional descendant** (a newer proposal with the same title/project_id/tech stack) may exist and should be updated instead of creating a new proposal.

## Diagnostic Workflow

### Step 1: Verify ghost in proposals.json

```python
import json
with open("/home/hermes/proposals/proposals.json") as f:
    data = json.load(f)
for project in data.get("projects", []):
    for prop in project.get("proposals", []):
        if prop.get("id") == "P-YYYYMMDD-XXX":
            print(json.dumps(prop, indent=2))
```

Ghost pattern: `title=""`, only `id/status/priority/created/assignee` fields present.

### Step 1b: Restore ghost title in proposals.json (if needed)

If the ghost's `title` field is empty (""), **it is valid and necessary to edit proposals.json directly** to restore it. This is the one exception to the "never edit proposals.json directly" rule.

```python
import json
from datetime import datetime

json_path = "/home/hermes/proposals/proposals.json"
with open(json_path) as f:
    data = json.load(f)

for proj in data["projects"]:
    if proj.get("id") == "PRJ-YYYYMMDD-XXX":
        for i, p in enumerate(proj["proposals"]):
            if p.get("id") == "P-YYYYMMDD-XXX" and p.get("title") == "":
                p["title"] = "ai-subscription-大模型调用层升级-llm-design-dev"  # restore original title
                p["updated"] = datetime.now().strftime("%Y-%m-%d")
                with open(json_path, "w") as f2:
                    json.dump(data, f2, indent=2, ensure_ascii=False)
                print("✓ Restored title + updated timestamp")
                break
```

The `.hermes/proposals/proposals/proposals.json` copy auto-syncs with `/home/hermes/proposals/proposals.json`, so editing either path updates both.

### Step 2: Search API for functional descendant by project_id + title keyword

```python
import urllib.request, json
api_key = open("/home/hermes/.ai-superpower/config.toml").read().split('key = "')[1].split('"')[0]

# List proposals for the same project
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/proposals?project_id=PRJ-YYYYMMDD-XXX&page=1&page_size=50",
    headers={'X-API-Key': api_key}
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
for p in result.get('items', []):
    # Find proposals with matching title keywords
    if '大模型调用层' in p.get('title', ''):
        print(f"{p.get('id')}: {p.get('title')} [{p.get('status')}]")
```

### Step 3: Identify the correct descendant to update

The functional descendant typically has:
- Same `project_id`
- Same or similar title (e.g., "ai-subscription大模型调用层升级" ← original was "ai-subscription-大模型调用层升级-llm-design-dev")
- Same tech stack in notes
- `tech_expectations: timeout-approved` already set (from the original timeout cron)
- `prd_confirmation: timeout-approved` already set
- Either `status: intake` or `stage: in_dev`

### Step 4: Walk the state machine to reach target status

The `status` field follows strict transitions. You CANNOT jump from `intake` to `in_dev`. Must step through:

```
intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev
```

```python
import urllib.request, json
api_key = open("/home/hermes/.ai-superpower/config.toml").read().split('key = "')[1].split('"')[0]
proposal_id = "P-YYYYMMDD-XXX"  # the functional descendant

transitions = [
    "clarifying",
    "prd_pending_confirmation", 
    "approved_for_dev",
    "in_dev"
]

for target_status in transitions:
    payload = json.dumps({"status": target_status}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/proposals/{proposal_id}/status",
        data=payload, method='PUT',
        headers={'X-API-Key': api_key, 'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        print(f"✓ {proposal_id} → {target_status}")
    except urllib.error.HTTPError as e:
        print(f"✗ {proposal_id} → {target_status}: {e.code} {e.reason}")
        break
```

### Step 5: Verify final state

```python
req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/proposals/{proposal_id}",
    headers={'X-API-Key': api_key}
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## Key Rules

1. **NEVER** `POST` a new proposal to replace a ghost — this orphans the original ID
2. **ALWAYS** walk the state machine one step at a time (no skipping)
3. The functional descendant already has `tech_expectations: timeout-approved` and `prd_confirmation: timeout-approved` set from the original proposal's timeout processing — these fields do NOT need to be re-set
4. The `stage` field may already be `in_dev` even when `status` is `intake` — check both; update both to match your target

## Example

Original: `P-20260502-017` (ghost, API 404) — "ai-subscription-大模型调用层升级-llm-design-dev"
Functional descendant: `P-20260524-013` (exists in API) — "ai-subscription大模型调用层升级"

Both have:
- `tech_expectations: timeout-approved`
- `prd_confirmation: timeout-approved`
- Same project: `PRJ-20260412-008` (ai-subscription)
- Same tech stack: `ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair`