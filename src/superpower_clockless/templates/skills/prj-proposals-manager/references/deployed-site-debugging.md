# Debugging Deployed Sites vs Local Code Divergence

When a user reports bugs on a deployed site but local code doesn't match deployed features, follow this diagnostic workflow.

## Common Scenario
- User reports bug on deployed URL (e.g., `https://yeluo45.github.io/todo-list/`)
- Local repo has different/downsized features (no Agent/Cron buttons in UI)
- Need to find what code is actually running on the deployed site

## Step 1: Identify Deployed Commit from JS Filename

Deployed sites typically have hashed JS filenames like `main-Bi4BT0Tn.js`. The hash itself isn't directly meaningful, but you can:

1. **Check GitHub Actions/Deploy workflow** to find which commit was deployed:
   ```bash
   curl -s "https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=3"
   ```

2. **Check GitHub Pages deployment**:
   ```bash
   curl -s "https://api.github.com/repos/{owner}/{repo}/pages"
   ```

## Step 2: Examine Remote Git History

```bash
# List remote branches
git branch -a

# Check origin/master history
git log --oneline origin/master -5

# Find commits that added specific files
git log --oneline --all -- "src/App.tsx" | head -10

# Show file from specific commit
git show <sha>:src/App.tsx | head -50

# List directory contents at a commit
git show <sha>:src/  # tree <sha>:src/
```

## Step 3: Search Deployed Minified JS

When remote code is inaccessible, analyze the deployed JS directly:

```bash
# Download deployed JS
curl -s "https://yeluo45.github.io/todo-list/assets/main-Bi4BT0Tn.js" | head -100

# Search for text/UI elements
curl -s "https://yeluo45.github.io/todo-list/assets/main-Bi4BT0Tn.js" | grep -o '"Agent"\|"Cron"\|"设置"\|"🤖"\|"⏰"'

# Count .split( occurrences (often the source of "k.split is not a function" errors)
curl -s "...main.js" | grep -o '.split(' | wc -l

# Extract error-related code context
curl -s "...main.js" | grep -A2 -B2 'k.split'
```

## Step 4: Map Deployed Features to Source

From minified JS analysis, you can identify:
- React components: `function AgentPanel` → UI for Agent page
- State management: Redux/Zustand stores
- Key UI elements: buttons, modals, navigation
- Error patterns: where `.split()` is called on non-string types

## Step 5: Find the Matching Commit

```bash
# Search for specific text in all branches
git log --oneline --all -S "Agent 控制面板" | head -5

# Search for specific component/function
git log --oneline --all -S "agent-panel" | head -5
```

## Key Insight: Local v58-clean vs Deployed

The local branch `v58-clean` may be a cleaned-up version that removed features (Agent/Cron/设置), while `feat/mcp-tool-bridge` or `master` branch may have the full deployed code.

In this case:
- Local v58-clean: basic TaskInput/TaskList only
- Remote master-clean: full Agent system (CreatorAgent/ReviewAgent/ReminderAgent)
- Deployed commit: f19903b on feat/mcp-tool-bridge branch

## CSV Patch Pitfall

When editing `/home/hermes/proposals/proposals.csv`, the row structure is:
```
id,title,owner,status,project_id,project_name,stage,...
```

If you patch a row incorrectly, rows can concatenate or wrap. Always:
1. Read full file after patch
2. Verify line count increased by exactly 1 for new rows
3. If concatenation happens, restore from backup or re-read and patch again

## Reference: Common Error Patterns

### "k.split is not a function"
- Source: `k.split(",")` where `k` is not a string
- Likely in: tag processing, token parsing, form field handling
- Context: editing task and clicking "更新" (update) triggers this

### Agent/Cron 返回 Not Working  
- Deployed code has these pages, local doesn't
- Return button uses `window.history.back()` or React Router navigation
- Blank page indicates component mount failure, not navigation failure

### "设置" Button
- May be non-existent in some builds (feature flag disabled)
- Or routing issue where `/settings` path has no corresponding component