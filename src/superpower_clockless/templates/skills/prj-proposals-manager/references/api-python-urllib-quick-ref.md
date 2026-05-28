# MCP Bridge — ai-superpower via superpower-clockless

All ai-superpower operations go through the `superpower-clockless mcp` bridge. Use the MCP tools listed below — **not** direct HTTP, `curl`, or Python `urllib`.

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `health` | Check ai-superpower server health |
| `project_list` | List projects (search, page_size) |
| `project_get` | Get project by ID |
| `proposal_list` | List proposals (project_id, search, page_size) |
| `proposal_get` | Get proposal by ID |
| `proposal_create` | Create proposal (title, owner, project_id, stage) |
| `proposal_update_fields` | Update proposal fields |
| `proposal_update_status` | Transition proposal status |

## Why Not curl/Python urllib?

- `curl` frequently times out even with `--max-time 10`
- Python urllib `timeout=10` is stable (0.2–0.5s response) but requires boilerplate
- MCP tools provide a clean JSON interface with consistent error handling

## MCP Tool Patterns

### project_list
```
Tool: project_list
Arguments: {"search": "keyword", "page_size": 50}
```

### proposal_get
```
Tool: proposal_get
Arguments: {"proposal_id": "P-YYYYMMDD-XXX"}
```

### proposal_create
```
Tool: proposal_create
Arguments: {"title": "My Proposal", "owner": "coordinator", "project_id": "PRJ-20260523-001", "stage": "approved_for_dev"}
```

### proposal_update_fields
```
Tool: proposal_update_fields
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"tech_expectations": "confirmed", "notes": "iteration notes"}}
```

### proposal_update_status
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_dev"}
```

## Server Down Recovery

If MCP tools return connection errors:

```bash
# Check if superpower-clockless can reach the server
superpower-clockless doctor

# Check ai-superpower process
ps aux | grep -E 'uvicorn|fastapi' | grep -v grep

# Check ports
ss -tlnp | grep -E '8000|8001'
```