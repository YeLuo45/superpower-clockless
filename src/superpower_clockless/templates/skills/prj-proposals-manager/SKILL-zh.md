---

---

name: prj-proposals-manager
description: 管理从需求 intake 到交付的完整提案生命周期，协调多个 Agent 或角色（Coordinator / PM / Dev / Test Expert / Research Analyst）。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。支持任意 Agent 平台（Cursor、Hermes、OpenClaw 等）
version: 5.0.0
author: YeLuo45
license: MIT
metadata:
  hermes:
    tags: [proposal, workflow, lifecycle, project-management, mcp, ai-superpower]
    homepage: [https://yeluo45.github.io/prj-proposals-manager/](https://yeluo45.github.io/prj-proposals-manager/)
related_skills: [ai-superpower, ai-superpower-iteration-workflow, mcp-server-integration-workflow, harness-desktop-iteration-workflow, dbg-card-game-workflow, pixel-pal-web-workflow]

---

# 提案管理

一个与平台无关的技能，用于在多角色工作流（Coordinator / PM / Dev / Test Expert / Research Analyst）中管理提案生命周期。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。

## 核心规则（v5.0.0 — 2026-06-08）

**项目/提案数据操作应通过 ai-superpower MCP 工具（见下表）。这是 SPA（`useMcp.js`）和 agent（`aisp mcp --transport=stdio`）的推荐路径。**

**MCP 工具**（通过 ai-superpower `mcp_server.py` 在 `/mcp` Streamable HTTP 端点暴露，详见 [ai-superpower skill](./../../productivity/ai-superpower/SKILL.md)）：


| 工具                                                                    | 用途                                                 |
| --------------------------------------------------------------------- | -------------------------------------------------- |
| `set_api_key`                                                         | stdio 模式设置 API key（写 `AI_SUPERPOWER_API_KEY` 环境变量） |
| `list_projects` / `get_project` / `create_project` / `update_project` | 项目 CRUD                                            |
| `check_project_duplicate`                                             | 创建前重复检查（name + git_repo）                           |
| `list_proposals` / `get_proposal` / `create_proposal`                 | 提案列表/详情/创建                                         |
| `update_proposal_status`                                              | 状态机强制转移（一次走一步）                                     |
| `update_proposal_fields`                                              | 局部字段更新（status 走另一接口）                               |
| `merge_proposals_by_project`                                          | 按源项目名批量迁移提案                                        |
| `get_audit`                                                           | 审计日志查询（page + filter）                              |
| `get_stats`                                                           | 聚合统计                                               |
| `get_sync_config` / `update_sync_config`                              | 同步配置读写                                             |
| `export_sync`                                                         | 触发 GitHub Pages 同步导出                               |
| `get_sync_status`                                                     | 同步状态查询                                             |


> **创建时的 stage**：只有 `stage: "approved_for_dev"` 接受，其他返 HTTP 422。**owner 必填**（min_length=1）。
>
> **字段更新**：用 `update_proposal_fields` —— **不要**用 `update_proposal_status`。
>
> **状态转移**：用 `update_proposal_status` —— 严格按 `intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev → in_test_acceptance → accepted → deployed → delivered` 一次走一步。
>
> **API key 配置**：SPA 在 localStorage 存 `mcp_server_url` + `mcp_api_key`；agent 用 `~/.ai-superpower/config.toml` 的 `[api].key`（env: `AI_SUPERPOWER_API_KEY`）。

---

## 提案生命周期状态机（v5 — 严格线性）

```
intake → clarifying → prd_pending_confirmation → approved_for_dev
                                                       ↓
              in_test_acceptance ←────────────────────── in_dev
                   ↓      ↓
             accepted   test_failed
                 ↓
             deployed → delivered
```

## 阶段定义


| 阶段                         | 负责人         | 说明                  |
| -------------------------- | ----------- | ------------------- |
| `intake`                   | Coordinator | Boss 提出需求后创建提案      |
| `clarifying`               | Coordinator | 提问澄清需求，最多 3 轮       |
| `prd_pending_confirmation` | PM          | PRD 草稿完成，等待 boss 确认 |
| `approved_for_dev`         | Coordinator | Boss 确认后分配 dev      |
| `in_dev`                   | Dev         | 开发实施                |
| `in_test_acceptance`       | Coordinator | 测试验收评审              |
| `test_failed`              | Coordinator | 测试未通过               |
| `accepted`                 | Coordinator | 验收通过                |
| `deployed`                 | Coordinator | 部署到生产环境             |
| `delivered`                | Coordinator | 交付给 boss            |


---

## 操作模式

### 默认模式（交互式）

需要用户确认时，提供 A/B/C/D 选项并等待单字母回复：

- 选项以括号形式呈现：`[A] 选项 A  [B] 选项 B  [C] 选项 C  [D] 继续`
- 用户以单个字母回复（不区分大小写）
- 超时后触发第一个选项作为默认

### 无人值守模式（全自动）

适用于无用户在场时的持续迭代。当请求者/boss 在提交提案时指定"无人值守"或"自动"时启用。

**如何进入：**

- Boss/请求者声明意图："我要无人值守模式跑这个项目"或"run in unattended mode"
- 在提案的 `notes` 字段中记录为 `mode: unattended`
- 一旦进入，所有后续迭代自动保持无人值守模式

**特性：**

- 始终自动选择第一个选项（默认）
- 不等待用户输入
- 交付时必定包含迭代方向选项（A/B/C/D），确保迭代持续
- 永远不会在确认门控上卡住
- 无人值守模式跨迭代保持——一旦设置，持续有效直到 boss 明确退出

**传递规则：**

- 当在无人值守模式项目下创建新迭代提案时，继承无人值守模式
- 交付后不清除无人值守模式——持续迭代直到 boss 明确退出

**触发时机：**

- 交付时：始终提供 A/B/C/D 迭代选项，自动选择第一个
- PRD/技术预期确认：5分钟超时后自动批准并继续
- 无人值守模式下不提问澄清问题

---

## 工作流：提案生命周期

```
Step 1a/1b: Intake -- 注册提案（从现有代码库或新建）
Step 2: Clarify -- 最多3轮澄清
Step 3: 如需要则转给 PM
Step 4: PRD 确认门控
Step 5: 技术预期门控（最多3轮）
Step 6: 输出技术方案
Step 6b: 交接给 Test Expert -- 生成 TDD 测试用例
Step 7: 交接给 Dev（以测试用例为参考）
Step 8: Test Expert 基于测试用例进行验收
Step 9: 交付或返修
Step 10: 研究方向（验收后迭代规划）
Step 11: 部署（验收后交付）
```

### Step 1a: 从现有代码库注册

当需求是克隆现有 GitHub 仓库并注册为提案时（而非从零开始构建）：

1. 将仓库克隆到 `$superpower-dev/<project-name>/proposals/` 或本地复制
2. 对于设计文档项目（`*-design`），按照 Step 1b 作为常规提案处理

### Step 1b: 从零开始注册新提案

⚠️ **重复项目名**是常见陷阱。创建前先评估名称冲突风险（旧 case-insensitive 守卫在第一次创建时可能返 409）。
如果项目名比较常见，务必使用下面的扫描流程。

**先用 ai-superpower 检查重名（精准匹配，区分大小写）：**
```bash
# 1. 按名称搜索
mcp_aisp.py list-projects --search "ProjectName" --page-size 5

# 2. 如果找到精准匹配：复用现有 PRJ-ID
#    v5.0.0+ 的精准匹配规则会自动返回现有项目，所以你也可以直接
#    调用 create-project 并读取响应中的 "_existing" 字段。

# 3. 如果没精准匹配但怀疑有旧数据重复：
mcp_aisp.py scan-duplicate-projects           # 默认 case-insensitive
mcp_aisp.py scan-duplicate-projects --case-insensitive false   # 仅完全匹配
```

**3 种场景处理：**

| `scan-duplicate-projects` 结果 | 行动 |
|---|---|
| 没有重复 | 安全创建新项目 |
| 找到重复（case-insensitive） | 提交给 boss：列出每个重复的 PRJ-ID，问哪个是规范的 |
| 找到重复（完全匹配） | 复用现有 ID —— `create-project` 会自动返回 `_existing: true` |

**如果 boss 说"把 X 合并到 Y"：**
```bash
# 步骤 A：建议先备份（审计日志已存，但可另外导出）
mcp_aisp.py get-audit --entity project --since 2026-06-01   # 查看最近活动

# 步骤 B：合并
mcp_aisp.py merge-projects --target-id PRJ-... --source-id PRJ-... --delete-source true

# 步骤 C：验证
mcp_aisp.py get-project --project-id <source-id>    # 应返回 "Project not found"
mcp_aisp.py scan-duplicate-projects                # 重复组数应 -1
```

**通过 `mcp_aisp.py`（MCP CLI）创建项目：**
```bash
# 第一次尝试（无精准匹配）：
mcp_aisp.py create-project --name "ProjectName" --git-repo "https://github.com/owner/repo"

# 强制创建（绕过 case-insensitive 重复守卫；很少用）：
mcp_aisp.py create-project --name "ProjectName" --git-repo "..." --force

# 精准匹配命中的响应（自动返回现有，无错误）：
# {"_existing": true, "id": "PRJ-YYYYMMDD-XXX", "_note": "Returned existing..."}
```
2. 通过 ai-superpower CLI 为项目生成下一个提案 ID（自动分配，无需手动管理）
3. 为此提案创建 gh-pages 分支（如果项目有远程仓库）：
  ```bash
  cd $superpower-proposals/<project-name>
  git checkout -b gh-pages
  ```
4. 将 `$TEMPLATES_DIR/request-intake-template.md` 复制到提案目录
5. 填写基本信息和原始需求
6. 通过 ai-superpower API 创建提案：
  ```bash
   mcp_aisp.py create-proposal --title "ProposalTitle" --owner "coordinator" --project-id "PRJ-YYYYMMDD-XXX" --stage approved_for_dev
  ```

### Step 2: 澄清需求

- 最多向请求者进行3轮澄清提问，聚焦于：目标、范围、约束、验收标准
- 在提案文件的"Clarification"部分记录每轮问答
- 3轮之后或需求清晰时，记录最终假设
- 将状态流转到 `clarifying`：
  ```bash
  mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status clarifying
  ```

### Step 3: 转给 PM

如果需求只是一个想法或粗略草案，转给 PM 角色来生成 PRD。

- PM 将 PRD 保存到 `$superpower-proposals/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md`
- PM 还将 PRD 复制到 `$superpower-proposals/<project-name>/docs/prd.v1.md`
- 通过 ai-superpower API 更新 PRD 路径：
  ```bash
  mcp_aisp.py update-proposal-fields --proposal-id P-YYYYMMDD-XXX --prd-path "$superpower-proposals/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md"
  ```

### Step 4: PRD 确认门控

PM 返回 PRD 后：

1. 向请求者展示 PRD 并请求确认
2. 开始确认倒计时（建议：5分钟）
3. 在"PRD Confirmation Countdown ID"中记录倒计时引用

如果确认：将 PRD Confirmation 设为 `confirmed`，取消倒计时，立即将状态流转为 `approved_for_dev` 并开始开发。

```bash
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status approved_for_dev
```

如果超时：将 PRD Confirmation 设为 `timeout-approved`，在"Timeout Resolution"中记录，立即将状态流转为 `approved_for_dev` 并开始开发。

```bash
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status approved_for_dev
```

### Step 5: 技术预期门控

在输出技术方案之前：

1. 从请求者处了解：技术栈、性能、成本、部署方式、可维护性、依赖约束
2. 最多3轮提问
3. 开始确认倒计时（与 Step 4 相同机制）
4. 在"Technical Expectations Countdown ID"中记录

如果确认：将 Technical Expectations 设为 `confirmed`，立即撰写技术方案并将状态流转为 `approved_for_dev`。

如果超时：将 Technical Expectations 设为 `timeout-approved`，按当前假设继续，立即撰写技术方案并将状态流转为 `approved_for_dev`。

### Step 6: 技术方案

- 将技术方案输出到 `$superpower-root/P-YYYYMMDD-XXX-tech-solution.md`
- 同时复制到 `$superpower-proposals/<project-name>/docs/technical-solution.v1.md`
- 通过 ai-superpower API 更新技术方案路径：
  ```bash
  mcp_aisp.py update-proposal-fields --proposal-id P-YYYYMMDD-XXX --tech-solution-path "$superpower-root/P-YYYYMMDD-XXX-tech-solution.md"
  ```

### Step 6b: TDD 测试用例生成

技术方案输出后，转交给 Test Expert 基于 TDD 原则生成测试用例：

1. Coordinator 将任务交接给 Test Expert，包含：PRD 文档、技术方案文档、项目背景
2. Test Expert 将测试用例输出到 `$superpower-test/<project-name>/YYYY-MM-DD-test-cases.md`
  - 测试用例必须可追溯到 PRD 需求
  - 包含：测试用例 ID、描述、前置条件、步骤、预期结果
  - 覆盖正常路径和边界情况
  - 将测试用例复制到 `$superpower-dev/<project-name>/proposals/docs/test-cases.v1.md`
3. 通过 ai-superpower API 将状态流转为 `in_tdd_test`：
  ```bash
   # 注：v5 状态机没有 in_tdd_test 状态。测试用例交付后状态保持 approved_for_dev
  ```

### Step 7: 交接给开发

- 将状态流转为 `in_dev`：
  ```bash
  mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status in_dev
  ```
- 更新 project_path：
  ```bash
  mcp_aisp.py update-proposal-fields --proposal-id P-YYYYMMDD-XXX --project-path "$superpower-proposals/<project-name>"
  ```
- 如果目录不存在，Dev 创建 `$superpower-proposals/<project-name>/docs/`

### Step 8: Test Expert 验收（基于 TDD）

Dev 报告完成后，Test Expert 基于测试用例执行验收：

需求一致性：

- 符合请求者确认的需求
- 与 PRD 对齐
- 无范围蔓延或偷工减料

测试用例执行：

- 执行 `test-cases.vN.md` 中的每个测试用例
- 记录每个测试用例的通过/失败状态
- 记录任何偏差或失败

功能验证（必须实际操作，不能只看截图）：

- 核心功能端到端正常工作
- 控制台/日志无 Error（warning 可以忽略）
- 现有功能未被破坏
- 构建成功

验收期间将状态流转为 `in_test_acceptance`：

```bash
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status in_test_acceptance
```

如果所有测试用例通过：进入 Step 9（交付）

如果任何测试用例失败：将状态流转为 `test_failed`，输出结构化返修意见：

```bash
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status test_failed
```

### Step 9: 交付或返修

如果所有测试用例通过：将状态流转为 `accepted`，进入 Step 10（研究方向）：

```bash
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status accepted
```

如果验收失败：将状态流转为 `needs_revision`，输出结构化返修意见：

```bash
# 注：v5 状态机没有 needs_revision 状态。验收失败后状态保持 test_failed
```

### Step 10: 研究方向（验收后迭代规划）

验收通过后（状态变为 `accepted` 或 `delivered`）：

1. Coordinator 询问请求者："基于本次交付，你是想探索下一个迭代方向，还是先维护当前版本？"
2. 开始5分钟确认倒计时，创建 cron job
3. 在"Research Direction Countdown ID"中记录倒计时引用

如果确认：将 Research Direction 设为 `confirmed`，立即将任务转给 PM 生成下一个迭代 PRD。

如果超时：将 Research Direction 设为 `timeout-approved`，Coordinator 自行决定，立即将任务转给 PM 生成下一个迭代 PRD。

### Step 11: 部署（验收后交付）

验收通过后（状态变为 `accepted`）：

1. 确定部署目标：GitHub Pages 或 Cloudflare Pages
2. 创建部署分支
3. 准备部署（确保 package-lock.json 已提交，运行 `npm run build`）
4. 推送到远程
5. 触发部署
6. 更新提案：将状态设为 `deployed`，记录 Deployment URL：
  ```bash
   mcp_aisp.py update-proposal-fields --proposal-id P-YYYYMMDD-XXX --deployment-url "https://..."
mcp_aisp.py update-proposal-status --proposal-id P-YYYYMMDD-XXX --status deployed
  ```

---

## API 操作速查

所有操作使用 HTTP REST API，Base URL = `http://0.0.0.0:8000`，Header: `X-API-Key: {key}`

> **完整接口文档**：见 `../../ai-superpower/docs/api/`：
>
> - `projects.md` — 项目 CRUD 接口
> - `proposals.md` — 提案 CRUD + 状态机流转
> - `utilities.md` — 审计、验证、健康检查、CLI 参考

### 项目操作（Python MCP stdio）

```python
# stdio 客户端通过 mcp Python SDK 连接
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def list_projects():
    params = StdioServerParameters(command="aisp", args=["mcp", "--transport=stdio"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_projects", {"search": "keyword"})
            print(result.content[0].text)

asyncio.run(list_projects())
```

### 提案操作（Python MCP stdio）

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def create_proposal():
    params = StdioServerParameters(command="aisp", args=["mcp", "--transport=stdio"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 状态机：必须从 approved_for_dev 开始
            result = await session.call_tool("create_proposal", {
                "title": "提案标题",
                "owner": "owner",
                "project_id": "PRJ-20260523-001",
                "stage": "approved_for_dev"
            })
            print(result.content[0].text)
            # 状态机流转（一次走一步）
            await session.call_tool("update_proposal_status", {
                "proposal_id": "P-20260523-001", "status": "in_dev"
            })

asyncio.run(create_proposal())
```

### 审计日志

```python
# ai-superpower/docs/api/utilities_api.py
from utilities_api import UtilitiesAPI
api = UtilitiesAPI(api_key=os.environ["SUPERPOWER_API_KEY"])

api.audit(page=1, page_size=100, entity="proposal", op="status_change")
api.validate({"title": "test", "owner": "me", "project_id": "PRJ-20260523-001", "stage": "ideation"})
api.health()
```

---

## 开发交付质量检查

验收前必须验证三项硬指标：

1. 构建 exit code：必须为 0
2. 输出目录非空：列出核心文件确认
3. 核心源文件/服务文件存在：验证关键文件存在

### 接管触发条件

满足任一条件时 Coordinator 应直接接管：

- Dev 连续2次交付不合格
- Dev session 因 API/配额错误中断
- Dev session 异常短（<30秒）却声称完成
- 修复方法简单明确

### 修复记录

当 Coordinator 直接修复问题时，记录到：

1. 项目 memory 文件（例如 `MEMORY.md`）的相关章节
2. 每日日志（例如 `memory/YYYY-MM-DD.md`）
3. 提案的 Notes 或 Main Fixes Applied 字段

---

## 备份和回滚

### 备份

```bash
# 创建备份（保留最近10个备份）
bash scripts/backup_proposals.sh

# 备份存储在：/home/hermes/proposals/backups/
```

### 回滚

```bash
# 列出可用备份
bash scripts/rollback_proposals.sh list

# 验证备份完整性
bash scripts/rollback_proposals.sh verify proposals_backup_YYYYMMDD_HHMMSS.tar.gz

# 全系统回滚（到最新备份）
bash scripts/rollback_proposals.sh full

# 全系统回滚到指定备份（N=1 为最新，N=2 为第二新）
bash scripts/rollback_proposals.sh full 3

# 回滚指定项目
bash scripts/rollback_proposals.sh project PRJ-YYYYMMDD-XXX

# 回滚指定提案
bash scripts/rollback_proposals.sh proposal P-YYYYMMDD-XXX
```

### 回滚行为


| Command           | Data Restored               |
| ----------------- | --------------------------- |
| `full N`          | 备份 N 中的所有 CSV + markdown 文件 |
| `project <id> N`  | projects.csv 条目 + 相关提案 + 映射 |
| `proposal <id> N` | proposals.csv 中的单个提案 + 映射   |


**安全措施：**

- 全系统回滚前：创建当前状态的紧急备份
- 提案/项目回滚前：创建紧急备份
- 所有操作需要 `yes` 确认

---

## 环境变量


| 变量                      | 说明                                                         |
| ----------------------- | ---------------------------------------------------------- |
| `AI_SUPERPOWER_API_KEY` | API 密钥（从 `~/.ai-superpower/config.toml` 的 `[api].key` 复制）  |
| `AISP_MCP_TRANSPORT`    | stdio 默认 / `http`（SPA 端通常用 http，agent 端用 stdio）            |
| `AISP_MCP_URL`          | Streamable HTTP 端点（默认 `http://127.0.0.1:8000/mcp/`，注意带尾斜杠） |


---

## 配置


| Variable             | Value                                                      | Description    |
| -------------------- | ---------------------------------------------------------- | -------------- |
| superpower-root      | `/home/hermes/proposals`                                   | 所有 agent 的文件目录 |
| superpower-dev       | `{superpower-root}/workspace-dev/<project>/proposals`      | Dev 工作空间       |
| superpower-pm        | `{superpower-root}/workspace-pm/<project>/proposals`       | PM 工作空间        |
| superpower-test      | `{superpower-root}/workspace-test/<project>/proposals`     | Test 工作空间      |
| superpower-research  | `{superpower-root}/workspace-research/<project>/proposals` | Research 工作空间  |
| superpower-proposals | `{superpower-root}/workspace-proposals/<project>`          | 提案（主索引）工作空间    |
| superpower-backups   | `{superpower-root}/backups`                                | 备份存储目录         |


---

## 工作空间初始化

使用 `--init-workspace` 创建项目时，脚本会创建：

```
workspace-dev/<project>/proposals/
workspace-dev/<project>/proposals/docs/index.md

workspace-pm/<project>/proposals/
workspace-pm/<project>/proposals/docs/index.md

workspace-test/<project>/proposals/
workspace-test/<project>/proposals/docs/index.md

workspace-research/<project>/proposals/
workspace-research/<project>/proposals/docs/index.md
```

每个 `docs/index.md` 包含 Proposal、PRD、Technical Solution 和 Test Cases 的版本追踪表。

### 验收后：将 PRD/技术方案同步到 Dev 工作空间

提案验收后，需将 PRD 和技术方案文件同步到 `workspace-dev/proposals/` 下对应的项目目录，确保项目同步到远程仓库时包含这些文档：

```bash
python3 scripts/sync-pm-to-dev.py <project_id> [--dry-run]

# 示例
python3 scripts/sync-pm-to-dev.py PRJ-20260422-001          # 同步 ai-novel-assistant
python3 scripts/sync-pm-to-dev.py PRJ-20260516-001 --dry-run  # 仅预览
```

文件从：`workspace-pm/proposals/{project_id}/` → `workspace-dev/proposals/{project_name}/`

测试用例文件（文件名包含 `test`、`spec`、`test-case` 的 .md 文件）也会被同步。

### 验收后：生成 OpenSpec SPEC

提案验收后，基于 PRD 和技术方案生成 OpenSpec 规范文件：

```bash
python3 scripts/generate-spec.py <project_id> [--dry-run]

# 示例
python3 scripts/generate-spec.py PRJ-20260422-001          # 为 ai-novel-assistant 生成 SPEC
python3 scripts/generate-spec.py PRJ-20260516-001 --dry-run  # 仅预览
```

读取 `workspace-pm/proposals/{project_id}/` 下的 PRD 和技术方案，生成：

```
workspace-dev/proposals/{project_name}/SPEC/
├── proposal.md        # Why/What/Capabilities/Impact（来自 PRD）
├── spec.md           # 需求 + GHERKIN 场景
├── design.md         # Context/Goals/Decisions/Risks（来自技术方案）
├── tasks.md          # 实施检查清单
└── .openspec.yaml    # 元数据（schema、project、创建日期）
```

OpenSpec 参考：[https://github.com/YeLuo45/OpenSpec（schemas/spec-driven/templates/）](https://github.com/YeLuo45/OpenSpec（schemas/spec-driven/templates/）)

### 为已有项目初始化 SPEC

为没有提案的项目（遗留项目）从现有项目文件初始化 OpenSpec SPEC：

```bash
# 为单个项目初始化 SPEC（按项目名）
python3 scripts/generate-spec.py --init <project_name>
python3 scripts/generate-spec.py --init todolist                      # 按项目名
python3 scripts/generate-spec.py --init ai-stock-simulation --name "AlphaTrader"  # 带显示名

# 为所有没有 SPEC 的项目初始化
python3 scripts/generate-spec.py --init --all
python3 scripts/generate-spec.py --init --all --dry-run               # 仅预览
```

读取来源：

- `workspace-dev/proposals/{project_name}/README.md`（项目描述、功能、技术栈）
- `workspace-dev/proposals/{project_name}/SPEC.md`（如果存在）
- 无来源时使用模板内容

---

## Bug 预防


| 问题       | 预防                          |
| -------- | --------------------------- |
| 重复 ID    | API 自动生成唯一 ID，无需手动管理        |
| CSV 字段错位 | API 强制 20 字段规范，杜绝错位         |
| 直接篡改 CSV | API 通过 audit log 全程记录，可审计   |
| 并发写入     | FastAPI + file lock 保证数据一致性 |
| ID 范围冲突  | API 按项目分配序号，隔离冲突            |
| 数据丢失     | Audit log 支持 replay 恢复      |


---

## References


| 文件                                              | 用途               |
| ----------------------------------------------- | ---------------- |
| `ai-superpower-architecture.md`                 | 防篡改架构设计          |
| `ai-superpower-cli-quirks.md`                   | CLI 参数规范         |
| `bash-pitfalls.md`                              | Shell 脚本常见错误     |
| `data-recovery.md`                              | 数据恢复方法           |
| `favorites-system.md`                           | 收藏功能架构           |
| `github-repo-rename.md`                         | GitHub 仓库重命名处理   |
| `local-path-population.md`                      | 本地路径填充逻辑         |
| `merge-proposals-dirs.md`                       | 合并提案目录           |
| `openspec-integration.md`                       | OpenSpec 集成      |
| `vite-cache-issue.md`                           | Vite 缓存问题处理      |
| `../../ai-superpower/docs/api/projects.md`      | 项目 API 接口文档      |
| `../../ai-superpower/docs/api/proposals.md`     | 提案 API 接口文档      |
| `../../ai-superpower/docs/api/utilities.md`     | 工具 API 接口        |
| `../../ai-superpower/docs/api/projects_api.py`  | 项目 API Python 封装 |
| `../../ai-superpower/docs/api/proposals_api.py` | 提案 API Python 封装 |
| `../../ai-superpower/docs/api/utilities_api.py` | 工具 API Python 封装 |


## Scripts


| 文件                      | 用途                    |
| ----------------------- | --------------------- |
| `backup_proposals.sh`   | 备份提案系统                |
| `rollback_proposals.sh` | 回滚提案系统（支持全系统/项目/提案级别） |


## 相关技能

- `ai-superpower-iteration-workflow` — ai-superpower 自身迭代流程
- `harness-desktop-iteration-workflow` — Desktop 项目迭代
- `dbg-card-game-workflow` — DBG 卡牌游戏开发
- `pixel-pal-web-workflow` — PixelPal Web 开发

