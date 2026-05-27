# superpower-clockless

Installateur multi-agent pour le système de propositions Superpower.

Il regroupe deux capacités dans un projet portable :

- `ai-superpower` : stockage projet/proposition API-first avec journaux d'audit, verrouillage CSV, validation et transitions de cycle de vie.
- `prj-proposals-manager` : skill de cycle de vie de proposition agnostique pour intake, PRD, TDD, handover dev, acceptance, déploiement et livraison.

Le design suit le pattern `agentmemory` : un service local partagé, plus des adaptateurs minces par agent pour MCP/config/skills.

## Agents Supportés

| Agent | Intégration |
| --- | --- |
| Hermes | `~/.hermes/config.yaml` bloc MCP + copie skill |
| OpenClaw | `~/.openclaw/openclaw.json` bloc MCP + copie skill extension |
| Cursor | `~/.cursor/mcp.json` bloc MCP + règle always-on |
| Claude Code | `~/.claude.json` bloc MCP + note workflow `CLAUDE.md` |
| Codex CLI | `~/.codex/config.toml` bloc MCP + note workflow `AGENTS.md` |

## Démarrage Rapide

```bash
pip install -e .
export AI_SUPERPOWER_API_KEY="<your-key>"
superpower-clockless agents
superpower-clockless mcp-info
superpower-clockless explain hermes
superpower-clockless install hermes --dry-run
superpower-clockless install hermes --api-url http://127.0.0.1:8000 --start-server
```

Pendant l'installation, `superpower-clockless` lit `AI_SUPERPOWER_API_KEY` ou `--api-key` et écrit `~/.superpower-clockless/env` (Unix) ou `~/.superpower-clockless/env.bat` (Windows) avec :

```bash
export AI_SUPERPOWER_API_KEY="<your-key>"
```

Sous Windows, utilisez :

```bat
@echo off
set "AI_SUPERPOWER_API_KEY=<your-key>"
```

Sources ce fichier depuis les scripts de démarrage shell pour rendre la clé disponible dans les nouvelles sessions terminal.

Par défaut, l'installation bootstrappe d'abord un scaffold ai-superpower local dans `~/.superpower-clockless/ai-superpower`, puis wire l'agent sélectionné. Utilisez `--skip-core` uniquement quand ai-superpower est déjà installé ailleurs.

Installez d'autres hosts en changeant le nom de l'agent :

```bash
superpower-clockless install cursor
superpower-clockless install claude-code
superpower-clockless install codex
superpower-clockless install openclaw
```

## Architecture

```
Hermes / OpenClaw / Cursor / Claude Code / Codex
        | config + MCP + skill/rules
        v
superpower-clockless MCP bridge + adapter
        |
        v
ai-superpower REST API (défaut http://127.0.0.1:8000)
        |
        v
projects.csv / proposals.csv / audit.log
```

## Structure du Dépôt

```
src/superpower_clockless/
  api_client.py                # client REST ai-superpower
  core.py                      # bootstrap core ai-superpower bundle
  doctor.py                    # validations post-install
  explain.py                   # aperçus d'installation non-mutatifs
  mcp_server.py                # pont stdio MCP minimal
  installer.py                 # installateur CLI et logique de fusion config
  catalog/agents.json          # matrice des agents supportés
  templates/skills/            # skill prj-proposals-manager bundle
  templates/ai-superpower/     # snapshot métadonnées package ai-superpower
  templates/agents/            # blocs d'instructions host

tests/
  test_api_client.py              # tests comportementaux client REST
  test_mcp_server.py              # tests comportementaux pont MCP
  test_installer.py               # tests comportementaux installateur
```

## Outils MCP

`superpower-clockless mcp` démarre un pont stdio JSON-RPC. Le pont expose ces outils :

- `health`
- `project_list`, `project_get`
- `proposal_list`, `proposal_get`, `proposal_create`
- `proposal_update_fields`, `proposal_update_status`

Utilisez `superpower-clockless mcp-info` pour inspecter les noms d'outils sans démarrer la boucle stdio.

## Doctor

Lancez le doctor post-install pour vérifier le câblage local host et la connectivité ai-superpower sans muter fichiers ou données :

```bash
superpower-clockless doctor --agent hermes
superpower-clockless doctor --agent all
superpower-clockless doctor --json
```

Le doctor vérifie les métadonnées du catalogue, la présence des fichiers config host, les entrées serveur MCP, les fichiers skill/règle et `GET /health` sur l'URL API ai-superpower configurée.

## Explain

Aperçu des changements installer avant d'écrire des fichiers :

```bash
superpower-clockless explain hermes
superpower-clockless explain all --json
superpower-clockless explain codex --start-server
```

La commande explain réutilise le planificateur d'installation en mode dry-run et rapporte les chemins config étendus, chemins skill, clés serveur MCP, URL API et actions planifiées.

## Règles de Sécurité

- Toutes les écritures de données projet/proposition doivent passer par l'API/CLI ai-superpower.
- Les fichiers CSV sont du stockage de données, pas une interface d'édition utilisateur.
- Les fichiers config agent existants sont fusionnés, non remplacés.
- L'installation par défaut bootstrap le core ai-superpower avant le câblage agent ; utilisez `--skip-core` pour le mode adaptateur uniquement.
- `--dry-run` montre les changements filesystem planifiés sans écrire.

## Support Windows

Sur les systèmes Windows :
- `~/.superpower-clockless/env.bat` est écrit pour les exports de clé API
- `set "AI_SUPERPOWER_API_KEY=<your-key>"` est l'équivalent de `export`
- Les chemins comme `~/.hermes/config.yaml` sont résolus vers `%USERPROFILE%\.hermes\config.yaml`

## Développement

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m superpower_clockless.cli agents
python -m superpower_clockless.cli mcp-info
python -m superpower_clockless.cli install hermes --dry-run
```