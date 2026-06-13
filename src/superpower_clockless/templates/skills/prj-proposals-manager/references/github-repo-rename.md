# GitHub Repo Rename — Post-Rename CSV Update Playbook

## The Problem

When a GitHub repository is renamed via GitHub REST API (`PATCH /repos/{owner}/{repo}`), the proposal system CSV records do NOT automatically update. This causes:

- `projects.csv` pointing to old repo name in `git_repo`
- `projects.csv` `prj_url` still using old deployment URL (`https://yeluo45.github.io/{old-name}/`)
- `proposals.csv` `git_repo` field and `notes` field (containing deployment URLs) stale

## GitHub API Rename

```bash
# Correct invocation (--method PATCH required)
gh api repos/{owner}/{old-name} --method PATCH -f name='{new-name}'

# Wrong — returns HTTP 400 Bad request
gh api repos/{owner}/{old-name} -f name='{new-name}'
```

## Required CSV Updates After Rename

### 1. projects.csv

| Field | Old | New |
|-------|-----|-----|
| `name` | `old-name` | `new-name` |
| `git_repo` | `https://github.com/YeLuo45/old-name` | `https://github.com/YeLuo45/new-name` |
| `prj_url` | `https://yeluo45.github.io/old-name/` | `https://yeluo45.github.io/new-name/` |

```bash
# Update projects.csv (sed works for simple replacements)
cd /home/hermes/proposals
sed -i 's|YeLuo45/old-name|YeLuo45/new-name|g' projects.csv
sed -i 's|yeluo45.github.io/old-name/|yeluo45.github.io/new-name/|g' projects.csv
sed -i 's|,old-name,|,new-name,|' projects.csv
```

### 2. proposals.csv

| Field | Update |
|-------|--------|
| `git_repo` | Replace `YeLuo45/old-name` → `YeLuo45/new-name` |
| `notes` | Replace deployment URLs in any embedded URLs |

```bash
sed -i 's|YeLuo45/old-name|YeLuo45/new-name|g' proposals.csv
sed -i 's|yeluo45.github.io/old-name/|yeluo45.github.io/new-name/|g' proposals.csv
```

### 3. proposal-index.md

Usually regenerated from CSV via `sync-to-index`, but if manually maintained:
```bash
sed -i 's|YeLuo45/old-name|YeLuo45/new-name|g' proposal-index.md
sed -i 's|yeluo45.github.io/old-name/|yeluo45.github.io/new-name/|g' proposal-index.md
```

## Verification

```bash
# Verify projects.csv has no remaining old-name references
grep "old-name" projects.csv && echo "STALE FOUND" || echo "Clean"

# Verify proposals.csv has no remaining old-name references
grep "old-name" proposals.csv && echo "STALE FOUND" || echo "Clean"

# Verify new-name appears correctly
grep "new-name" projects.csv
grep "new-name" proposals.csv
```

## Sequence

1. Rename repo via GitHub API: `gh api repos/{owner}/{old} --method PATCH -f name='{new}'`
2. Update `projects.csv` (3 field changes)
3. Update `proposals.csv` (git_repo + notes URLs)
4. Verify integrity with `mcp_aisp.py get-audit --entity project --since 2026-06-01` (look for the rename op)
5. Force index regeneration with `mcp_aisp.py get-sync-status` (or run `sync-proposals-to-website.py`)
