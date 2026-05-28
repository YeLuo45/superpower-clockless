---
name: prj-proposals-manager
description: 管理从需求 intake 到交付的完整提案生命周期，协调多个 Agent 或角色（Coordinator / PM / Dev / Test Expert / Research Analyst）。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。支持任意 Agent 平台（Cursor、Hermes、OpenClaw 等）
version: 4.5.0
author: YeLuo45
license: MIT
metadata:
  hermes:
    tags: [proposal, workflow, lifecycle, project-management, api]
    homepage: https://yeluo45.github.io/prj-proposals-manager/
    related_skills: [ai-superpower-iteration-workflow, harness-desktop-iteration-workflow, dbg-card-game-workflow, pixel-pal-web-workflow]
---

# 提案管理

一个与平台无关的技能，用于在多角色工作流（Coordinator / PM / Dev / Test Expert / Research Analyst）中管理提案生命周期。涵盖 intake、澄清、PRD 确认、技术评审、测试用例生成、开发交接、验收和交付。

## ⚠️ 核心规则

**所有项目/提案数据操作必须通过 superpower-clockless MCP 桥接工具（见下），禁止直接读写 CSV。**

**MCP 工具**（由 `superpower-clockless mcp` 暴露）：

| 工具 | 用途 |
|------|---------|
| `health` | 检查 ai-superpower 服务健康状态 |
| `project_list` | 列出项目（search, page_size） |
| `project_get` | 获取指定项目 |
| `proposal_list` | 列出提案（project_id, search, page_size） |
| `proposal_get` | 获取指定提案 |
| `proposal_create` | 创建提案（title, owner, project_id, stage） |
| `proposal_update_fields` | 更新提案字段（proposal_id, fields） |
| `proposal_update_status` | 状态机流转（proposal_id, status） |

> **⚠️ 禁止直接 API 调用**：不要使用 `curl`、`requests` 或 `urllib` 调用 ai-superpower，始终使用上表中的 MCP 工具。
> **MCP 工具语法**：工具接受 JSON 对象作为参数，例如 `{"name": "proposal_create", "arguments": {"title": "...", "owner": "...", "project_id": "...", "stage": "approved_for_dev"}}`
> **创建时的 stage 值**：创建时仅接受 `stage: "approved_for_dev"`，`intake`、`clarifying`、`prd_pending_confirmation` 等值会返回 `422 Unprocessable Entity`。
> **字段更新**：使用 `proposal_update_fields` 更新字段（tech_expectations、notes 等），不要使用 PUT/PATCH。
> **状态流转**：使用 `proposal_update_status` 进行状态机流转——遵循 `intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev`。

---

## 提案生命周期状态机

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

## 阶段定义

| 阶段 | 负责人 | 说明 |
|-------|-------|-------------|
| `intake` | Coordinator | Boss 提出需求后创建提案 |
| `clarifying` | Coordinator | 提问澄清需求，最多3轮 |
| `prd_pending_confirmation` | PM | PRD 草稿完成，等待 boss 确认 |
| `approved_for_dev` | Coordinator | Boss 确认后分配 dev |
| `in_dev` | Dev | 开发实施 |
| `needs_revision` | Dev | 验收未通过——Dev 根据反馈返修 |
| `in_tdd_test` | Dev | TDD 测试阶段 |
| `in_test_acceptance` | Coordinator | 测试验收评审 |
| `test_failed` | Coordinator | 测试未通过 |
| `accepted` | Coordinator | 验收通过 |
| `deployed` | Coordinator | 部署到生产环境 |
| `delivered` | Coordinator | 交付给 boss |

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

## 生命周期钩子

每个生命周期节点可触发 pre/post 钩子，用于自动化、日志或副作用。钩子定义在提案的 `notes` 字段（JSON）或环境配置中。

### 钩子触发点

| 阶段 | Pre-Hook | Post-Hook | 可用变量 |
|-------|----------|-----------|-------------------|
| `intake` | `on_intake_pre` | `on_intake_post` | `proposal_id`, `title`, `owner` |
| `clarifying` | `on_clarifying_pre` | `on_clarifying_post` | `proposal_id`, `round` |
| `prd_pending_confirmation` | `on_prd_pre` | `on_prd_post` | `proposal_id`, `prd_path` |
| `approved_for_dev` | `on_approved_pre` | `on_approved_post` | `proposal_id`, `project_id` |
| `in_dev` | `on_dev_pre` | `on_dev_post` | `proposal_id`, `project_path` |
| `in_tdd_test` | `on_tdd_pre` | `on_tdd_post` | `proposal_id`, `test_cases_path` |
| `in_test_acceptance` | `on_acceptance_pre` | `on_acceptance_post` | `proposal_id`, `test_results` |
| `test_failed` | — | `on_test_failed_post` | `proposal_id`, `failure_reasons` |
| `accepted` | — | `on_accepted_post` | `proposal_id`, `deployment_url` |
| `deployed` | — | `on_deployed_post` | `proposal_id`, `deployment_url` |
| `delivered` | — | `on_delivered_post` | `proposal_id`, `delivered_at` |

### 在提案 Notes 中定义钩子

```json
{
  "hooks": {
    "on_intake_pre": "echo 'Intake started for P-YYYYMMDD-XXX' >> /tmp/lifecycle.log",
    "on_approved_post": "/usr/local/bin/notify-slack.sh",
    "on_deployed_post": "curl -X POST https://hooks.example.com/deploy $DEPLOYMENT_URL"
  }
}
```

### 钩子执行规则
- **执行方式**：Coordinator 同步（阻塞）执行 pre/post 钩子
- **失败处理**：pre-hook 失败 → 阻止状态转换并报告错误；post-hook 失败 → 仅记录错误，允许状态转换继续
- **无人值守模式**：post-hook 自动运行；pre-hook 若会阻塞则 30 秒超时后跳过
- **未定义钩子**：静默跳过（不报错）
- **变量**：以导出变量形式提供给钩子 shell 上下文（`$proposal_id`、`$project_id` 等）

---

## 架构重构触发机制

每 N 个已完成迭代提案（同项目，默认 6 次，可通过 `AI_SUPERPOWER_REFACTOR_ITERATIONS` 环境变量配置），项目进入**强制架构重构阶段**。Dev 以"架构师"角色接管，而非普通功能开发。

**配置：**
```bash
export AI_SUPERPOWER_REFACTOR_ITERATIONS=6  # 默认6，设为任意正整数；0禁用
```

**触发检测：**
- Coordinator 统计项目下所有 `stage: accepted` 或 `stage: deployed` 的提案数量
- 当数量 % `AI_SUPERPOWER_REFACTOR_ITERATIONS` == 0 时，Coordinator 设置 `needs_revision` 并附带架构重构授权
- Coordinator 在提案 notes 中记录：`"refactor_mandate": true`、`"refactor_count": <N>`

**架构师职责：**
1. 全量代码审计：识别耦合、技术债务、性能瓶颈、安全暴露面
2. 输出 `ARCHITECTURE.md`——模块分解、数据流、技术选型及理由
3. 输出 `REFACTOR.md`——优先排序的行动项及估算工作量
4. 所有重构提交在合并前必须通过现有测试套件
5. 重构阶段 scope 冻结——不引入新功能

**退出条件：** 架构师提交 `ARCHITECTURE.md` + `REFACTOR.md` 且所有现有测试通过后，Coordinator 将状态转回正常 `in_dev` 流程。

**项目仓库：** https://github.com/YeLuo45/superpowers

---

## 复杂需求任务拆解

当提案包含复杂的多组件需求时，Coordinator 将其拆分为离散的子任务，以 todo 列表方式跟踪，而非单一整体交付物。子任务可串行或并行（通过委托）推进。

### 触发条件

满足任一条件时触发任务拆解：
- PRD 包含 3+ 独立功能
- 任一单一功能需要 >3 个不同实现步骤
- 功能涉及不同技术栈或技能要求
- PRD 显式标记 `complex: true`

### 拆解流程

1. **识别子任务**：将 PRD 拆分为原子单元（如"认证模块"、"API 端点"、"UI 组件"、"单元测试"）
2. **创建子任务项**：在提案 notes 中以 JSON 任务列表形式记录：
   ```json
   {
     "tasks": [
       {"id": "T1", "content": "实现认证模块", "status": "pending"},
       {"id": "T2", "content": "构建 API 端点", "status": "pending", "depends_on": ["T1"]},
       {"id": "T3", "content": "UI 仪表盘", "status": "pending", "depends_on": ["T2"]},
       {"id": "T4", "content": "集成测试", "status": "pending", "depends_on": ["T2"]}
     ]
   }
   ```
3. **依赖解析**：`depends_on` 指定的前置任务未完成时，当前任务不能开始
4. **并行分配**：无依赖关系的任务（如 T1、T2 无先后顺序）可并发委托
5. **进度跟踪**：`pending` → `in_progress` → `completed`
6. **完成门控**：所有子任务 `completed` 后才可将提案转入 `accepted`

### 交接给 Dev

交接子任务时提供：`id`、`content` 和 `depends_on` 上下文。Dev 按子任务报告完成情况（而非仅报总体完成）。Test Expert 逐个验证子任务通过后标记 `completed`。

### 进度报告

Coordinator 可随时回答"这个提案的状态如何？"，格式示例：
```
Proposal P-YYYYMMDD-XXX: 2/4 tasks completed
  T1 ✅ 认证模块 — completed
  T2 ✅ API 端点 — completed
  T3 🔄 UI 仪表盘 — in progress
  T4 ⏳ 集成测试 — pending（waiting on T3）
```

---

## PM 角色：UI 设计专业能力

PM 在起草 PRD 时自动承担 UI 设计师职责。PM 设计能力在涉及视觉/UI 的项目（如 Web 应用、移动应用、互动游戏）时自动激活。

### 设计工具

| 工具 | 用途 |
|---|---|
| **open-design** | open-design.io 协作设计平台（主用） |
| **Figma** | Open Design 不可用时的备选 |
| **Excalidraw** | 架构图和快速原型 |
| **Canva** | 营销页/Landing page |

### 内置设计系统

| 设计系统 | 适用场景 | 关键规格 |
|---|---|---|
| **Apple macOS / iOS** | 桌面/移动原生感 | SF Pro 字体、8pt grid、动态字体、毛玻璃效果、41pt 触控目标 |
| **Material Design 3** | Android 应用 | M3 组件、4dp baseline、色相系统、动态配色 |
| **Fluent Design** | Windows 应用 | acrylic/云母背景、9pt grid、reveal highlight |
| **Human Interface Guidelines (HIG)** | Apple 平台全品类 | 隐私/完整性/美学三大原则、栏位结构、手势导航 |
| **Ant Design** | 企业中台 / React 技术栈 | 4px spacing、24-column grid、40+原子组件 |
| **Carbon Design** | B端数据密集型应用 | IBM Carbon、2x grid、暗黑主题优先 |

### PRD 设计审查清单

起草 UI 相关 PRD 时必须覆盖：
1. **Layout**：Grid 系统、响应式断点、安全区域
2. **Typography**：字体族、字号阶梯（type ramp）、行高
3. **Color**：品牌色板、语义色（success/error/warning）、对比度 ≥ 4.5:1
4. **Components**：核心 UI 元素、状态（default/hover/active/disabled）、变体
5. **Accessibility**：键盘导航、屏幕阅读器、焦点顺序、ARIA labels
6. **Animation**：过渡动效、微交互、duration/curve

---

## 工作流：提案生命周期

```
Step 1a/1b: Intake -- 注册提案（从现有代码库或新建）
Step 2: Clarify -- 最多3轮澄清
Step 3: 如需要则转给 PM
Step 4: PRD 确认门控
Step 5: 技术预期门控（最多3轮）
Step 6: 输出技术方案
Step 6b: 交接给 Test Expert -- 生成 TDD 测试用例（含 UI 测试增强）
Step 7: 交接给 Dev（以测试用例为参考，含任务拆解）
Step 8: Test Expert 基于测试用例进行验收
Step 9: 交付或返修（含 README + SPEC 更新）
Step 10: 研究方向（验收后迭代规划，含在线扩展）
Step 11: 部署（验收后交付，支持多目标）
```

### Step 1a: 从现有代码库注册

当需求是克隆现有 GitHub 仓库并注册为提案时（而非从零开始构建）：
1. 将仓库克隆到 `$superpower-dev/<project-name>/proposals/` 或本地复制
2. 对于设计文档项目（`*-design`），按照 Step 1b 作为常规提案处理

### Step 1b: 从零开始注册新提案

1. 通过 ai-superpower CLI 创建项目（如不存在）：
   ```bash
   ai-superpower project create --name "ProjectName" --git-repo "https://github.com/owner/repo"
   ```
2. 通过 MCP 工具 `proposal_create` 创建提案（ID 自动生成，无需手动管理）
3. 为此提案创建 gh-pages 分支（如果项目有远程仓库）：
   ```bash
   cd $DEV_PROPOSALS/<project-name>
   git checkout -b gh-pages
   ```
4. 将 `$TEMPLATES_DIR/request-intake-template.md` 复制到提案目录
5. 填写基本信息和原始需求
6. 通过 MCP 工具 `proposal_create` 创建提案：
   ```
   Tool: proposal_create
   Arguments: {"title": "ProposalTitle", "owner": "coordinator", "project_id": "PRJ-YYYYMMDD-XXX", "stage": "approved_for_dev"}
   ```

### Step 2: 澄清需求

- 最多向请求者进行3轮澄清提问，聚焦于：目标、范围、约束、验收标准
- 在提案的"Clarification"部分记录每轮问答
- 3轮之后或需求清晰时，记录最终假设
- 将状态流转到 `clarifying`：
  ```
  Tool: proposal_update_status
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "clarifying"}
  ```

### Step 3: 转给 PM

如果需求只是一个想法或粗略草案，转给 PM 角色来生成 PRD。

- PM 将 PRD 保存到 `$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md`
- PM 还将 PRD 复制到 `$DEV_PROPOSALS/<project-name>/docs/prd.v1.md`
- 通过 MCP 工具 `proposal_update_fields` 更新 PRD 路径：
  ```
  Tool: proposal_update_fields
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"prd_path": "$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md"}}
  ```

### Step 4: PRD 确认门控

PM 返回 PRD 后：
1. 向请求者展示 PRD 并请求确认
2. 开始确认倒计时（建议：5分钟）
3. 在"PRD Confirmation Countdown ID"中记录倒计时引用

如果确认：将 PRD Confirmation 设为 `confirmed`，取消倒计时，立即将状态流转为 `approved_for_dev` 并开始开发。
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "approved_for_dev"}
```

如果超时：将 PRD Confirmation 设为 `timeout-approved`，在"Timeout Resolution"中记录，立即将状态流转为 `approved_for_dev` 并开始开发。

### Step 5: 技术预期门控

在输出技术方案之前：
1. 从请求者处了解：技术栈、性能、成本、部署方式、可维护性、依赖约束
2. 最多3轮提问
3. 开始确认倒计时（与 Step 4 相同机制）
4. 在"Technical Expectations Countdown ID"中记录

如果确认：将 Technical Expectations 设为 `confirmed`，立即撰写技术方案并将状态流转为 `approved_for_dev`。

如果超时：将 Technical Expectations 设为 `timeout-approved`，按当前假设继续，立即撰写技术方案并将状态流转为 `approved_for_dev`。

**⚠️ 超时 cron 触发但 proposal-index.md 无对应条目时**：不要手动编辑 index，运行 `sync-proposals-to-website.py` 协调一致后，再用 MCP 工具更新字段。状态流转仍通过 ai-superpower API 执行——index 是派生数据，不是数据源。

### Step 6: 技术方案

- 将技术方案输出到 `$superpower-root/P-YYYYMMDD-XXX-tech-solution.md`
- 同时复制到 `$DEV_PROPOSALS/<project-name>/docs/technical-solution.v1.md`
- 通过 MCP 工具 `proposal_update_fields` 更新技术方案路径：
  ```
  Tool: proposal_update_fields
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"tech_solution_path": "$superpower-root/P-YYYYMMDD-XXX-tech-solution.md"}}
  ```

### Step 6b: TDD 测试用例生成

技术方案输出后，转交给 Test Expert 基于 TDD 原则生成测试用例：

1. Coordinator 将任务交接给 Test Expert，包含：PRD 文档、技术方案文档、项目背景
2. Test Expert 将测试用例输出到 `$superpower-test/<project-name>/YYYY-MM-DD-test-cases.md`
   - 测试用例必须可追溯到 PRD 需求
   - 包含：测试用例 ID、描述、前置条件、步骤、预期结果
   - 覆盖正常路径和边界情况
   - 将测试用例复制到 `$superpower-dev/<project-name>/proposals/docs/test-cases.v1.md`
3. **UI 测试增强（来自 GitHub）**
   - 在 GitHub 上搜索项目技术栈的测试模式（如 `playwright react testing`、`selenium e2e`、`testing-library best practices`）
   - 筛选同一框架下 500+ stars 的 Top 5 UI 测试仓库
   - 提取测试结构、page object 模式和覆盖率策略
   - UI 重度项目，自动追加以下测试用例：
     - 视觉回归测试（快照/pixel-diff）
     - 响应式布局测试（移动/平板/桌面断点）
     - 无障碍测试（axe-core、键盘导航、屏幕阅读器）
     - 加载态/骨架屏/错误边界测试
     - 交互测试（hover、focus、keyboard、touch、drag-drop）
4. 通过 MCP 工具 `proposal_update_status` 将状态流转为 `in_tdd_test`：
   ```
   Tool: proposal_update_status
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_tdd_test"}
   ```

### Step 7: 交接给开发

将状态流转为 `in_dev`：
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_dev"}
```
更新 project_path：
```
Tool: proposal_update_fields
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"project_path": "$DEV_PROPOSALS/<project-name>"}}
```
如果目录不存在，Dev 创建 `$DEV_PROPOSALS/<project-name>/docs/`。

**复杂需求任务拆解**：如果提案通过任务拆解流程分解为多个子任务，提供每个子任务的 `id`、`content` 和 `depends_on` 上下文。Dev 按子任务报告完成情况。

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
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_test_acceptance"}
```

如果所有测试用例通过：进入 Step 9（交付）

如果任何测试用例失败：将状态流转为 `test_failed`，输出结构化返修意见：
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "test_failed"}
```

### Step 9: 交付或返修

**在流转到 `accepted` 前，Test Expert 必须完成文档更新：**

1. **更新 README**：确保项目 README 反映最新交付物
   - 更新版本号（如有版本化）
   - 更新功能列表/变更日志
   - 部署目标变更时更新部署说明
   - UI 变更时更新截图/Demo 链接

2. **更新 SPEC**：将 `SPEC.md`（或 `SPEC.vN.md`）与已验收实现同步
   - 将所有已实现需求标记为 `DONE`
   - 记录与原始规格的任何偏差
   - 系统结构变更时更新架构图
   - 记录任何新约束或技术决策

3. README + SPEC 更新完成后，流转到 `accepted`：
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "accepted"}
```

如果验收失败：流转到 `needs_revision`，输出结构化返修意见：
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "needs_revision"}
```

### Step 10: 研究方向（验收后迭代规划）

验收通过后（状态变为 `accepted` 或 `delivered`）：

1. Coordinator 询问请求者："基于本次交付，你是想探索下一个迭代方向，还是先维护当前版本？"
2. 开始5分钟确认倒计时，创建 cron job
3. 在"Research Direction Countdown ID"中记录倒计时引用

如果确认：将 Research Direction 设为 `confirmed`，立即将任务转给 PM 生成下一个迭代 PRD。

如果超时：将 Research Direction 设为 `timeout-approved`，Coordinator 自行决定，立即将任务转给 PM 生成下一个迭代 PRD。

#### 研究扩展：在线搜索 + GitHub 智能

研究迭代方向时，Coordinator 自动从外部来源补充信息（不限于用户输入）：

**Step 10a：用户提供方向**
- 记录请求者明确提出的所有方向
- 这些是主输入——外部来源作为补充，而非替代

**Step 10b：在线搜索扩展**
- 在网上搜索相关技术趋势、竞品功能、新兴模式
- 搜索目标：产品类别关键词 + "best practices"、"2024 2025 trends"、"design patterns"
- 使用 `web` 工具集进行搜索

**Step 10c：GitHub 智能**
- 查询项目技术栈的 GitHub Trending
- 识别同一领域 Top 10 开源项目
- 对每个 Trending 仓库：记录 stars、最近提交、README 亮点、架构模式
- 筛选条件：100+ stars、6个月内活跃、Permissive license（MIT/Apache2）

**Step 10d：综合研究**
- 将用户方向 + 网络发现 + GitHub 智能结合
- 按与项目的相关性排序
- 以迭代选项（A/B/C/D/E 格式）呈现候选方向
- 无人值守模式：5分钟后自动选择第一个选项

**研究来源优先级：**

| 来源 | 适用场景 |
|------|----------|
| 请求者提供 | 始终（必需输入） |
| Web 搜索（web 工具） | UI/UX 改进、新功能 |
| GitHub Trending | 技术栈验证、架构灵感 |
| GitHub Top10 仓库 | 功能对标、差异化机会 |

### Step 11: 部署（验收后交付）

验收通过后（状态变为 `accepted`）：

1. 从项目配置或环境变量 `AI_SUPERPOWER_DEPLOY_TARGET` 确定部署目标
2. 创建部署分支
3. 准备部署（确保 package-lock.json 已提交，运行 `npm run build`）
4. 推送到远程
5. 通过目标特定方式触发部署（见下表）
6. 更新提案：将状态设为 `deployed`，记录 Deployment URL：
   ```
   Tool: proposal_update_status
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "deployed"}
   Tool: proposal_update_fields
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"deployment_url": "https://..."}}
   ```

#### 部署目标

| 目标 | 环境变量配置 | 部署方式 |
|------|------------|---------|
| **GitHub Pages** | `AI_SUPERPOWER_DEPLOY_TARGET=github-pages` | Push 到 `gh-pages` 分支，GitHub Actions 自动部署 |
| **Cloudflare Pages** | `AI_SUPERPOWER_DEPLOY_TARGET=cloudflare-pages` | `wrangler pages deploy` via Cloudflare Workers |
| **Aliyun OSS** | `AI_SUPERPOWER_DEPLOY_TARGET=aliyun-oss` | `ossutil` 或 Aliyun CLI 上传；需要 `ALIYUN_ACCESS_KEY_ID` + `ALIYUN_ACCESS_KEY_SECRET` + `ALIYUN_BUCKET` + `ALIYUN_REGION` |
| **AWS S3** | `AI_SUPERPOWER_DEPLOY_TARGET=aws-s3` | `aws s3 sync` 到 S3 bucket；需要 `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_BUCKET` + `AWS_REGION` |
| **Vercel** | `AI_SUPERPOWER_DEPLOY_TARGET=vercel` | `vercel --prod`；需要 `VERCEL_TOKEN` |
| **Netlify** | `AI_SUPERPOWER_DEPLOY_TARGET=netlify` | `netlify deploy --prod`；需要 `NETLIFY_AUTH_TOKEN` + `NETLIFY_SITE_ID` |

**新增目标**：在上表中添加新行即可。Coordinator 读取 `AI_SUPERPOWER_DEPLOY_TARGET` 环境变量，如值无法识别则报错并列出支持的目标。

**目标特定环境变量（在 ai-superpower 主机上设置）：**
```bash
# Aliyun OSS
export ALIYUN_ACCESS_KEY_ID=...
export ALIYUN_ACCESS_KEY_SECRET=...
export ALIYUN_BUCKET=my-bucket
export ALIYUN_REGION=cn-hangzhou

# AWS S3
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_BUCKET=my-bucket
export AWS_REGION=us-east-1
```

---

## MCP 工具参考

### health

检查 ai-superpower 服务器健康状态。无参数。

### project_list

列出项目。

参数：`search`（可选，搜索关键词）、`page_size`（可选，默认 20，最大 200）、`page`（可选，默认 1）

返回：`{"items": [...], "total": N, "page": N, "page_size": N}`

### project_get

获取指定项目。

参数：`project_id`（必填，如 `PRJ-20260523-001`）

### proposal_list

列出提案。

参数：`project_id`（可选）、`search`（可选）、`page_size`（可选）、`page`（可选）

返回：`{"items": [...], "total": N, "page": N, "page_size": N}`

### proposal_get

获取指定提案。

参数：`proposal_id`（必填，如 `P-20260523-001`）

### proposal_create

创建新提案。

参数：`title`（必填）、`owner`（必填）、`project_id`（必填）、`stage`（必填，仅接受 `"approved_for_dev"`）

> **⚠️ stage 值限制**：创建时 stage 只能设为 `"approved_for_dev"`，其他值返回 HTTP 422。

### proposal_update_fields

更新提案字段。

参数：`proposal_id`（必填）、`fields`（必填，JSON 对象）

支持的字段：`title`、`owner`、`stage`、`prd_path`、`tech_solution_path`、`project_path`、`tech_expectations`、`notes`、`deployment_url`

### proposal_update_status

状态机流转。

参数：`proposal_id`（必填）、`status`（必填，新状态）

> **⚠️ 有效状态转换**：
> - `intake` → `clarifying`
> - `clarifying` → `prd_pending_confirmation`
> - `prd_pending_confirmation` → `approved_for_dev`
> - `approved_for_dev` → `in_dev`
> - `in_dev` → `needs_revision` 或 `in_tdd_test`
> - `needs_revision` → `in_dev`
> - `in_tdd_test` → `in_dev` 或 `in_test_acceptance`
> - `in_test_acceptance` → `accepted` 或 `test_failed`
> - `test_failed` → `in_dev`
> - `accepted` → `deployed`
> - `deployed` → `delivered`

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
1. 项目 memory 文件（如 `MEMORY.md`）的相关章节
2. 每日日志（如 `memory/YYYY-MM-DD.md`）
3. 提案的 Notes 或 Main Fixes Applied 字段

---

## 备份和回滚

### 自动备份（系统内部触发）

ai-superpower 内部统计已创建提案的累计数量。每 N 个提案（默认 5，可通过 `AI_SUPERPOWER_BACKUP_INTERVAL` 环境变量配置），系统在 `intake` → `clarifying` 转换门前自动触发备份。

**Coordinator 职责——无需手动执行备份：**
1. 从提案 notes 的 `last_backup` 读取确认备份已完成
2. 如 `last_backup` 缺失且计数器已达阈值，报告"Backup pending — please ensure ai-superpower auto-backup is active"
3. 在提案审计跟踪中记录备份确认

**配置（在 ai-superpower 主机上设置）：**
```bash
export AI_SUPERPOWER_BACKUP_INTERVAL=5  # 默认5，设为任意正整数；0禁用
```

**环境变量为 0 或未设置**：自动备份禁用（仅手动备份）。

### 手动备份

```bash
source ~/.superpower-clockless/env  # Unix
# 或: .\.\superpower-clockless\env.bat  # Windows
bash scripts/backup_proposals.sh
```

**数据源必须是 ai-superpower API——禁止直接读写 CSV。** `backup_proposals.sh` 调用 `backup_api.py`，它会对 `/api/projects` 和 `/api/proposals` 进行分页，并将 JSON 转换为 CSV。

> **API endpoint 注意事项**：
> - 路径是 `/api/{entity}`，不是 `/api/v1/{entity}`（v1 前缀不存在）
> - `page_size` 最大为 200——传 1000 会返回 HTTP 422
> - 使用 `page=1`、`page=2`... 分页，直到 `len(items) >= total`

备份存储在：`superpower-backups/backup_YYYYMMDD_HHMMSS/`

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

| 命令 | 数据恢复 |
|------|----------|
| `full N` | 备份 N 中的所有 CSV + markdown 文件 |
| `project <id> N` | projects.csv 条目 + 相关提案 + 映射 |
| `proposal <id> N` | proposals.csv 中的单个提案 + 映射 |

**安全措施：**
- 全系统回滚前：创建当前状态的紧急备份
- 项目/提案回滚前：创建紧急备份
- 所有操作需要 `yes` 确认

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `AI_SUPERPOWER_API_KEY` | API 密钥（由 `superpower-clockless install` 写入 `~/.superpower-clockless/env`；Unix 上用 `source ~/.superpower-clockless/env`，Windows 上用 `.\.superpower-clockless\env.bat`） |
| `AI_SUPERPOWER_URL` | API 基础 URL，默认为 `http://127.0.0.1:8000` |

---

## 配置

| 变量 | 值 | 说明 |
|------|-------|-------------|
| superpower-root | `/home/hermes/proposals` | 所有 agent 文件的根目录 |
| superpower-dev | `{superpower-root}/workspace-dev/<project>/proposals` | Dev 工作空间 |
| superpower-pm | `{superpower-root}/workspace-pm/<project>/proposals` | PM 工作空间 |
| superpower-test | `{superpower-root}/workspace-test/<project>/proposals` | Test 工作空间 |
| superpower-research | `{superpower-root}/workspace-research/<project>/proposals` | Research 工作空间 |
| superpower-proposals | `{superpower-root}/workspace-proposals/<project>` | 提案（主索引）工作空间 |
| superpower-backups | `{superpower-root}/backups` | 备份存储目录 |
| `AI_SUPERPOWER_BACKUP_INTERVAL` | 默认 5 | 自动备份间隔（每 N 个提案），0 禁用 |
| `AI_SUPERPOWER_REFACTOR_ITERATIONS` | 默认 6 | 架构重构触发迭代间隔，0 禁用 |
| `AI_SUPERPOWER_DEPLOY_TARGET` | 默认 github-pages | 部署目标平台 |

---

## MCP 桥接快速参考

详见 `references/mcp-bridge-quick-ref.md`。