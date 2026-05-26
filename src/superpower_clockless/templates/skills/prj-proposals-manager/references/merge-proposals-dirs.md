# Proposal Directory Merge Workflow

## Context (Updated 2026-05-21)

**2026-05-21 迁移**：提案系统从 `~/.hermes/proposals` 迁移到 `/home/hermes/proposals/`。

```
/home/hermes/
├── projects/          ← 69 project directories
└── proposals/         ← proposal management system root (moved from ~/.hermes/proposals)
    ├── projects.csv
    ├── proposals.csv
    ├── workspace-dev/proposals/   ← symlinks to /home/hermes/projects/<name>
    └── ...
```

## Critical: mv Glob Overwrite Trap

**⚠️ NEVER use `mv source/*.md target/` when same-named files exist in target.**

This silently overwrites files in `target/` with files from `source/`. In this session, migrating `/home/hermes/prj-proposals/*.md` to `/home/hermes/proposals/prj-proposals/` overwrote `PRJ-20260506-001.md` (60KB → 1.4KB) and `PRJ-20260506-002.md` (15KB → 449B).

**Recovery**:
```bash
cd /home/hermes/proposals
git checkout HEAD -- prj-proposals/PRJ-20260506-001.md prj-proposals/PRJ-20260506-002.md
```

**Safe alternatives**:
1. Use `cp -n` (no overwrite) or compare sizes before copying
2. Use Python with conflict detection
3. List target files first and verify no name collisions

## Merge Procedure

```python
import os, shutil

src = '/home/hermes/proposals'
dst = '/home/hermes/.hermes/proposals'

# 1. Root .md files (skip proposal-index.md which already exists)
for f in os.listdir(src):
    if not f.endswith('.md') or f == 'proposal-index.md':
        continue
    src_path = f'{src}/{f}'
    dst_path = f'{dst}/{f}'
    if not os.path.exists(dst_path):
        shutil.copy2(src_path, dst_path)

# 2. workspace-pm/proposals (merge, skip dirs and existing files)
src_pm = f'{src}/workspace-pm/proposals'
dst_pm = f'{dst}/workspace-pm/proposals'
os.makedirs(dst_pm, exist_ok=True)
for f in os.listdir(src_pm):
    src_path = f'{src_pm}/{f}'
    if os.path.isdir(src_path):
        continue  # skip subdirs (e.g., "P19")
    dst_path = f'{dst_pm}/{f}'
    if not os.path.exists(dst_path):
        shutil.copy2(src_path, dst_path)

# 3. prj-proposals
src_prj = f'{src}/prj-proposals'
dst_prj = f'{dst}/prj-proposals'
os.makedirs(dst_prj, exist_ok=True)
for f in os.listdir(src_prj):
    if os.path.isdir(f'{src_prj}/{f}'):
        continue
    if not os.path.exists(f'{dst_prj}/{f}'):
        shutil.copy2(f'{src_prj}/{f}', f'{dst_prj}/{f}')

# 4. workspace-dev/proposals — symlink from canonical location
# (already done via local_path population; just verify)

# 5. Remove old directory
shutil.rmtree(src)
```

## What Gets Merged

| Location | What | Notes |
|----------|------|-------|
| Root `.md` | PRJ-YYYYMMDD-XXX.md files | Skip `proposal-index.md` (already canonical) |
| `workspace-pm/proposals/` | PRD and proposal markdown files | Skip subdirectories and existing files |
| `prj-proposals/` | Project-level documents | **Check for name collisions before merge** |
| `workspace-dev/proposals/` | Actual project directories | **Don't merge — use symlinks instead** (see local-path-population.md) |

## Safe Merge Procedure for prj-proposals

```python
import os, shutil

src_prj = '/home/hermes/prj-proposals'
dst_prj = '/home/hermes/proposals/prj-proposals'
os.makedirs(dst_prj, exist_ok=True)

# Check for collisions BEFORE copying
src_files = set(os.listdir(src_prj))
dst_files = set(os.listdir(dst_prj))
collisions = src_files & dst_files

if collisions:
    print(f"WARNING: {len(collisions)} files would be overwritten:")
    for f in sorted(collisions):
        src_size = os.path.getsize(f'{src_prj}/{f}')
        dst_size = os.path.getsize(f'{dst_prj}/{f}')
        print(f"  {f}: src={src_size} dst={dst_size}")
    # Decide: skip, overwrite, or rename

for f in os.listdir(src_prj):
    if os.path.isdir(f'{src_prj}/{f}'):
        continue
    if f in collisions:
        continue  # skip duplicates
    shutil.copy2(f'{src_prj}/{f}', f'{dst_prj}/{f}')
```

## Verification

After merge:
```bash
# Verify old dir removed
ls /home/hermes/prj-proposals  # should fail or be empty

# Verify files transferred
ls /home/hermes/proposals/prj-proposals/ | wc -l

# If overwrite happened, recover from git:
cd /home/hermes/proposals
git checkout HEAD -- prj-proposals/
```

## Post-Merge Sync

Always run sync after merge:
```bash
cd /home/hermes/.hermes/skills/prj-proposals-manager
GITHUB_TOKEN=$(gh auth token) python3 scripts/sync-proposals-to-website.py
```

Note: PROPOSALS_ROOT is now `/home/hermes/proposals` (moved from `~/.hermes/proposals` on 2026-05-21).