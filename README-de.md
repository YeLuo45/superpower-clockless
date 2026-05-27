# superpower-clockless

Cross-Agent-Installer für das Superpower-Vorschlagssystem.

Es bündelt zwei Fähigkeiten in einem portablen Projekt:

- `ai-superpower`: API-first Projekt-/Vorschlags-Speicher mit Audit-Protokollen, CSV-Sperrung, Validierung und Lifecycle-Übergängen.
- `prj-proposals-manager`: Plattformunabhängiger Skill für den vollständigen Vorschlags-Lifecycle: Intake, PRD, TDD, Entwicklungsübergabe, Abnahme, Deployment und Lieferung.

Das Design folgt dem `agentmemory`-Muster: ein gemeinsamer lokaler Service, plus dünne Adapter pro Agent für MCP/Config/Skills.

## Unterstützte Agents

| Agent | Integration |
| --- | --- |
| Hermes | `~/.hermes/config.yaml` MCP-Block + Skill-Kopie |
| OpenClaw | `~/.openclaw/openclaw.json` MCP-Block + Extension-Skill-Kopie |
| Cursor | `~/.cursor/mcp.json` MCP-Block + always-on Regel |
| Claude Code | `~/.claude.json` MCP-Block + `CLAUDE.md` Workflow-Hinweis |
| Codex CLI | `~/.codex/config.toml` MCP-Block + `AGENTS.md` Workflow-Hinweis |

## Schnellstart

```bash
pip install -e .
export AI_SUPERPOWER_API_KEY="<your-key>"
superpower-clockless agents
superpower-clockless mcp-info
superpower-clockless explain hermes
superpower-clockless install hermes --dry-run
superpower-clockless install hermes --api-url http://127.0.0.1:8000 --start-server
```

Während der Installation liest `superpower-clockless` die `AI_SUPERPOWER_API_KEY` oder `--api-key` und schreibt `~/.superpower-clockless/env` (Unix) bzw. `~/.superpower-clockless/env.bat` (Windows) mit:

```bash
export AI_SUPERPOWER_API_KEY="<your-key>"
```

Unter Windows verwenden Sie:

```bat
@echo off
set "AI_SUPERPOWER_API_KEY=<your-key>"
```

Sources Sie diese Datei aus Shell-Startup-Skripten, damit der Key in neuen Terminal-Sessions verfügbar ist.

Standardmäßig bootstrapped die Installation zuerst ein lokales ai-superpower-Grundgerüst unter `~/.superpower-clockless/ai-superpower`, bevor der ausgewählte Agent angebunden wird. Verwenden Sie `--skip-core` nur, wenn ai-superpower woanders bereits installiert ist.

Installieren Sie andere Hosts durch Ändern des Agent-Namens:

```bash
superpower-clockless install cursor
superpower-clockless install claude-code
superpower-clockless install codex
superpower-clockless install openclaw
```

## Architektur

```
Hermes / OpenClaw / Cursor / Claude Code / Codex
        | config + MCP + skill/rules
        v
superpower-clockless MCP bridge + adapter
        |
        v
ai-superpower REST API (Standard: http://127.0.0.1:8000)
        |
        v
projects.csv / proposals.csv / audit.log
```

## Repository-Aufbau

```
src/superpower_clockless/
  api_client.py                # ai-superpower REST-Client
  core.py                      # gebündeltes ai-superpower Core-Bootstrap
  doctor.py                    # Post-Install-Validierungsprüfungen
  explain.py                   # nicht-mutierende Install-Vorschau-Pläne
  mcp_server.py                # minimaler MCP stdio-Bridge
  installer.py                 # CLI-Installer und Config-Merge-Logik
  catalog/agents.json          # unterstützte Agent-Matrix
  templates/skills/            # gebündelter prj-proposals-manager Skill
  templates/ai-superpower/     # ai-superpower Paket-Metadaten-Snapshot
  templates/agents/            # Host-Anweisungsblöcke

tests/
  test_api_client.py              # REST-Client-Verhaltenstests
  test_mcp_server.py              # MCP-Bridge-Verhaltenstests
  test_installer.py               # Installer-Verhaltenstests
```

## MCP-Tools

`superpower-clockless mcp` startet eine stdio-JSON-RPC-Bridge. Die Bridge stellt diese Tools bereit:

- `health`
- `project_list`, `project_get`
- `proposal_list`, `proposal_get`, `proposal_create`
- `proposal_update_fields`, `proposal_update_status`

Verwenden Sie `superpower-clockless mcp-info`, um Tool-Namen zu inspizieren, ohne die stdio-Schleife zu starten.

## Doctor

Führen Sie den Post-Install-Doctor aus, um die lokale Host-Verkabelung und ai-superpower-Konnektivität zu verifizieren, ohne Dateien oder Daten zu mutieren:

```bash
superpower-clockless doctor --agent hermes
superpower-clockless doctor --agent all
superpower-clockless doctor --json
```

Der Doctor prüft Katalog-Metadaten, Host-Config-Dateien-Präsenz, MCP-Server-Einträge, Skill-/Regel-Dateien und `GET /health` auf der konfigurierten ai-superpower API-URL.

## Explain

Vorschau der Installer-Änderungen, bevor Dateien geschrieben werden:

```bash
superpower-clockless explain hermes
superpower-clockless explain all --json
superpower-clockless explain codex --start-server
```

Der Explain-Befehl verwendet den Install-Planer im Dry-Run-Modus und berichtet erweiterte Config-Pfade, Skill-Pfade, MCP-Server-Schlüssel, API-URL und geplante Aktionen.

## Sicherheitsregeln

- Alle Projekt-/Vorschlags-Datenschreibvorgänge müssen über die ai-superpower API/CLI erfolgen.
- CSV-Dateien sind Datenspeicher, keine Benutzer-Editing-Oberfläche.
- Existierende Agent-Config-Dateien werden zusammengeführt, nicht ersetzt.
- Standard-Installation bootstrapt ai-superpower Core vor Agent-Verkabelung; verwenden Sie `--skip-core` für Adapter-nur-Modus.
- `--dry-run` zeigt geplante Dateisystem-Änderungen ohne zu schreiben.

## Windows-Unterstützung

Auf Windows-Systemen:
- `~/.superpower-clockless/env.bat` wird für API-Key-Exporte geschrieben
- `set "AI_SUPERPOWER_API_KEY=<your-key>"` ist das Äquivalent zu `export`
- Pfade wie `~/.hermes/config.yaml` werden nach `%USERPROFILE%\.hermes\config.yaml` aufgelöst

## Entwicklung

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m superpower_clockless.cli agents
python -m superpower_clockless.cli mcp-info
python -m superpower_clockless.cli install hermes --dry-run
```