# Common Pitfalls (prj-proposals-manager v5.0.0+)

**Read this FIRST when something breaks.** These issues come up repeatedly in v5 work — checking this list saves deep debugging.

---

## P1. `act(...) is not supported in production builds of React` (vitest)

**Symptom**: Every `renderHook` / `render` in vitest throws this error.
**Cause**: `npx vitest run` defaults to `NODE_ENV=production`, which makes React skip dev-only `act()` support.
**Fix**: Run with `NODE_ENV=test npx vitest run` (or `NODE_ENV=development`). Always.

```bash
# WRONG (fails in SPA / hook tests)
npx vitest run

# RIGHT
NODE_ENV=test npx vitest run
```

The same fix applies to any test that uses `@testing-library/react`. This bites for every new project that copies vitest setup from this skill.

---

## P2. `npm install` omits dev dependencies (vitest, jsdom, etc.)

**Symptom**: After `git pull` or fresh clone, `npx vitest` says "command not found" or `@testing-library/react` is missing.
**Cause**: `NODE_ENV=production` causes npm to skip `devDependencies` per default npm config (`omit=dev`).
**Fix**: `NODE_ENV=development npm install --include=dev`.

```bash
# WRONG (missing vitest, @testing-library, jsdom)
npm install
NODE_ENV=production npm install

# RIGHT
NODE_ENV=development npm install --include=dev
```

Apply this whenever you set up a fresh prj-proposals-manager-based project (ma-prj-proposal-manager included).

---

## P3. Boss says "继续" or "继续推动" or "继续推送" = execute the next pipeline step

When boss types one of these (after a pause, after a question, etc.), they mean: **don't ask "what next?" — execute the next commit/push/build/deploy step immediately.**

If you just finished a `git commit`, run `git push` next. If you just finished a build, run the next test or commit. Don't ask "should I push now?" — push.

The user profile note: *"boss 期望不间断推进(3 次连续 block 后自动换 strategy)"* — pipeline blockers should be resolved by changing strategy, not by asking.

Examples:
- After a test suite passes → commit + push (don't ask "should I commit?")
- After a build succeeds → run the dev server / next test
- After a feature merge → start the next iteration
- After a memory note → keep working (don't pause for confirmation)

---

## P4. proposals.json is OBSOLETE in v5 — do not read it

The legacy `YeLuo45/proposals-manager/data/proposals.json` (or any local copy) is **no longer authoritative**. v5 source of truth is `~/.ai-superpower/proposals.csv` + the MCP server.

Reading proposals.json in v5 will return stale or inconsistent data. If you see a `useGitHub.js` or proposals.json read, that's a v4 leftover.

---

## P5. v4 state names are gone in v5

- `in_tdd_test` → removed (use `in_dev` for TDD work)
- `needs_revision` → removed (use `test_failed` to bounce back to dev)

`update_proposal_status` will reject both with "Invalid status transition" errors. Migrate any v4 code first.

---

## P6. `mergeProjects` and `scanDuplicates` MCP tools not in old mcp_aisp.py

`mcp_aisp.py` v5.0.0+ has 2 new tools added in 2026-06-10:
- `scan-duplicate-projects` (case_insensitive=true|false)
- `merge-projects` (target_id, source_id, delete_source=true|false)

If your `mcp_aisp.py` only has 18 tools (not 20), you have an older copy. Pull the latest from this skill's `scripts/mcp_aisp.py` (or run `mcp_aisp.py --list` to confirm).

---

## P7. PowerShell bootstrap.ps1: 3 known bugs

When installing via `superpower-clockless/bootstrap.ps1`:

1. `2>nul 1>nul` → `2>&1 | Out-Null` (PS5.x FileStream error)
2. `-ErrorAction SilentlyContinue` → remove (passed to git as unknown switch)
3. Prompt text `Edit` and `.venv` → `notepad` and `.\venv` (typo fixes)

All 3 are fixed in `superpower-clockless` v0.2.0+. If you hit them, you're on an old bootstrap. See `automation/superpower-clockless/SKILL.md`.

---

## See also

- `references/mcp-aisp-cli.md` — full CLI reference (20 tools)
- `references/mcp-vs-rest-migration.md` — v4→v5 state name + endpoint mapping
- `references/duplicate-project-workflow.md` — exact-name-match + dedup workflow
- `references/multi-agent-variant.md` — pattern for building ma-* variants
- `automation/superpower-clockless/SKILL.md` — bootstrap installer pitfalls
