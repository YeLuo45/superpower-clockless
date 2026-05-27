# superpower-clockless

Superpower提案システムのクロスエージェントインストーラー。

2つの能力を1つのポータブルプロジェクトにまとめます：

- `ai-superpower`：監査ログ、CSVロック、検証、ライフサイクル遷移を備えたAPIファーストのプロジェクト/提案ストレージ。
- `prj-proposals-manager`：インテイク、PRD、TDD、開発handoff、受け入れ、デプロイメント、配達のためのプラットフォーム非依存提案ライフサイクルスキル。

設計は`agentmemory`パターンを採用：1つの共有ローカルサービスと、MCP/設定/スキル用の薄いエージェントごと'adapter。

## 対応エージェント

| エージェント | 統合方法 |
| --- | --- |
| Hermes | `~/.hermes/config.yaml` MCPブロック + スキルコピー |
| OpenClaw | `~/.openclaw/openclaw.json` MCPブロック + 拡張スキルコピー |
| Cursor | `~/.cursor/mcp.json` MCPブロック + 常時オンのルール |
| Claude Code | `~/.claude.json` MCPブロック + `CLAUDE.md` ワークフロー備考 |
| Codex CLI | `~/.codex/config.toml` MCPブロック + `AGENTS.md` ワークフロー備考 |

## クイックスタート

```bash
pip install -e .
export AI_SUPERPOWER_API_KEY="<your-key>"
superpower-clockless agents
superpower-clockless mcp-info
superpower-clockless explain hermes
superpower-clockless install hermes --dry-run
superpower-clockless install hermes --api-url http://127.0.0.1:8000 --start-server
```

インストール中、`superpower-clockless`は`AI_SUPERPOWER_API_KEY`または`--api-key`を読み取り、`~/.superpower-clockless/env`（Unix）または`~/.superpower-clockless/env.bat`（Windows）に以下を書き込みます：

```bash
export AI_SUPERPOWER_API_KEY="<your-key>"
```

Windowsでは以下を使用します：

```bat
@echo off
set "AI_SUPERPOWER_API_KEY=<your-key>"
```

新しいターミナルセッションでキーを利用可能にするには、シェルの起動スクリプトからこのファイルをsourceしてください。

デフォルトでは、インストールは最初に`~/.superpower-clockless/ai-superpower`にローカルのai-superpowerスキャフォールドをブートストラップしてから、選択したエージェントを接続します。ai-superpowerが既に別の場所にインストールされている場合のみ`--skip-core`を使用してください。

エージェント名を変更して他のホストをインストールします：

```bash
superpower-clockless install cursor
superpower-clockless install claude-code
superpower-clockless install codex
superpower-clockless install openclaw
```

## アーキテクチャ

```
Hermes / OpenClaw / Cursor / Claude Code / Codex
        | config + MCP + skill/rules
        v
superpower-clockless MCP bridge + adapter
        |
        v
ai-superpower REST API（デフォルト: http://127.0.0.1:8000）
        |
        v
projects.csv / proposals.csv / audit.log
```

## リポジトリ構成

```
src/superpower_clockless/
  api_client.py                # ai-superpower RESTクライアント
  core.py                      # バンドルされたai-superpowerコアブートストラプ
  doctor.py                    # インストール後検証チェック
  explain.py                   # 非変異インストールプレビュープラン
  mcp_server.py                # 最小MCP stdioブリッジ
  installer.py                 # CLIインストーラーと設定マージロジック
  catalog/agents.json          # 対応エージェントマトリックス
  templates/skills/            # バンドルされたprj-proposals-managerスキル
  templates/ai-superpower/     # ai-superpowerパッケージメタデータスナップショット
  templates/agents/            # ホスト命令ブロック

tests/
  test_api_client.py              # RESTクライアント動作テスト
  test_mcp_server.py              # MCPブリッジ動作テスト
  test_installer.py               # インストーラー動作テスト
```

## MCPツール

`superpower-clockless mcp`はstdio JSON-RPCブリッジを開始します。ブリッジは以下のツールを公開します：

- `health`
- `project_list`, `project_get`
- `proposal_list`, `proposal_get`, `proposal_create`
- `proposal_update_fields`, `proposal_update_status`

stdioループを開始せずにツール名を検査するには`superpower-clockless mcp-info`を使用してください。

## Doctor

ローカルホスト接続とai-superpower接続性を検証するために、ファイルやデータを変更せずにインストール後Doctorを実行します：

```bash
superpower-clockless doctor --agent hermes
superpower-clockless doctor --agent all
superpower-clockless doctor --json
```

Doctorはカタログメタデータ、ホスト設定ファイル的存在、MCPサーバーエントリ、スキル/ルールファイル、 구성된ai-superpower API URLへの`GET /health`をチェックします。

## Explain

ファイルを書く前にインストーラーの変更をプレビュー：

```bash
superpower-clockless explain hermes
superpower-clockless explain all --json
superpower-clockless explain codex --start-server
```

explainコマンドはインストールプランナーをdry-runモードで再利用し、拡張された設定パス、スキルパス、MCPサーバーキー、API URL、計画されたアクションを報告します。

## 安全ルール

- すべてのプロジェクト/提案データ書き込みはai-superpower API/CLI経由で実行する必要があります。
- CSVファイルはデータストレージであり、ユーザー編集インターフェースではありません。
- 既存のエージェント設定ファイルはマージされ、置き換えられません。
- デフォルトインストールはエージェント接続前にai-superpowerコアをブートストラップします。adapter 전용 모드では`--skip-core`を使用してください。
- `--dry-run`はファイルシステムへの変更を書き込みせずに表示します。

## Windowsサポート

Windowsシステムでは：
- APIキーエクスポートには`~/.superpower-clockless/env.bat`が書き込みされます
- `set "AI_SUPERPOWER_API_KEY=<your-key>"`は`export`の同等物です
- `~/.hermes/config.yaml`のようなパスは`%USERPROFILE%\.hermes\config.yaml`に解決されます

## 開発

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m superpower_clockless.cli agents
python -m superpower_clockless.cli mcp-info
python -m superpower_clockless.cli install hermes --dry-run
```