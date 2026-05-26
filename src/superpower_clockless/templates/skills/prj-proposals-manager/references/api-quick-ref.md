# ai-superpower HTTP API Quick Reference

## Server Info

- **Actual port: 8001** (not 8000 — 8000 appears in legacy docs but server binds to 8001)
- Base URL: `http://127.0.0.1:8001/api` (also `http://localhost:8001/api`)
- Health endpoint: `http://127.0.0.1:8001/health`

## Server Startup

```bash
ai-superpower run   # 启动 HTTP server — 默认端口 8001
```

## API Key

From `~/.ai-superpower/config.toml`:
```toml
[api]
key = "dfd37469666776457eb593e3ded692a5"
```

## Quick Test

```bash
# 检查 server 状态
curl -s http://localhost:8001/api/health

# 列出项目
curl -s http://localhost:8001/api/projects \
  -H "X-API-Key: dfd37469666776457eb593e3ded692a5"

# 列出提案
curl -s http://localhost:8001/api/proposals \
  -H "X-API-Key: dfd37469666776457eb593e3ded692a5"
```

## Create Project

```bash
curl -s -X POST http://localhost:8001/api/projects \
  -H "X-API-Key: dfd37469666776457eb593e3ded692a5" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "project-name",
    "git_repo": "https://github.com/owner/repo",
    "description": "项目描述"
  }'
```

## Create Proposal

```bash
curl -s -X POST http://localhost:8001/api/proposals \
  -H "X-API-Key: dfd37469666776457eb593e3ded692a5" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "提案标题",
    "owner": "小墨",
    "project_id": "PRJ-20260524-001",
    "stage": "proposal",
    "notes": "备注"
  }'
```

**注意**：`stage` 值必须是 `VALID_PROPOSAL_STAGES` 中的值：
- `proposal` (对应状态机的 intake 阶段)
- `ideation`, `development`, `research`
- `in_dev`, `in_acceptance`, `accepted`, `delivered`, `active`
- `approved_for_dev`, `prd_pending_confirmation`

`"intake"` 不是合法的 stage 值。

## Update Proposal Status

```bash
curl -s -X PUT http://localhost:8001/api/proposals/P-20260524-001/status \
  -H "X-API-Key: dfd37469666776457eb593e3ded692a5" \
  -H "Content-Type: application/json" \
  -d '{"status": "clarifying"}'
```

## CLI vs HTTP

| 命令 | 传输 | Server 要求 |
|------|------|-------------|
| `ai-superpower project list` | Unix socket (`/tmp/ai-superpower.sock`) | 必须 socket 模式 |
| `curl http://localhost:8000/api/...` | HTTP/TCP | 必须 HTTP 模式 |

当 server 运行在 HTTP 模式（`ai-superpower run`）而 CLI 报 socket 错误时，直接用 curl 调用 HTTP API 即可。

## Sync to proposal-index.md

```bash
ai-superpower sync-to-index
```

如果 socket 问题导致 CLI 失败，可以用 Python 直接调用 API 获取数据后手动更新 proposal-index.md。