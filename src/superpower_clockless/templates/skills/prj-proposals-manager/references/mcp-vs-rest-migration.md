# MCP vs REST Migration Guide (v4 → v5)

**Status**: NEW in v5.0.0 (2026-06-08)
**Migration driver**: P-20260608-004 / P-20260608-005 (ai-superpower adds MCP server, prj-proposals-manager switches to MCP client)

This reference is the v4→v5 migration cheat sheet for code, prompts, and operations. Use it whenever you encounter v4 patterns that need to be translated to v5 MCP.

---

## 1. Data source authority

| v4 (deprecated) | v5 (current) |
|---|---|
| `YeLuo45/proposals-manager` GitHub repo → `data/proposals.json` | **ai-superpower `~/.ai-superpower/proposals.csv`** (CSV + flock + audit) |
| SPA reads/writes `useGitHub.js` (api.github.com + PAT) | SPA reads/writes **useMcp.js** (MCP at `/mcp/`) |
| Agent reads/writes via `urllib`/`curl` to `ai-superpower/api/*` REST | Agent reads/writes via **`mcp_aisp.py <tool>`** (unified CLI that wraps `aisp mcp --transport=stdio`) |

**v5 truth**: ai-superpower is the only source of truth. proposals.json has been **retired** (not deleted from git history, but no longer authoritative).

---

## 2. Tool mapping (v4 REST → v5 MCP)

| v4 REST endpoint | v5 MCP tool | Notes |
|---|---|---|
| `GET /api/health` | `health_check` (or just `GET /health`) | Both work in v5 |
| `GET /api/projects?search=X` | `list_projects(search=X)` | Pagination via `page` + `page_size` |
| `GET /api/projects/{id}` | `get_project(project_id=id)` | |
| `POST /api/projects` | `create_project(name, git_repo, description)` | **`check_project_duplicate` first** in v5 (v4 didn't have this) |
| `PUT /api/projects/{id}` | `update_project(project_id, updates={...})` | `updates` is a dict (v4 was form-encoded) |
| `DELETE /api/projects/{id}` | `delete_project(project_id)` | Requires `allow_delete=true` in config |
| `GET /api/proposals?project_id=X` | `list_proposals(project_id=X)` | |
| `GET /api/proposals/{id}` | `get_proposal(proposal_id=id)` | |
| `POST /api/proposals` | `create_proposal(title, owner, project_id, stage)` | **Only `stage="approved_for_dev"` accepted at creation** |
| `PUT /api/proposals/{id}/fields` | `update_proposal_fields(proposal_id, fields={...})` | **`fields` is a dict, not flat params** |
| `PUT /api/proposals/{id}/status` | `update_proposal_status(proposal_id, status)` | **Strict linear state machine** |
| `DELETE /api/proposals/{id}` | `delete_proposal(proposal_id)` | Requires `allow_delete=true` |
| `GET /api/proposals/audit?page=X` | `get_audit(page=X)` | Same data, different interface |
| `GET /api/stats` | `get_stats()` | |
| `GET /api/sync/config` | `get_sync_config()` | |
| `POST /api/sync/trigger` | `export_sync()` | |
| `GET /api/sync/status` | `get_sync_status()` | |
| — | `set_api_key(key)` | NEW in v5 — for stdio transport only |

**Net change**: v4 had ~13 REST endpoints, v5 has 20 MCP tools (added 7: `check_project_duplicate`, `delete_project`, `delete_proposal`, `merge_proposals_by_project`, `set_api_key`, `get_stats`, `export_sync`).

---

## 3. Auth: API key

| v4 | v5 |
|---|---|
| `X-API-Key: <32-hex>` HTTP header | `X-API-Key: <32-hex>` HTTP header (same!) |
| `SUPERPOWER_API_KEY` env var | `AI_SUPERPOWER_API_KEY` env var (renamed) |
| Stored in `~/.ai-superpower/config.toml` `[api].key` | Stored in `~/.ai-superpower/config.toml` `[api].key` (same) |
| SPA: `localStorage.github_token` | SPA: `localStorage.mcp_api_key` |

**Action**: rename env var in any launch scripts, `~/.bashrc`, `~/.zshrc`, etc.

---

## 4. SPA integration

| v4 | v5 |
|---|---|
| `useGitHub.js` (custom api.github.com client) | `useMcp.js` (`@modelcontextprotocol/sdk` browser client) |
| `localStorage.github_token` | `localStorage.mcp_server_url` + `localStorage.mcp_api_key` |
| Settings UI: GitHub PAT input | Settings UI: Server URL + X-API-Key input + Test Connection |
| CORS: needed for api.github.com (GitHub CORS allows it) | CORS: dev proxy via vite (works in dev); production needs reverse proxy |
| Build artifact includes `data/proposals.json` | Build artifact has no data — all from MCP at runtime |

**Migration steps (for any project using prj-proposals-manager v4 patterns)**:
1. `npm install @modelcontextprotocol/sdk`
2. Copy `useMcp.js` from prj-proposals-manager repo (or write your own wrapper)
3. Update all `useGitHub` imports to `useMcp`
4. Add vite dev proxy for `/mcp` → ai-superpower port
5. Update Settings UI to ask for `mcp_server_url` + `mcp_api_key` instead of `github_token`
6. Test: `npm run dev` → open http://localhost:5173 → Settings → Test Connection

---

## 5. Verification commands (v4 → v5)

| What you want to verify | v4 command | v5 command |
|---|---|---|
| Proposal exists in data layer | `grep -n "P-..." /home/hermes/proposals/proposals.json` | `grep -n "P-..." /home/hermes/proposals/proposals.csv` |
| API can read proposal | `curl /api/proposals/{id}` | `mcp_aisp.py get-proposal --proposal-id P-...` |
| Project exists | `curl /api/projects/{id}` | `mcp_aisp.py get-project --project-id PRJ-...` |
| Update a proposal field | `curl -X PUT /api/proposals/{id}/fields -d "..."` | `mcp_aisp.py update-proposal-fields --proposal-id P-... --field1 val1 --field2 val2` |
| Move to next state | `curl -X PUT /api/proposals/{id}/status -d "status=..."` | `mcp_aisp.py update-proposal-status --proposal-id P-... --status <status>` |
| List MCP tools (smoke test) | n/a (REST has no tool list) | `mcp_aisp.py --list` (calls `aisp mcp --transport=stdio` then `tools/list` under the hood) |
| Trigger sync | `curl -X POST /api/sync/trigger` | `aisp sync now` (or MCP `export_sync`) |
| Server health | `curl /api/health` | `curl /health` (v5 still has this) |
| List MCP tools (smoke test) | n/a (REST has no tool list) | `aisp mcp --transport=stdio` then `tools/list` |

---

## 6. State machine differences (v4 → v5)

**v4** (loose — could jump or repeat):
```
intake → clarifying → prd_pending_confirmation → approved_for_dev
                                                       ↓
             in_tdd_test ←────────────────────── in_dev
                  ↓                                   ↓
         in_test_acceptance ←──────────────── needs_revision
                ↓      ↓
          accepted   test_failed
              ↓
          deployed → delivered
```
- 12 states (had `needs_revision`, `in_tdd_test` for iterative loops)
- Could go `in_dev → in_tdd_test → in_test_acceptance` (loop)
- Could go `in_test_acceptance → in_dev` (revision)

**v5** (strict linear):
```
intake → clarifying → prd_pending_confirmation → approved_for_dev
                                                       ↓
              in_test_acceptance ←────────────────────── in_dev
                   ↓      ↓
             accepted   test_failed
                 ↓
             deployed → delivered
```
- 10 states (removed `needs_revision`, `in_tdd_test`)
- `in_dev` is the start of development (no test-first loop)
- `test_failed` is a terminal state from `in_test_acceptance` (must restart from `in_dev`)
- Strict linear: each transition is its own MCP call, no skips

**Migration action**: update any code that used `in_tdd_test` or `needs_revision`. Re-validate that all current proposals have valid v5 states (`mcp_aisp.py list-proposals --page-size 200` should return proposals with valid stages only). Use `mcp_aisp.py update-proposal-fields` to fix any orphaned v4 stages.

---

## 7. Rejected v4 patterns (do NOT use in v5)

- ❌ Direct CSV access (proposals.csv is MCP-managed, not agent-editable)
- ❌ `curl -X PUT /api/proposals/{id}/fields -d "stage=in_dev"` (use `update_proposal_status` instead)
- ❌ `curl -X POST /api/proposals -d "stage=in_dev"` (create must use `stage=approved_for_dev`)
- ❌ Modifying `data/proposals.json` in `YeLuo45/proposals-manager` (the file is retired)
- ❌ Reading GitHub `proposals.json` as the data source (it's a historical artifact, no longer authoritative)
- ❌ Setting `SUPERPOWER_API_KEY` env var (renamed to `AI_SUPERPOWER_API_KEY`)

---

## 8. What's the same

- ai-superpower server, port 8000 default, `~/.ai-superpower/config.toml` for config
- X-API-Key auth header (value preserved, env var renamed)
- CSV files in `~/.ai-superpower/` (proposals.csv, projects.csv, audit log)
- proposal-index.md is still derived (regenerate via `aisp sync-to-index`)
- The multi-agent workflow (Coordinator / PM / Dev / Test Expert) — only the data layer changed
- The state machine concept (still intake → delivered, just stricter v5)

---

## 9. Rollback plan (if MCP fails in production)

If the v5 MCP integration fails and you need to fall back to v4 patterns:

1. **Revert prj-proposals-manager**: `git checkout v4.5.0 -- src/hooks/useGitHub.js src/App.jsx src/pages/ProjectDetailPage.jsx vite.config.js`
2. **Re-enable v4 data source**: restore `YeLuo45/proposals-manager` repo as authoritative
3. **Point SPA back to GitHub API**: change `useMcp` to `useGitHub`, restore `data/proposals.json` build artifact
4. **Disable MCP server**: remove the `mcp_server.py` mount from `ai-superpower/src/ai_superpower/server.py`

**Caveat**: rollback loses the v5 benefits (single source of truth, audit log, MCP multi-consumer). Only do this for emergency. Better: fix the MCP issue and stay on v5.

---

## See also

- `references/mcp-connection-troubleshooting.md` — 7 MCP failure modes with fixes
- `references/api-quick-ref.md` — v4 REST API quick ref (kept for legacy smoke tests)
- `references/api-python-urllib-quick-ref.md` — v4 Python urllib patterns
- `references/ai-superpower-architecture.md` — ai-superpower v5 architecture overview
- ai-superpower SKILL.md § "MCP 端点" — server-side MCP setup
