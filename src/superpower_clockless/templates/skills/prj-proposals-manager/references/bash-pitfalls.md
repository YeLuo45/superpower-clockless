# bash-pitfalls.md — Shell Scripting Pitfalls for Proposal System Scripts

> Discovered: 2026-05-15

## Pitfall 1: `((var++))` Returns Exit Code 1 When Value Is 0

### Problem

In bash with `set -e`, using `((success++))` will **abort the script** when `success` starts at 0. The `(( ))` arithmetic expansion returns exit code **1** (false) when the expression evaluates to 0.

```bash
set -e
success=0
((success++))   # evaluates to 0, exits with code 1, script aborts!
```

### Symptom

```
📄 备份索引和配置文件...
  ✅ project-index.md
  ✅ proposal-docs-index.md
  ... (script aborts on ((success++)) when success=0)
```

### Fix

Use `var=$((var + 1))` instead of `((var++))`:

```bash
# WRONG — breaks with set -e when var=0
((success++))

# CORRECT
success=$((success + 1))
```

### Affected Scripts

- `backup_proposals.sh` — fixed at lines using `((success++))`, `((failed++))`, `((total++))`
- `rollback_proposals.sh` — same pattern, fixed

---

## Pitfall 2: cp -r Hangs on Large Directories (workspace-dev)

### Problem

Copying `workspace-dev/` (full git repositories) with `cp -r` can hang indefinitely, causing cron jobs to timeout and leaving backups in half-complete state.

```bash
# This can hang for minutes or timeout
cp -r "$WORKSPACE_DIR" "${BACKUP_DIR}/workspace-${workspace}"
```

### Symptom

```
📁 备份 workspace-dev...
[Command timed out after 60s]
# MANIFEST.md never written, backup incomplete
```

### Fix

**For cron jobs: skip large workspace directories**

Core CSV/markdown backup completes in <5s. Backup workspaces in a separate async job or manually.

```bash
# Fast backup: core data only (<5s)
CORE_FILES=(projects.csv proposals.csv project_proposal_mapping.csv proposal-index.md ...)
for f in "${CORE_FILES[@]}"; do
    [ -f "$f" ] && cp "$f" "${BACKUP_DIR}/"
done
```

**If workspaces must be included: use rsync with timeout**

```bash
timeout 30 rsync -a "$WORKSPACE_DIR/" "${BACKUP_DIR}/workspace-${workspace}/" || true
```

---

## Pitfall 3: Missing Quote Causes Path Breakage

### Problem

```bash
# WRONG — space after $TEMPLATES_DIR splits the path
cp -r "$TEMPLATES_DIR "${BACKUP_DIR}/templates"
# Shell interprets: cp -r "/path" "" + second arg = empty!
```

### Fix

Always attach quotes directly to the variable:

```bash
# CORRECT
cp -r "$TEMPLATES_DIR" "${BACKUP_DIR}/templates"
```

---

## Pitfall 4: `ls -1t` Returns Full Paths on Some Systems

### Problem

```bash
for backup in $(ls -1t "$BACKUP_DIR"/proposals_backup_*.tar.gz 2>/dev/null); do
```

On some systems `ls -1t` returns full paths. Use `basename`:

```bash
backup_name=$(basename "$backup")
```
