# local_path Population Workflow

## Unified /home/hermes/projects/ Standard (2026-05-21)

**As of 2026-05-21, ALL 69 projects have `local_path` → `/home/hermes/projects/<project-name>`.**

The actual project directories live in `/home/hermes/projects/`. The `workspace-dev/proposals/` directory contains **only symlinks** pointing to those directories.

```
/home/hermes/projects/               ← real project directories live here
├── ai-subscription/
├── monopoly3d/
├── AstrBot/              (moved from opensource/AstrBot)
├── OpenMAIC/             (moved from workspace-dev/proposals/OpenMAIC)
├── openspec/             (moved from opensource/OpenSpec, renamed from openspec-design)
├── prj-proposals-manager/
└── ... (69 total)

/home/hermes/proposals/workspace-dev/proposals/  ← ONLY symlinks
├── ai-subscription -> /home/hermes/projects/ai-subscription
├── AstrBot -> /home/hermes/projects/AstrBot
└── ... (69 symlinks total)
```

## Symlink Strategy

All 69 symlinks in `workspace-dev/proposals/` point to `/home/hermes/projects/<name>`. There are NO real project directories in `workspace-dev/proposals/` anymore.

## Python Population Script

```python
import csv, os

with open('projects.csv', 'r', encoding='utf-8') as f:
    projects = list(csv.reader(f))

header = projects[0]
lp_idx = header.index('local_path')
gr_idx = header.index('git_repo')

wp_dev = '/home/hermes/proposals/workspace-dev/proposals'
os.makedirs(wp_dev, exist_ok=True)

ws_dev = '/home/hermes/workspace-dev/proposals'
home = '/home/hermes'
opensource = '/home/hermes/opensource'
projects_dir = '/home/hermes/projects'

updated = []
for row in projects[1:]:
    if row[lp_idx]:  # skip already filled
        continue
    repo_name = row[gr_idx].split('/')[-1] if row[gr_idx] else ''
    alt = row[1]

    # Try all source locations
    src = None
    for base in [ws_dev, home, opensource, projects_dir]:
        for name in [repo_name, alt]:
            p = f'{base}/{name}'
            if os.path.isdir(p) and not os.path.islink(p):
                src = p
                break
        if src:
            break

    if src:
        target = f'{wp_dev}/{os.path.basename(src)}'
        if not os.path.exists(target):
            os.symlink(src, target)
        row[lp_idx] = target
        updated.append((row[0], row[1], target))

with open('projects.csv', 'w', encoding='utf-8', newline='') as f:
    csv.writer(f).writerows(projects)

print(f'Updated {len(updated)} rows')
```

## Key Insight

The `*-design` projects (VitePress documentation sites) are typically stored under `/home/hermes/opensource/, but there are important exceptions documented below.

### Standard pattern for `*-design` projects

When a project has `git_repo: https://github.com/YeLuo45/ohmypi-design`, the local path may be:
- `/home/hermes/opensource/ohmypi-design` (standard case)
- OR the symlink may point directly to the git clone in `workspace-dev/proposals/`

### Critical exceptions (2026-05-21 discovered)

These projects do NOT follow the standard `*-design` pattern and require careful verification:

| CSV `name` | Expected `local_path` | Actual filesystem | Git remote |
|------------|----------------------|-------------------|------------|
| `OpenMAIC` | `workspace-dev/proposals/OpenMAIC` | Real git clone at `workspace-dev/proposals/OpenMAIC` | `YeLuo45/OpenMAIC.git` |
| `AstrBot` | `opensource/AstrBot` | Real directory at `opensource/AstrBot` | NOT a git repo |
| `openspec` | `opensource/OpenSpec` | Real git clone at `opensource/OpenSpec` (not `openspec-design`) | No origin remote |
| `prj-proposals-manager` | `workspace-dev/proposals/prj-proposals-manager` | Real git clone at `workspace-dev/proposals/prj-proposals-manager` | `YeLuo45/prj-proposals-manager.git` |

**Key rule**: When in doubt, `ls` the actual filesystem path — do NOT assume the CSV `name` field maps to a directory of the same name.

### Unified `/home/hermes/projects/` standard (2026-05-21)

As of 2026-05-21, ALL 69 projects should have `local_path` pointing to `/home/hermes/projects/<project-name>`. The previous pattern of storing some projects in `workspace-dev/proposals/` or `opensource/` has been consolidated.

### Migration workflow (2026-05-21 revised)

**Step 1**: Compare `ls /home/hermes/projects/` vs `ls /home/hermes/proposals/workspace-dev/proposals/`
- projects/ has 69 real directories
- workspace-dev/proposals/ should have ONLY symlinks (69 symlinks)

**Step 2**: Find missing projects
```bash
# Projects in CSV but missing from projects/
python3 -c "
import csv, os
with open('/home/hermes/proposals/projects.csv') as f:
    csv_names = {r['name'] for r in csv.DictReader(f)}
proj_dirs = set(os.listdir('/home/hermes/projects/'))
missing = csv_names - proj_dirs
print(f'Missing from projects/: {len(missing)}')
for n in sorted(missing):
    print(f'  {n}')
"
```

**Step 3**: Check if missing projects exist in workspace-dev/proposals/ as real directories
- 17 projects were in workspace-dev/proposals/ as real directories, not symlinks
- These are NOT duplicate — they ARE the actual project locations
- Move them to projects/: `mv /home/hermes/proposals/workspace-dev/proposals/{name} /home/hermes/projects/`

**Step 4**: Delete duplicates in workspace-dev/proposals/
- After moving, workspace-dev/proposals/ may still have the old directories
- Delete the old copies: `rm -rf /home/hermes/proposals/workspace-dev/proposals/{name}`
- Do NOT just delete and re-symlink — the content may differ

**Step 5**: Clean non-project directories in workspace-dev/proposals/
Known non-project dirs to delete: `calculator-app.bak.*`, `dsw-*`, `shared`, `todo-ghpages`, `todo-list`, `whack-a-mole-3d-git`

**Step 6**: Create all symlinks
```python
import csv, os
csv_path = '/home/hermes/proposals/projects.csv'
symlink_dir = '/home/hermes/proposals/workspace-dev/proposals'
proj_root = '/home/hermes/projects'
with open(csv_path) as f:
    for r in csv.DictReader(f):
        name = r['name']
        target = os.path.join(proj_root, name)
        link_path = os.path.join(symlink_dir, name)
        if os.path.exists(target):
            if os.path.islink(link_path):
                os.remove(link_path)
            elif os.path.exists(link_path):
                continue  # skip real dirs
            os.symlink(target, link_path)
```

**Step 7**: Verify
```bash
# Count verification
ls /home/hermes/projects/ | wc -l          # should be 69
grep -c "" /home/hermes/proposals/projects.csv  # should be 70 (69 + header)
ls /home/hermes/proposals/workspace-dev/proposals/ | grep -c "^l"  # should be 69

# No broken symlinks
for f in /home/hermes/proposals/workspace-dev/proposals/*; do
  [ -L "$f" ] && [ ! -e "$f" ] && echo "BROKEN: $f"
done
```

**Known migration results** (2026-05-21):
- `OpenMAIC`: moved from `workspace-dev/proposals/OpenMAIC` → `projects/OpenMAIC`
- `AstrBot`: moved from `opensource/AstrBot` → `projects/AstrBot` (git_repo: YeLuo45/AstrBot, no local git)
- `openspec`: moved from `opensource/OpenSpec` → `projects/openspec` (renamed from `openspec-design`)
- `prj-proposals-manager`: moved from `workspace-dev/proposals/prj-proposals-manager` → `projects/prj-proposals-manager`


## Untracked Directories

`/home/hermes/proposals/workspace-dev/proposals/` may contain directories not yet in `projects.csv`. Before creating symlinks, check if the project already exists in CSV. Untracked but GitHub-hosted projects should be added to CSV with new `PRJ-YYYYMMDD-NNN` IDs before linking.

Known untracked (2026-05-16): `dsw-debug`, `dsw-deploy`, `dsw-fresh`, `dsw-new-deploy`, `shared`, `todo-ghpages`, `calculator-app.bak.*` — these are tools/temp/backup dirs, not projects to track.

## Migration Verification Checklist

When doing any work on `workspace-dev/proposals/` or `projects/`:

```
Step 1: Count verification
  ls /home/hermes/projects/ | wc -l          # must be 69
  grep -c "" /home/hermes/proposals/projects.csv  # must be 70 (69 data + 1 header)
  ls /home/hermes/proposals/workspace-dev/proposals/ | grep "^l" | wc -l  # must be 69

Step 2: Broken symlink check
  for f in /home/hermes/proposals/workspace-dev/proposals/*; do
    [ -L "$f" ] && [ ! -e "$f" ] && echo "BROKEN: $f"
  done

Step 3: CSV local_path distribution check
  python3 -c "
  import csv
  with open('/home/hermes/proposals/projects.csv') as f:
    rows = list(csv.DictReader(f))
  non_proj = [r for r in rows if not r['local_path'].startswith('/home/hermes/projects/')]
  print(f'Non-projects/ paths: {len(non_proj)}')
  for r in non_proj: print(f'  {r[\"id\"]} {r[\"name\"]}: {r[\"local_path\"]}')
  "

Step 4: CSV vs filesystem alignment
  python3 -c "
  import csv, os
  with open('/home/hermes/proposals/projects.csv') as f:
    csv_names = {r['name'] for r in csv.DictReader(f)}
  proj_dirs = set(os.listdir('/home/hermes/projects/'))
  missing = csv_names - proj_dirs
  extra = proj_dirs - csv_names
  if missing: print(f'CSV has but projects/ missing: {missing}')
  if extra: print(f'projects/ has but CSV missing: {extra}')
  if not missing and not extra: print('CSV and projects/ fully aligned')
  "
```

**Critical**: Do NOT trust a symlink's mere existence — `ls -la` shows the symlink even if the target is dead. Always `readlink` + `test -e`.

## After Editing CSV

After any CSV edit:
1. Verify row count: `wc -l projects.csv` (should be 70)
2. Verify all `local_path` start with `/home/hermes/projects/`
3. Run sync to push to GitHub:
```bash
cd /home/hermes/.hermes/skills/prj-proposals-manager
GITHUB_TOKEN=$(gh auth token) python3 scripts/sync-proposals-to-website.py
```

## Common Pitfalls

1. **Using raw `/home/hermes/{repo}` paths** instead of symlinks — breaks the centralized reference pattern
2. **Forgetting to create symlink** — `local_path` points to non-existent directory
3. **Wrong directory name** — some repos use alternate names (e.g., `todo-list` in filesystem vs `todolist` in git_repo)
4. **CRLF in CSV** — always run `sed -i 's/\r$//' projects.csv proposals.csv` after execute_code writes
5. **Forgetting `workspace-dev/` prefix** — the correct path is `workspace-dev/`, NOT `workplace-dev/` (persistent typo)
6. **Symlink already exists as real directory** — if `workspace-dev/proposals/{repo}` is already a real dir (not symlink), don't try to `os.symlink(src, target)` — just set `local_path` to that path directly

7. **Broken symlink (points to non-existent path)** — a symlink can exist but point to a path that doesn't exist. This is silently broken and worse than no symlink. **Always verify symlink target actually exists** with `readlink -f` + `test -e`:
   ```bash
   # WRONG: just checking symlink exists
   ls -la workspace-dev/proposals/openspec-design  # shows symlink, looks OK

   # CORRECT: verify target also exists
   test -e "$(readlink -f workspace-dev/proposals/openspec-design)" && echo OK || echo BROKEN
   ```
   Real case (2026-05-20): `openspec-design` symlink pointed to `/home/hermes/projects/openspec-design` (non-existent), while CSV correctly had `/home/hermes/opensource/OpenSpec`. Both symlink and CSV must be checked independently.

8. **`OpenMAIC` is a real git clone directory, NOT a symlink** — `workspace-dev/proposals/OpenMAIC` IS the actual project (a full git clone of YeLuo45/OpenMAIC), NOT a symlink. `/home/hermes/opensource/OpenMAIC` does NOT exist. CSV `local_path` for `OpenMAIC` must be `/home/hermes/proposals/workspace-dev/proposals/OpenMAIC`, NOT `/home/hermes/opensource/OpenMAIC`.

9. **`openspec-design` has duplicate content in two locations** — `/home/hermes/opensource/OpenSpec` is the real VitePress project (git clone of YeLuo45/openspec-design), while `/home/hermes/projects/openspec-design` is an orphan non-git directory with incomplete content. CSV and symlink must point to `/home/hermes/opensource/OpenSpec`. Do NOT use `projects/openspec-design` as the symlink target.

10. **`*-design` CSV name vs non-design directory name** — some projects have CSV `name` ending in `-design` but the actual opensource directory uses a non-design name:
   | CSV `name` | Actual directory |
   |------------|------------------|
   | `OpenMAIC` | `OpenMAIC` (no -design suffix, in workspace-dev/proposals/) |
   | `astrbot-design` | `AstrBot` |
   | `openspec-design` | `OpenSpec` |
   | `deepcode-design` | `DeepCode` |
   | `deepseek-coder-design` | `DeepSeek-Coder` |
   | `chatdev-design` | `ChatDev` |
   | `media-crawler-design` | `MediaCrawler` |
   | `bmad-method-design` | `BMAD-METHOD` |
   
   **Symptom**: `workspace-dev/proposals/{name}` symlink points to non-existent `/home/hermes/opensource/{name}` (e.g., `astrbot-design` → `/home/hermes/opensource/astrbot-design` which doesn't exist — correct path is `/home/hermes/opensource/AstrBot`).
   
   **Fix**: Before creating symlinks, verify the actual directory name in `/home/hermes/opensource/`. Use `ls /home/hermes/opensource/ | grep -i {partial-name}` to find the correct directory. Update both symlink target and CSV `local_path` to match the actual path.
   
   **Rule**: When migrating projects from `/home/hermes/opensource/`, always `ls /home/hermes/opensource/` first to get exact directory names — do NOT assume the CSV `name` field matches the filesystem directory name.

## Migration Verification Checklist

When migrating `/home/hermes/projects/` entries to `workspace-dev/proposals/` symlinks:

```
for each project:
  1. Check if /home/hermes/projects/{name} EXISTS (real dir or broken symlink)
  2. Check if workspace-dev/proposals/{name} EXISTS as symlink
  3. If symlink exists: verify readlink target == CSV local_path field
  4. If symlink missing: create symlink to correct source path
  5. If symlink target != CSV local_path: fix symlink AND CSV
  6. Verify target path actually exists (test -e)
  7. Update last_update in CSV if any field changed
```

**Critical**: Do NOT trust a symlink's mere existence — `ls -la` shows the symlink even if the target is dead. Always `readlink` + `test -e`.

## 2026-05-21 Session Findings

### Two-location directory trap

`workspace-dev/proposals/` may contain BOTH real directories AND symlinks for the same project. A directory may have git history and content that's DIFFERENT from what a symlink in the same location points to.

**Real case**: `prj-proposals-manager` existed as a real directory at `workspace-dev/proposals/prj-proposals-manager` (git: `YeLuo45/prj-proposals-manager.git`) while CSV `local_path` pointed to `/home/hermes/workspace-dev/proposals/prj-proposals-manager` (different git: `YeLuo45/proposals-manager.git`). These were two completely different projects.

**Before moving any directory, always check**:
```bash
# Compare git remotes
git -C /path/to/dir remote get-url origin

# Check inode to confirm identity
stat /path/to/dir | grep Inode
```

### prj_url/git_repo mismatch detection

Always verify `prj_url` is correctly inferred from `git_repo`:
```python
m = re.match(r'https://github\.com/YeLuo45/([^/]+)\.git', git_repo)
if m:
    expected_prj_url = f'https://yeluo45.github.io/{m.group(1)}/'
    if prj_url != expected_prj_url:
        print(f"MISMATCH: {prj_url} vs {expected_prj_url}")
```

**Real case**: `plants-vs-zombies` git_repo had `.git` suffix but prj_url was incorrectly inferred as `plants-vs-zombies-temp` instead of `plants-vs-zombies`.
