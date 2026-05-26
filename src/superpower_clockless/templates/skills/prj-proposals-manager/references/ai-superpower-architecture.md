# ai-superpower: Anti-Tamper Proposal API Engine

> **When to use this reference**: When building new proposal-management tooling, evaluating anti-tamper strategies, or operating ai-superpower in production.

## Why ai-superpower Exists

The old CSV-only system (`proposal_manager_cli.py`) had **no protection against direct CSV tampering**. Multiple incidents (2026-05-17 through 2026-05-22) showed a clear pattern:

| Incident | Root Cause | Outcome |
|----------|-----------|---------|
| subagent rewrite proposals.csv | `csv.DictWriter writerows()` full rewrite | 92 rows permanently deleted |
| `die()` wipe | Error handler called `write_csv([])` | CSV zeroed out |
| execute_code direct patch | No enforcement, just convention | CSV drift from index |
| CLI dual-path writes | `~/.hermes/proposals/` != `/home/hermes/proposals/` | Data invisible to git |

**The core problem**: CSV was the data source but had no enforcement mechanism preventing direct writes.

## ai-superpower Architecture

```
ai-superpower API Server (FastAPI + uvicorn)
  X-API-Key Header Authentication
  All mutation goes through Pydantic models
  State machine validation on every write
                        |
                        V
  storage.py — CSV Storage Layer
  - fcntl.LOCK_EX (exclusive file lock)
  - Pre/post-write SHA256 checksum
  - Audit log (_audit_log)
  - Proposal count sync (_sync_count)
                        |
                        V
  /home/hermes/proposals/projects.csv
  /home/hermes/proposals/proposals.csv
                          A
                          | Unix Domain Socket
                          | (/tmp/ai-superpower.sock or /var/run/ai-superpower/api.sock)
                          |
  ai-superpower CLI (client.py)
  - ai-superpower project add/list/update/...
  - ai-superpower proposal add/list/update/...
  - ai-superpower sync-to-index
```

## Tamper Resistance Layers

### Layer 1: Exclusive Write Path (File Lock)

The CSV files are **not directly writable** by normal processes. The API server holds an exclusive flock when running:

```python
# storage.py — server acquires lock on startup
self._lock = open(self._csv_path, 'r')
fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
```

Any process that tries to `open(..., 'w')` directly will block or fail if the server holds the lock.

### Layer 2: SHA256 Checksum (Detection, Not Prevention)

```python
# Before mutation
prev_sha = self._sha256(self._csv_path)

# After mutation
new_sha = self._sha256(tmp_path)
self._audit('CSV_UPDATE', str(self._csv_path),
    {'sha_before': prev_sha[:8], 'sha_after': new_sha[:8], 'rows': len(rows)})
```

If a direct write bypasses the API, the next API write will detect SHA mismatch and log it. This is **detection**, not prevention.

### Layer 3: API-Only Mutations

No direct CSV mutation path exists through the API. Every write goes through:

1. Pydantic model validation (field types, enums, ID format)
2. State machine transition validation (STATUS_TRANSITIONS)
3. Atomic write (.tmp -> .bak -> rename)
4. Audit log entry

## API Endpoints

```
POST/GET      /api/projects
GET/PUT/DELETE /api/projects/{id}

POST/GET      /api/proposals
GET           /api/proposals/{id}
PUT           /api/proposals/{id}/status   (state machine enforced)
PUT           /api/proposals/{id}/fields   (partial-field updates, enum validated)
DELETE        /api/proposals/{id}

POST          /validate
GET           /api/audit
GET           /health
```

**No full PUT** — only `PUT .../status` (enforces state machine) and `PUT .../fields` (partial updates). Full row overwrites are not supported.

### State Machine (v4.0.0)

The state machine is defined in `models.py` as `STATUS_TRANSITIONS`. Any transition not in this map raises `400 Bad Request`.

The `/fields` endpoint validates enum fields (`prd_confirmation`, `tech_expectations`, `acceptance`, `game_type`) against `VALID_ENUMS`.

## Installation & Startup

```bash
# Install
cd /home/hermes/ai-superpower
pip install -e .

# Configure API Key (edit config.toml)
vim ~/.ai-superpower/config.toml

# Start API server
ai-superpower run

# Or via systemd (production)
sudo cp deploy/ai-superpower.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-superpower
sudo systemctl start ai-superpower
```

## Key Files

| File | Role |
|------|------|
| `src/ai_superpower/server.py` | FastAPI + Unix socket, all endpoints |
| `src/ai_superpower/storage.py` | flock + SHA256 audit + atomic write |
| `src/ai_superpower/models.py` | Pydantic models + state machine |
| `src/ai_superpower/client.py` | Unix socket HTTP client |
| `src/ai_superpower/cli.py` | CLI entry point |
| `deploy/ai-superpower.service` | systemd unit file |
| `~/.ai-superpower/config.toml` | API Key, socket path, CSV paths |

## Operational State

- **Socket** (test): `/tmp/ai-superpower.sock`
- **Socket** (prod): `/var/run/ai-superpower/api.sock`
- **Lock**: `fcntl.LOCK_EX` exclusive, blocks all other writers
- **Audit log**: `/home/hermes/proposals/audit.log`
- **Git commit** (2026-05-23): `d3338c8`

## Limitations

1. **SHA256 is detection only** — if attacker has root access they can disable the server, write, and restart
2. **Flock is per-machine** — in a multi-machine deployment the lock does not span machines
3. **API Key in config.toml** — if the file is compromised, authentication is bypassed
4. **CLI still uses CSV paths directly** — `client.py` speaks to the API; if the CLI bypasses the API client, protection fails

## allow_delete 陷阱（2026-05-23）

**症状**：配置 `~/.ai-superpower/config.toml` 中 `allow_delete` 已改为 `true`（或 `false`），但删除仍返回 204（或仍返回 403）。

**根因**：FastAPI server 在启动时一次性读取 config，后续修改不自动Reload。Server 进程持有旧值。

**调试方法**：
1. 在 `server.py` delete handler 加 debug 打印：
   ```python
   print(f"[DEBUG] allow_delete={s.config.allow_delete}", flush=True)
   ```
2. 重启 server
3. 发起 DELETE 请求，看 server 终端输出的实际值
4. 对比 `~/.ai-superpower/config.toml` 中的值

**正确步骤**：
```bash
# 1. 编辑配置
vim ~/.ai-superpower/config.toml
# allow_delete = true

# 2. 重启 server（必须）
pkill -f "ai-superpower run"; sleep 1; ai-superpower run

# 3. 验证
curl -X DELETE http://localhost:8000/api/proposals/TEST-ID \
  -H "X-API-Key: $KEY"
# 期望: 204（allow_delete=true）或 403（allow_delete=false）
```

**注意**：`pyproject.toml` 是包元数据文件，**不是**配置文件。正确路径永远是 `~/.ai-superpower/config.toml`。

## When to Use ai-superpower vs Old CLI

| Scenario | Use |
|----------|-----|
| New proposal management tool | **ai-superpower** (mandatory) |
| Operating existing ai-superpower | ai-superpower CLI |
| Emergency recovery from corruption | Old CLI (read-only) + backup restore |
| One-time CSV operations | Old CLI (but must go through API afterward) |

## Migration from Old System

The old `proposal_manager_cli.py` is deprecated for write operations. All mutation must go through ai-superpower:

```bash
# Old (DEPRECATED — no tamper protection)
python3 scripts/proposal_manager_cli.py proposal add ...

# New (REQUIRED — tamper-resistant)
ai-superpower proposal add ...
```

The `sync-to-index` command still runs via CLI (reads from CSV via API, writes markdown):
```bash
ai-superpower sync-to-index
```
