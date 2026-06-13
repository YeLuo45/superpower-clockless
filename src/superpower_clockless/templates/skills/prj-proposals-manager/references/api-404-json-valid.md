# API 404 but proposals.json Valid

> ⚠️ **v5 MIGRATION NOTE (2026-06-08)**:
> 
> This reference documents the v4 era when `proposals.json` (in `YeLuo45/proposals-manager` GitHub repo) was the authoritative store.
> 
> **v5.0.0 migration**: proposals.json has been retired. The new authoritative store is **ai-superpower's `~/.ai-superpower/proposals.csv` (CSV + flock + audit log)**, exposed via **MCP tools** at `/mcp` Streamable HTTP endpoint. SPA uses `useMcp.js`, agents use `aisp mcp --transport=stdio`.
> 
> The diagnostic pattern ("API 404 but data valid" → conclude DONE) **still applies** in v5, but verification commands changed:
> - v4: `grep -n "P-..." /home/hermes/proposals/proposals.json` + `GET /api/proposals/{id}`
> - v5: `grep -n "P-..." /home/hermes/proposals/proposals.csv` + `mcp_aisp.py get-proposal --proposal-id P-...`
> 
> See `references/mcp-connection-troubleshooting.md` for v5 patterns.
> 
> ---

**Symptoms**: `GET /api/proposals/P-YYYYMMDD-XXX` returns HTTP 404, but `proposals.json` contains an entry for that ID with correct field values.

**Root Cause**: Proposal is "orphaned" in the JSON mirror but absent from the live API database. Can occur after server restart, failed sync, or migration to new API format.

**Diagnosis**:
1. Read `proposals.json` around the ID: `grep -n "P-YYYYMMDD-XXX" /home/hermes/proposals/proposals.json`
2. Inspect 10–20 lines around the match — check `status`, `tech_expectations`, `tech_stack`, `notes`, `stage`
3. If all required fields are present and correct → data layer is complete

**Decision Tree**:

| proposals.json state | API state | Action |
|---------------------|-----------|--------|
| Has entry + correct values | 404 | Task already done — skip API, skip index edit |
| Has entry + incomplete/incorrect | 404 | Orphaned — do NOT POST replacement; use functional descendant or rollback |
| No entry | 404 | Proposal genuinely missing — create via API if appropriate |

**Do NOT**:
- POST a new proposal to replace the 404 entry — orphans the original ID and doubles count
- Manually add entry to `proposal-index.md` — it is derived, will sync later
- Run `sync-proposals-to-website.py` if missing — may not exist

**Do**:
- Verify JSON has all correct values → conclude data-layer task complete
- Report `[DONE]` — the data is already correct at source
- For cron timeout jobs: if all target fields already set in JSON, the timeout handler's work is already done

---

## Session Example (2026-05-27)

Cron job `P-20260502-017-tech-confirm` timeout handler was asked to:
- Set `tech_expectations: timeout-approved`
- Set `current_status: in_dev`
- Add `tech_stack: ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair`

`proposals.json` lines 1822–1839:
```json
{
  "id": "P-20260502-017",
  "title": "ai-subscription-大模型调用层升级-llm-design-dev",
  "status": "in_dev",
  "priority": "PRJ-20260412-008",
  "created": "ai-subscription",
  "updated": "2026-05-27",
  "assignee": "",
  "tech_expectations": "timeout-approved",
  "tech_expectations_timeout_resolution": "倒计时到期(2026-05-02)，默认通过处理",
  "current_status": "in_dev",
  "tech_stack": "ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair",
  "stage": "in_dev",
  "notes": "Technical Expectations Timeout Resolution: 倒计时到期(2026-05-02)，默认通过处理\nTechnical Stack: ai SDK + @ai-sdk/openai + @ai-sdk/anthropic + @ai-sdk/google + partial-json + jsonrepair"
}
```

All target fields already present and correct. API `GET` returned 404. **Conclusion**: task already done at data layer, no action needed.