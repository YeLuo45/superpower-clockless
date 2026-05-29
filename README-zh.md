# superpower-clockless

Superpower 提案系统的跨 Agent 安装器。

它将两个能力打包成一个便携式项目：

- `ai-superpower`：API 优先的项目/提案存储，带审计日志、CSV 锁定、验证和生命周期流转。
- `prj-proposals-manager`：平台无关的提案生命周期技能，涵盖受理、PRD、TDD、开发交接、验收、部署和交付。

设计遵循 `agentmemory` 模式：一个共享本地服务，加上每个 Agent 的薄适配器（ MCP / 配置 / 技能）。

## 支持的 Agent

| Agent | 集成方式 |
| --- | --- |
| Hermes | `~/.hermes/config.yaml` MCP 块 + 技能复制 |
| OpenClaw | `~/.openclaw/openclaw.json` MCP 块 + 扩展技能复制 |
| Cursor | `~/.cursor/mcp.json` MCP 块 + 常驻规则 |
| Claude Code | `~/.claude.json` MCP 块 + `CLAUDE.md` 工作流备注 |
|| Codex CLI | `~/.codex/config.toml` MCP 块 + `AGENTS.md` 工作流备注 |

## 无 Python 环境安装

`superpower-clockless` 是 Python 应用。如果没有安装 Python，可使用以下方式。

### 方式一：Bootstrap 脚本（Linux/macOS）

运行 bootstrap 脚本——它会自动检测系统、安装 Python（如缺失），然后配置 superpower-clockless：

```bash
curl -fsSL https://raw.githubusercontent.com/YeLuo45/superpower-clockless/main/bootstrap.sh | bash
```

Bootstrap 脚本会：
1. 检测操作系统（Linux/macOS）
2. 通过系统包管理器安装 Python 3.10+（`apt`/`brew`/`yum`）
3. 在 `~/.superpower-clockless/venv` 创建 Python 虚拟环境
4. 将 superpower-clockless 安装到虚拟环境
5. 写入 `~/.superpower-clockless/env` 并提示设置 API key

安装完成后，添加到 shell 配置文件：
```bash
# Unix
echo 'source ~/.superpower-clockless/env' >> ~/.bashrc
source ~/.bashrc
```

### 方式二：Docker

```bash
# 拉取最新镜像
docker pull yeluo45/superpower-clockless:latest

# 运行容器
docker run -d \
  --name superpower-clockless \
  -p 8000:8000 \
  -e AI_SUPERPOWER_API_KEY="<your-key>" \
  yeluo45/superpower-clockless:latest
```

ai-superpower API 访问地址：`http://localhost:8000`。容器内运行 ai-superpower 服务 + superpower-clockless MCP 桥接。

### 方式三：独立可执行文件（Windows）

从 GitHub Releases 下载 Windows 独立可执行文件：

```powershell
# 下载并运行安装脚本
irm https://raw.githubusercontent.com/YeLuo45/superpower-clockless/main/bootstrap.ps1 | iex
```

bootstrap.ps1 脚本直接下载运行——无需 GitHub Releases 附件。

---

## 快速开始

```bash
# 安装 superpower-clockless（可编辑模式，从本地克隆仓库）
pip install -e .

# 设置 ai-superpower API 密钥（从 https://github.com/YeLuo45/ai-superpower 获取）
export AI_SUPERPOWER_API_KEY="<your-key>"

# 列出所有支持的 Agent 及其集成状态
superpower-clockless agents

# 显示可用的 MCP 桥接工具（不启动 stdio 循环）
superpower-clockless mcp-info

# 预览 hermes 安装计划（不写入任何文件）
superpower-clockless explain hermes

# 演练：显示 hermes 集成的计划文件系统变更
superpower-clockless install hermes --dry-run

# 完整安装：配置 hermes + 在 http://127.0.0.1:8000 启动 ai-superpower 服务
superpower-clockless install hermes --api-url http://127.0.0.1:8000 --start-server
```

安装过程中，`superpower-clockless` 读取 `AI_SUPERPOWER_API_KEY` 或 `--api-key`，并写入环境文件。Unix/macOS 使用 `~/.superpower-clockless/env`，Windows 使用 `~/.superpower-clockless/env.bat`。

```bash
# Unix / macOS
export AI_SUPERPOWER_API_KEY="<your-key>"
```

```bat
:: Windows
@echo off
set "AI_SUPERPOWER_API_KEY=<your-key>"
```

在新终端会话中使用密钥，需要将环境文件 source 到 shell 启动脚本中。

默认情况下，安装会首先在 `~/.superpower-clockless/ai-superpower` 引导本地 ai-superpower 脚手架，再连接选定的 Agent。仅在 ai-superpower 已安装在其他位置时才使用 `--skip-core`。

通过更改 Agent 名称来安装其他宿主：

```bash
superpower-clockless install cursor
superpower-clockless install claude-code
superpower-clockless install codex
superpower-clockless install openclaw
```

## 架构

```
Hermes / OpenClaw / Cursor / Claude Code / Codex
        | config + MCP + skill/rules
        v
superpower-clockless MCP bridge + adapter
        |
        v
ai-superpower REST API（默认 http://127.0.0.1:8000）
        |
        v
projects.csv / proposals.csv / audit.log
```

## 仓库结构

```
src/superpower_clockless/
  api_client.py                # ai-superpower REST 客户端
  core.py                      # 捆绑的 ai-superpower 核心引导
  doctor.py                    # 安装后验证检查
  explain.py                   # 非变更安装预览计划
  mcp_server.py                # 最小 MCP stdio 桥接
  installer.py                 # CLI 安装器和配置合并逻辑
  catalog/agents.json          # 支持的 Agent 矩阵
  templates/skills/            # 捆绑的 prj-proposals-manager 技能
  templates/ai-superpower/     # ai-superpower 包元数据快照
  templates/agents/            # 宿主指令块

tests/
  test_api_client.py              # REST 客户端行为测试
  test_mcp_server.py              # MCP 桥接行为测试
  test_installer.py               # 安装器行为测试
```

## MCP 工具

`superpower-clockless mcp` 启动 stdio JSON-RPC 桥接。桥接暴露以下工具：

- `health`
- `project_list`, `project_get`
- `proposal_list`, `proposal_get`, `proposal_create`
- `proposal_update_fields`, `proposal_update_status`

使用 `superpower-clockless mcp-info` 检查工具名称，无需启动 stdio 循环。

## Doctor

运行安装后 Doctor 验证本地宿主连接和 ai-superpower 连通性，不变更文件或数据：

```bash
superpower-clockless doctor --agent hermes
superpower-clockless doctor --agent all
superpower-clockless doctor --json
```

Doctor 检查目录元数据、宿主配置文件存在性、MCP 服务器条目、技能/规则文件，以及对配置的 ai-superpower API URL 的 `GET /health`。

## Explain

在写入文件之前预览安装变更：

```bash
superpower-clockless explain hermes
superpower-clockless explain all --json
superpower-clockless explain codex --start-server
```

Explain 命令在 dry-run 模式下复用安装规划器，报告扩展后的配置路径、技能路径、MCP 服务器密钥、API URL 和计划操作。

## 安全规则

- 所有项目/提案数据写入必须通过 ai-superpower API/CLI 进行。
- CSV 文件是数据存储，而非用户编辑界面。
- 现有 Agent 配置文件会被合并，而非替换。
- 默认安装会在 Agent 连接之前引导 ai-superpower 核心；使用 `--skip-core` 仅进行适配器模式。
- `--dry-run` 显示计划的文件系统变更，不执行写入。

## Windows 支持

在 Windows 系统上：

- API 密钥导出写入 `~/.superpower-clockless/env.bat`
- `set "AI_SUPERPOWER_API_KEY=<your-key>"` 是 `export` 的等效写法
- 路径如 `~/.hermes/config.yaml` 会解析为 `%USERPROFILE%\.hermes\config.yaml`
- PowerShell 用户：运行 `.\.superpower-clockless\env.bat` 或将其添加到 `$PROFILE`

## 多语言文档

| 文件 | 语言 |
| --- | --- |
| `README.md` | English |
| `README-zh.md` | 中文（Chinese） |
| `README-de.md` | 德语（Deutsch） |
| `README-fr.md` | 法语（Français） |
| `README-ja.md` | 日语（日本語） |

## 开发

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m superpower_clockless.cli agents
python -m superpower_clockless.cli mcp-info
python -m superpower_clockless.cli install hermes --dry-run
```