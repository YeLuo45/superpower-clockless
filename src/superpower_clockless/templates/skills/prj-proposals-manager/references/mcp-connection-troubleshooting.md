# MCP Connection Troubleshooting (v5.0.0)

**Status**: NEW in v5.0.0 (2026-06-08)
**Scope**: All MCP-related connection issues for ai-superpower ↔ SPA/agent

This reference covers the **MCP-specific failure modes** that emerged during Phase 2 of P-20260608-004. Use this when a v5 issue surfaces that the v4 references don't cover.

---

## 1. Server not running

**Symptom**: `curl http://127.0.0.1:8000/mcp/` returns `Connection refused` or hangs.

**Diagnosis**:
```bash
ps aux | grep "aisp run\|aisp mcp" | grep -v grep
# or
lsof -i :8000
```

**Fix**: Start the server.
```bash
# Web UI + MCP (single port 8000)
aisp run --port 8000

# MCP only on different port (e.g., 8765)
aisp mcp --transport=http --host 0.0.0.0 --port 8765
```

**Why this happens in dev**: The `aisp run` from production worktree (default `master` branch checkout) may be running an **older** ai-superpower that doesn't have MCP mounted. Check `cd /home/hermes/ai-superpower && git log --oneline -1` against the dev-env version.

---

## 2. 307 Temporary Redirect (missing trailing slash)

**Symptom**: `curl -X POST http://127.0.0.1:8000/mcp` returns 307, not the expected 200. With strict HTTP clients (Python `urllib`), this raises `HTTPError`.

**Root cause**: FastAPI mount + Starlette redirect normalize `/mcp` → `/mcp/`. The actual endpoint requires the trailing slash.

**Fix**:
- **Browser fetch**: auto-follows 307, no change needed in `useMcp.js` (but log shows the redirect for debugging)
- **Python urllib**: use `Request(url + '/mcp/')` directly, or `urlopen(req)` will fail with 307 unless you use a custom redirect handler
- **curl**: use `-L` to follow redirects, or hit `/mcp/` directly

**Verification**:
```bash
# This should return 200 with serverInfo:
curl -X POST http://127.0.0.1:8000/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

**v5 reference**: SKILL.md "MCP 端点" section + ai-superpower SKILL.md "FastAPI mount FastMCP 的三个坑".

---

## 3. 500 "Task group is not initialized" (lifespan race)

**Symptom**: First `/mcp/` request returns 500 with `RuntimeError: Task group is not initialized. Make sure to use run().` in server logs.

**Root cause**: Inner Starlette's `lifespan` (which starts the session manager) is supposed to run when the first request hits the sub-app. If something prevents that, you get this error.

**Wrong fix attempt** (DO NOT USE): Wrapping the parent app's lifespan to run `mcp._session_manager.run()` — **this breaks 88 tests** because multiple `TestClient` instances race on the shared task group.

**Correct fix** (already in `ai-superpower-dev/src/ai_superpower/server.py`): keep the inner Starlette's own lifespan, ensure `streamable_http_path="/"` so the path doesn't double up.

**Diagnosis if still failing**:
```bash
cd /home/hermes/ai-superpower-dev
grep -A5 "streamable_http_path" src/ai_superpower/mcp_server.py
# Should show: streamable_http_path="/"

grep -A3 "make_asgi_app" src/ai_superpower/mcp_server.py
# Should show: returns inner with mcp.session_manager.run() lifespan
```

If both look correct but the error persists, restart the server (the session manager task group may have been corrupted by a previous TestClient run).

---

## 4. 401/403 Unauthorized (X-API-Key mismatch)

**Symptom**: MCP tool call returns `Unauthorized` or `{"error": "Invalid API key"}`.

**Diagnosis**:
```bash
# Get the real key from config
grep '^key' ~/.ai-superpower/config.toml
# Compare with what the client is sending

# SPA: check localStorage in browser DevTools
# localStorage.getItem('mcp_api_key')
```

**Fix**:
- **SPA**: Settings UI → 重新输入 X-API-Key (should be 32-char hex from config.toml)
- **agent**: `export AI_SUPERPOWER_API_KEY=$(grep '^key' ~/.ai-superpower/config.toml | sed 's/.*= *"\(.*\)"/\1/')`
- **stdio transport**: `aisp mcp --transport=stdio` reads from `AI_SUPERPOWER_API_KEY` env var automatically

---

## 5. vite dev proxy 404

**Symptom**: SPA in dev mode (`npm run dev`, http://localhost:5173) shows MCP tools loading failure. Browser DevTools Network shows `GET /mcp/.../tools/list` 404.

**Root cause**: `vite.config.js` proxy misconfigured or wrong target.

**Fix**:
```js
// vite.config.js — should have:
server: {
  proxy: {
    '/mcp': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      // Important: don't rewrite the path
    }
  }
}
```

**Verify proxy is up**:
```bash
# After npm run dev:
curl -X POST http://localhost:5173/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}'
# Should proxy to 8000 and return 200 (or follow redirect)
```

---

## 6. CORS error (production build served from different origin)

**Symptom**: `Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS policy`.

**Root cause**: Production deployment serves SPA from `https://yeluo45.github.io/prj-proposals-manager/` but ai-superpower runs on a different origin/port.

**Fix options**:
1. **Same-origin**: Deploy ai-superpower behind a reverse proxy that exposes `/mcp` on the same origin as the SPA. Recommended for production.
2. **CORS allow-list**: In ai-superpower config, add the SPA origin to allowed origins. (Requires server-side change.)
3. **Dev proxy only**: The `vite.config.js` proxy handles this in dev mode. For production, you need option 1 or 2.

**Status (2026-06-08)**: CORS config not yet implemented. SPA in production will fail MCP connection until reverse proxy or CORS allow-list is added.

---

## 7. SPA localStorage corrupted

**Symptom**: Settings UI shows "Connection failed" even with correct URL + key. Re-entering credentials doesn't help.

**Fix**:
1. Open browser DevTools → Application → Local Storage
2. Delete keys: `mcp_server_url`, `mcp_api_key`
3. Refresh page
4. Re-enter credentials in Settings UI

---

## Quick diagnostic script

```bash
#!/bin/bash
# diagnose_mcp.sh — quick health check for ai-superpower MCP
URL="${1:-http://127.0.0.1:8000}"
KEY=$(grep '^key' ~/.ai-superpower/config.toml | sed 's/.*= *"\(.*\)"/\1/')

echo "1. Server reachable?"
curl -s -o /dev/null -w "  /health: %{http_code}\n" $URL/health

echo "2. /mcp/ endpoint accepts initialize?"
INIT_RESP=$(curl -s -X POST $URL/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"diag","version":"1"}}}')
echo "  $INIT_RESP" | head -c 200
echo

echo "3. With API key, list_proposals call works?"
curl -s -X POST $URL/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "X-API-Key: $KEY" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_proposals","arguments":{"page_size":1}}}' | head -c 300
echo
```

Run this from any shell to validate the MCP stack end-to-end.
