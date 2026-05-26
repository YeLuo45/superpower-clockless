# ai-superpower CLI 参数规范

## 核心规则
**使用 `ai-superpower` CLI，所有数据操作必须通过 API，禁止直接读写 CSV。**

配置文件：`~/.ai-superpower/config.toml`（**不是 pyproject.toml**）

---

## project create

```bash
# ❌ ERROR: git_repo format rejected
ai-superpower project create \
  --name "pixel-pal-web" \
  --git-repo "YeLuo45/pixel-pal-web"
# ERROR: git_repo 格式错误，需以 https:// 或 git@ 开头

# ✅ 正确：必须 https:// 开头
ai-superpower project create \
  --name "pixel-pal-web" \
  --git-repo "https://github.com/YeLuo45/pixel-pal-web"

# 自动生成项目ID: PRJ-YYYYMMDD-NNN
```

**Note**: `--name` 必填，`--git-repo` 必填且必须是完整 URL 格式。

---

## project list

```bash
# 列出所有项目
ai-superpower project list

# 按名称搜索
ai-superpower project list --search "keyword"

# 带排序参数
ai-superpower project list --sort-by last_update --sort-order desc
```

---

## project update

```bash
# ✅ 正确：project ID 是位置参数
ai-superpower project update PRJ-20260519-001 \
  --name "新名称" \
  --prj-url "https://new-url.pages.dev"

# ❌ ERROR: --id is NOT supported
ai-superpower project update --id PRJ-20260519-001 ...
```

---

## proposal create

```bash
# ✅ 正确：自动分配 ID
ai-superpower proposal create \
  --title "pixel-pal-web 完全移除MUI依赖" \
  --project-id PRJ-20260519-001 \
  --owner "coordinator" \
  --stage "ideation"

# ❌ ERROR: --id is NOT supported (ID is auto-generated)
ai-superpower proposal create \
  --id P-20260519-003 \
  --title "..."
```

---

## proposal update

```bash
# ✅ 正确：proposal ID 是位置参数
ai-superpower proposal update P-20260519-003 \
  --status "clarifying" \
  --notes "Phase 1 完成"

# ❌ ERROR: --id is NOT supported
ai-superpower proposal update --id P-20260519-003 ...
```

---

## proposal list

```bash
# 查看所有提案
ai-superpower proposal list

# 按项目/状态/阶段过滤
ai-superpower proposal list --project-id PRJ-20260523-001
ai-superpower proposal list --status in_dev
ai-superpower proposal list --stage "beta"

# 带搜索和排序
ai-superpower proposal list --search "关键词" --sort-by last_update --sort-order desc
```

---

## proposal advance（状态流转）

```bash
# 推进提案到下一个状态
ai-superpower proposal advance P-20260522-002

# 状态转换链（v4.0.0）
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

---

## allow_delete 配置

```bash
# config.toml 中设置
[api]
allow_delete = true   # 默认 false，需显式开启

# 修改后必须重启 server
pkill -f "ai-superpower run"; sleep 1; ai-superpower run
```

---

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `git_repo 格式错误` | URL 未以 `https://` 开头 | 使用完整 URL |
| `--id is NOT supported` | 新 CLI 不支持手动指定 ID | 自动生成 |
| `Delete operation is disabled` | `allow_delete=false` | 修改 config.toml 并重启 |
| `python: command not found` | WSL 环境没有 python 别名 | 使用 `python3` |

---

## 直接操作 CSV（禁止）

```bash
# ❌ 禁止：直接读写 CSV
tail -1 ~/.hermes/proposals/proposals.csv | cut -d',' -f1,6
wc -l ~/.hermes/proposals/proposals.csv

# ✅ 正确：使用 API
curl "$BASE/api/proposals?page=1&page_size=1" -H "X-API-Key: $KEY"
```

**所有数据操作必须通过 ai-superpower API，直接操作 CSV 会破坏数据完整性。**