---
name: prj-proposals-manager
description: Manage the complete proposal lifecycle from intake to delivery, coordinating multiple Agents or roles (Coordinator / PM / Dev / Test Expert / Research Analyst). Covers intake, clarification, PRD confirmation, technical review, test case generation, development handoff, acceptance, and delivery. Platform-agnostic (works with Cursor, Hermes, OpenClaw, etc.)
version: 4.4.0
author: YeLuo45
license: MIT
metadata:
  hermes:
    tags: [proposal, workflow, lifecycle, project-management, api]
    homepage: https://yeluo45.github.io/prj-proposals-manager/
    related_skills: [ai-superpower-iteration-workflow, harness-desktop-iteration-workflow, dbg-card-game-workflow, pixel-pal-web-workflow]
---

# Proposal Management

A platform-agnostic skill for managing proposal lifecycle across multi-role workflows (Coordinator / PM / Dev / Test Expert / Research Analyst). Covers intake, clarification, PRD confirmation, technical review, test case generation, development handoff, acceptance, and delivery.

## ⚠️ Core Rule
**All project/proposal data operations MUST go through the superpower-clockless MCP bridge (tools below). Direct CSV access is prohibited.**

**MCP Tools** (exposed by `superpower-clockless mcp`):
| Tool | Purpose |
|------|---------|
| `health` | Check ai-superpower server health |
| `project_list` | List projects (search, page_size) |
| `project_get` | Get project by ID |
| `proposal_list` | List proposals (project_id, search, page_size) |
| `proposal_get` | Get proposal by ID |
| `proposal_create` | Create proposal (title, owner, project_id, stage) |
| `proposal_update_fields` | Update proposal fields (proposal_id, fields) |
| `proposal_update_status` | Transition proposal status through state machine (proposal_id, status) |

> **⚠️ No direct API access**: Do NOT use `curl`, `requests`, or `urllib` to call ai-superpower. Always use MCP tools above.
> **MCP tool syntax**: Tools accept JSON objects as arguments, e.g. `{"name": "proposal_create", "arguments": {"title": "...", "owner": "...", "project_id": "...", "stage": "approved_for_dev"}}`
> **Stage values at creation**: Only `stage: "approved_for_dev"` is accepted at creation time. Values like `intake`, `clarifying`, `prd_pending_confirmation` return `422 Unprocessable Entity`.
> **Field updates**: Use `proposal_update_fields` for fields (tech_expectations, notes, etc.), NOT PUT/PATCH.
> **Status transitions**: Use `proposal_update_status` for state machine transitions — follow `intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev`.

---

## Proposal Lifecycle State Machine
```
intake → clarifying → prd_pending_confirmation → approved_for_dev
                                                       ↓
             in_tdd_test ←────────────────────── in_dev
                  ↓                                   ↓
         in_test_acceptance ←──────────────── needs_revision
                ↓      ↓
          accepted   test_failed
              ↓
          deployed → delivered
```

## Stage Definitions

| Stage | Owner | Description |
|-------|-------|-------------|
| `intake` | Coordinator | Proposal created after boss raises a request |
| `clarifying` | Coordinator | Clarifying questions, max 3 rounds |
| `prd_pending_confirmation` | PM | PRD draft ready, waiting for boss confirmation |
| `approved_for_dev` | Coordinator | Boss confirmed, assigning dev |
| `in_dev` | Dev | Development in progress |
| `needs_revision` | Dev | Test acceptance failed — Dev revises based on feedback |
| `in_tdd_test` | Dev | TDD test phase |
| `in_test_acceptance` | Coordinator | Test acceptance review |
| `test_failed` | Coordinator | Test did not pass |
| `accepted` | Coordinator | Acceptance passed |
| `deployed` | Coordinator | Deployed to production |
| `delivered` | Coordinator | Delivered to boss |

---

## Lifecycle Hooks

Each lifecycle node can trigger pre/post hooks for automation, logging, or side effects. Hooks are defined in `proposal.notes` field (JSON) or via environment config.

### Hook Trigger Points

| Stage | Pre-Hook | Post-Hook | Available Variables |
|-------|----------|-----------|-------------------|
| `intake` | `on_intake_pre` | `on_intake_post` | `proposal_id`, `title`, `owner` |
| `clarifying` | `on_clarifying_pre` | `on_clarifying_post` | `proposal_id`, `round` |
| `prd_pending_confirmation` | `on_prd_pre` | `on_prd_post` | `proposal_id`, `prd_path` |
| `approved_for_dev` | `on_approved_pre` | `on_approved_post` | `proposal_id`, `project_id` |
| `in_dev` | `on_dev_pre` | `on_dev_post` | `proposal_id`, `project_path` |
| `in_tdd_test` | `on_tdd_pre` | `on_tdd_post` | `proposal_id`, `test_cases_path` |
| `in_test_acceptance` | `on_acceptance_pre` | `on_acceptance_post` | `proposal_id`, `test_results` |
| `test_failed` | — | `on_test_failed_post` | `proposal_id`, `failure_reasons` |
| `accepted` | — | `on_accepted_post` | `proposal_id`, `deployment_url` |
| `deployed` | — | `on_deployed_post` | `proposal_id`, `deployment_url` |
| `delivered` | — | `on_delivered_post` | `proposal_id`, `delivered_at` |

### Defining Hooks in Proposal Notes

```json
{
  "hooks": {
    "on_intake_pre": "echo 'Intake started for P-YYYYMMDD-XXX' >> /tmp/lifecycle.log",
    "on_approved_post": "/usr/local/bin/notify-slack.sh",
    "on_deployed_post": "curl -X POST https://hooks.example.com/deploy $DEPLOYMENT_URL"
  }
}
```

### Hook Execution Rules
- **Execution**: Coordinator executes hooks synchronously (blocking) before/after each transition
- **Failure handling**: If pre-hook fails, block transition and report error. If post-hook fails, log error but allow transition to proceed
- **Unattended mode**: Post-hooks run automatically; pre-hooks that would block use 30s timeout then skip
- **No hooks defined**: Skip hook execution silently (no error)
- **Variables**: Available in hook shell context as exported vars (`$proposal_id`, `$project_id`, etc.)

---

## Architecture Refactor Trigger

After N completed iteration proposals under the same project (default: 6, configurable via `AI_SUPERPOWER_REFACTOR_ITERATIONS` env var), the project enters **mandatory architecture refactor phase**. Dev is handed off with an explicit "Architect" mandate instead of regular feature development.

**Configuration:**
```bash
export AI_SUPERPOWER_REFACTOR_ITERATIONS=6  # default 6, set to any positive integer; 0 disables
```

**Trigger detection:**
- Coordinator counts all proposals under the project with `stage: accepted` or `stage: deployed`
- When count % `AI_SUPERPOWER_REFACTOR_ITERATIONS` == 0, Coordinator sets `needs_revision` with refactor mandate
- Coordinator records in proposal notes: `"refactor_mandate": true`, `"refactor_count": <N>`

**Architect handoff requirements (Architect mandate):**
1. Full code audit: identify coupling, debt, performance bottlenecks, security surface
2. Produce `ARCHITECTURE.md` — module decomposition, data flow, technology choices with rationale
3. Produce `REFACTOR.md` — prioritized action items with estimated effort
4. All refactoring commits must pass existing test suite before merging
5. No new features during refactor phase — scope freeze

**Exit condition:** Refactor phase ends when Architect submits `ARCHITECTURE.md` + `REFACTOR.md` AND all existing tests pass. Coordinator transitions back to normal `in_dev` flow.

**Project repo reference:** https://github.com/YeLuo45/superpowers

---

## Operation Modes

### Default Mode (Interactive)

When user confirmation is needed, present A/B/C/D options and wait for single-letter reply:
- Options in brackets: `[A] Option A  [B] Option B  [C] Option C  [D] Continue`
- User replies with a single letter (case-insensitive)
- Timeout triggers first option as default

### Unattended Mode (Fully Automated)

For continuous iteration when no user is present. Enabled when requester/boss specifies "unattended" or "auto" when submitting a proposal.

**How to enter:**
- Boss/requester declares intent: "I want to run this project in unattended mode" or "run in unattended mode"
- Record as `mode: unattended` in the proposal's `notes` field
- Once entered, all subsequent iterations automatically stay in unattended mode

**Characteristics:**
- Always auto-selects first option (default)
- Does not wait for user input
- Delivery always includes A/B/C/D iteration options to ensure continuity
- Never stuck at confirmation gates
- Unattended mode persists across iterations — once set, stays active until boss explicitly exits

**Pass-through rules:**
- When creating a new iteration proposal under an unattended project, inherit unattended mode
- Do not clear unattended mode after delivery — continue iterating until boss explicitly exits

**Trigger timing:**
- On delivery: always provide A/B/C/D iteration options, auto-select first
- PRD/Technical expectation confirmation: auto-approve and continue after 5 min timeout
- No clarification questions in unattended mode

---

## PM Role: UI Design Professional Capabilities

When acting as PM, the Coordinator also fulfills UI Designer responsibilities. PM design capabilities are activated automatically when drafting PRD for visual/UI projects (e.g., web apps, mobile apps, interactive games).

### Design Tool Access
PM uses these professional design tools:
- **open-design** — open-design.io collaborative design platform (primary)
- **Figma** — when Open Design unavailable
- **Excalidraw** — for architecture diagrams and rapid prototyping
- **Canva** — for marketing/landing page mockups

### Built-in Design System References

PM defaults to these industry-leading design systems:

| Design System |适用场景 | Key Specifications |
|---|---|---|
| **Apple macOS / iOS** | 桌面/移动原生感 | SF Pro 字体, 8pt grid, 动态字体, 毛玻璃效果, 41pt 触控目标 |
| **Material Design 3** | Android 应用 / Material 组件库 | M3 组件, 4dp baseline, 色相系统, 动态配色 |
| **Fluent Design** | Windows 应用 | acrylic/云母背景, 9pt grid, reveal highlight |
| **Human Interface Guidelines (HIG)** | Apple 平台全品类 | 隐私/完整性/美学三大原则, 栏位结构, 手势导航 |
| **Ant Design** | 企业中台 / React 技术栈 | 4px spacing, 24-column grid, 40+原子组件 |
| **Carbon Design** | B端数据密集型应用 | IBM Carbon, 2x grid, 暗黑主题优先 |

### Design Review Checklist (Per PRD)
When drafting UI-related PRD, PM must cover:
1. **Layout**: Grid system, responsive breakpoints, safe area
2. **Typography**: Font family, scale (type ramp), line height
3. **Color**: Brand palette, semantic colors (success/error/warning), contrast ratio ≥ 4.5:1
4. **Components**: Core UI elements, states (default/hover/active/disabled), variant
5. **Accessibility**: Keyboard navigation, screen reader, focus order, ARIA labels
6. **Animation**: Transitions, micro-interactions, duration/curve

---

## Workflow: Proposal Lifecycle

```
Step 1a/1b: Intake -- Register proposal (from existing repo or new)
Step 2: Clarify -- Max 3 rounds of clarification
Step 3: Transfer to PM if needed
Step 4: PRD confirmation gate
Step 5: Technical expectations gate (max 3 rounds)
Step 6: Output technical solution
Step 6b: Handoff to Test Expert -- Generate TDD test cases
Step 7: Handoff to Dev (with test cases as reference)
Step 8: Test Expert acceptance based on test cases
Step 9: Delivery or revision
Step 10: Research direction (post-acceptance iteration planning)
Step 11: Deployment (post-acceptance delivery)
```

### Step 1a: Register from Existing Repo

When the request is to clone an existing GitHub repo and register as a proposal (vs. building from scratch):

1. Clone repo to `$superpower-dev/<project-name>/proposals/` or local copy
2. For design-doc projects (`*-design`), treat as normal proposal per Step 1b

### Step 1b: Register New Proposal from Scratch

1. Create project via ai-superpower CLI (if not exists):
   ```bash
   ai-superpower project create --name "ProjectName" --git-repo "https://github.com/owner/repo"
   ```
2. Create proposal via MCP tool `proposal_create` (ID auto-generated, no manual management)
3. Create gh-pages branch for the proposal (if project has remote repo):
   ```bash
   cd $DEV_PROPOSALS/<project-name>
   git checkout -b gh-pages
   ```
4. Copy `$TEMPLATES_DIR/request-intake-template.md` to proposal directory
5. Fill in basic info and original request
6. Create proposal via MCP tool `proposal_create`:
   ```
   Tool: proposal_create
   Arguments: {"title": "ProposalTitle", "owner": "coordinator", "project_id": "PRJ-YYYYMMDD-XXX", "stage": "approved_for_dev"}
   ```

### Step 2: Clarify Requirements

- Max 3 rounds of clarifying questions, focused on: goals, scope, constraints, acceptance criteria
- Record each Q&A round in the proposal's "Clarification" section
- After 3 rounds or when requirements are clear, record final assumptions
- Transition status via MCP tool `proposal_update_status`:
  ```
  Tool: proposal_update_status
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "clarifying"}
  ```

### Step 3: Transfer to PM

If the request is just an idea or rough draft, transfer to PM role to generate PRD.

- PM saves PRD to `$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md`
- PM also copies PRD to `$DEV_PROPOSALS/<project-name>/docs/prd.v1.md`
- Update PRD path via MCP tool `proposal_update_fields`:
  ```
  Tool: proposal_update_fields
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"prd_path": "$PM_PROPOSALS/PRJ-YYYYMMDD-XXX/YYYY-MM-DD-prd.md"}}
  ```

### Step 4: PRD Confirmation Gate

After PM returns PRD:

1. Present PRD to requester and request confirmation
2. Start confirmation countdown (recommend: 5 minutes)
3. Record countdown reference in "PRD Confirmation Countdown ID"

If confirmed: set PRD Confirmation to `confirmed`, cancel countdown, immediately transition to `approved_for_dev` and start development.
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "approved_for_dev"}
```

If timeout: set PRD Confirmation to `timeout-approved`, record in "Timeout Resolution", immediately transition to `approved_for_dev` and start development.

### Step 5: Technical Expectations Gate

Before outputting technical solution:

1. Understand from requester: tech stack, performance, cost, deployment method, maintainability, dependency constraints
2. Up to 3 rounds of questions
3. Start confirmation countdown (same mechanism as Step 4)
4. Record in "Technical Expectations Countdown ID"

If confirmed: set Technical Expectations to `confirmed`, write technical solution and transition to `approved_for_dev`.

If timeout: set Technical Expectations to `timeout-approved`, proceed with current assumptions, write technical solution and transition to `approved_for_dev`.

**⚠️ Timeout cron firing on proposal with missing index entry:** If the cron job fires but `proposal-index.md` has no entry for that proposal (yet `proposals.json` has the proposal), do NOT manually edit the index. Follow the recovery path in `references/proposal-index-missing-entry.md`:
1. Verify the proposal exists in `proposals.json` via `grep -n "P-YYYYMMDD-XXX" /home/hermes/proposals/proposals.json`
2. Run `sync-proposals-to-website.py` to reconcile the index
3. Only after the entry appears in the index should you attempt field updates
4. The correct status transition is still done via ai-superpower API — the index is derived, not the source of truth

### Step 6: Technical Solution

- Output to `$superpower-root/P-YYYYMMDD-XXX-tech-solution.md`
- Also copy to `$DEV_PROPOSALS/<project-name>/docs/technical-solution.v1.md`
- Update via MCP tool `proposal_update_fields`:
  ```
  Tool: proposal_update_fields
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"tech_solution_path": "$superpower-root/P-YYYYMMDD-XXX-tech-solution.md"}}
  ```

### Step 6b: TDD Test Case Generation

After technical solution output, transfer to Test Expert to generate test cases based on TDD principles:

1. Coordinator hands off to Test Expert with: PRD doc, technical solution doc, project background

2. Test Expert outputs to `$superpower-test/<project-name>/YYYY-MM-DD-test-cases.md`
   - Test cases must be traceable to PRD requirements
   - Include: test case ID, description, preconditions, steps, expected results
   - Cover normal paths and edge cases
   - Copy to `$superpower-dev/<project-name>/proposals/docs/test-cases.v1.md`

3. **UI Testing Enhancement (from GitHub Intelligence)**
   - Search GitHub for existing test patterns in the project's tech stack (e.g., `playwright react testing`, `selenium e2e`, `testing-library best practices`)
   - Identify top 5 UI testing repositories with 500+ stars for the same framework
   - Extract test structure, page object patterns, and coverage strategies
   - For UI-heavy projects, add mandatory UI test cases from GitHub examples:
     - Visual regression tests (snapshot or pixel-diff)
     - Responsive layout tests (mobile/tablet/desktop breakpoints)
     - Accessibility tests (axe-core, keyboard navigation, screen reader)
     - Loading state / skeleton / error boundary tests
     - Interaction tests: hover, focus, keyboard, touch, drag-drop

4. Transition status via MCP tool `proposal_update_status`:
   ```
   Tool: proposal_update_status
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_tdd_test"}
   ```

### Step 7: Handoff to Dev

Transition status via MCP tool `proposal_update_status`:
  ```
  Tool: proposal_update_status
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_dev"}
  ```
- Update project_path via MCP tool `proposal_update_fields`:
  ```
  Tool: proposal_update_fields
  Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"project_path": "$DEV_PROPOSALS/<project-name>"}}
  ```
- If directory doesn't exist, Dev creates `$DEV_PROPOSALS/<project-name>/docs/`

### Step 8: Test Expert Acceptance (Based on TDD)

After Dev reports completion, Test Expert performs acceptance based on test cases:

Requirements consistency:
- Matches requester-confirmed requirements
- Aligned with PRD
- No scope creep or cutting corners

Test case execution:
- Execute each test case in `test-cases.vN.md`
- Record pass/fail status for each
- Record any deviations or failures

Functional verification (must实际操作, not just screenshots):
- Core features work end-to-end
- Console/logs have no Error (warnings acceptable)
- Existing features not broken
- Build succeeds

Transition status via MCP tool `proposal_update_status`:
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_test_acceptance"}
```

If all test cases pass: proceed to Step 9 (delivery)

If any test case fails: transition to `test_failed`, output structured revision feedback:
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "test_failed"}
```

### Step 9: Delivery or Revision

**Before transitioning to `accepted`, Test Expert must complete post-acceptance documentation:**

1. **Update README**: Ensure project README reflects the latest deliverable:
   - Update version number (if versioned)
   - Update feature list / changelog
   - Update deployment instructions if deployment target changed
   - Update screenshots/demo links if UI changed

2. **Update SPEC**: Sync `SPEC.md` (or `SPEC.vN.md`) with accepted implementation:
   - Mark all implemented requirements as `DONE`
   - Add implementation notes for any deviations from original spec
   - Update architecture diagrams if system structure changed
   - Record any new constraints or technical decisions

3. After README + SPEC update, transition to `accepted`:
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "accepted"}
```

If acceptance fails: transition to `needs_revision`, output structured revision feedback:
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "needs_revision"}
```

### Step 10: Research Direction (Post-Acceptance Iteration Planning)

After acceptance passes (status becomes `accepted` or `delivered`):

1. Coordinator asks requester: "Based on this delivery, do you want to explore the next iteration direction, or maintain the current version?"
2. Start 5-minute confirmation countdown, create cron job
3. Record countdown reference in "Research Direction Countdown ID"

If confirmed: set Research Direction to `confirmed`, immediately transfer to PM for next iteration PRD.

If timeout: set Research Direction to `timeout-approved`, Coordinator decides independently, immediately transfer to PM for next iteration PRD.

#### Research Extension: Online Search + GitHub Intelligence

When researching iteration directions, Coordinator automatically enriches with external sources beyond user input:

**Step 10a: User-Provided Directions**
- Record all directions explicitly mentioned by requester
- These are primary — external sources supplement, not replace

**Step 10b: Online Search Expansion**
- Search web for relevant technology trends, competitor features, emerging patterns
- Search target: product category keywords + "best practices", "2024 2025 trends", "design patterns"
- Use `web` toolset for search

**Step 10c: GitHub Intelligence**
- Query GitHub Trending for the project's tech stack (language/framework)
- Identify top 10 open-source projects in the same domain
- For each trending repo: note stars, recent commits, README highlights, architecture patterns
- Filter for projects with: 100+ stars, activity in last 6 months, permissive license (MIT/Apache2)

**Step 10d: Synthesize Research**
- Combine user directions + web findings + GitHub intelligence
- Rank by relevance to current project
- Present top candidates as iteration options (A/B/C/D/E format)
- In unattended mode: auto-select first option after 5 min

**Research Sources Priority:**
| Source | Use When |
|--------|----------|
| Requester-provided | Always (required input) |
| Web search (web tool) | UI/UX improvements, new features |
| GitHub Trending | Tech stack validation, architecture inspiration |
| GitHub Top10 repos | Feature parity check, differentiation opportunities |

**GitHub Trending Query Example:**
```bash
# Query GitHub trending for React projects in past week
# Use web search: "site:github.com/trending react since:2025-01-01"
# Filter results for 1000+ stars, recent activity
```

### Step 11: Deployment (Post-Acceptance Delivery)

After acceptance passes (status becomes `accepted`):

1. Determine deployment target from project config or environment variable `AI_SUPERPOWER_DEPLOY_TARGET`
2. Create deployment branch
3. Prepare deployment (ensure package-lock.json is committed, run `npm run build`)
4. Push to remote
5. Trigger deployment via target-specific method (see Deployment Targets below)
6. Update proposal: transition to `deployed`, record Deployment URL:
   ```
   Tool: proposal_update_status
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "deployed"}
   Tool: proposal_update_fields
   Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"deployment_url": "https://..."}}
   ```

#### Deployment Targets

| Target | Environment Config | Deploy Method |
|--------|------------------|---------------|
| **GitHub Pages** | `AI_SUPERPOWER_DEPLOY_TARGET=github-pages` | Push to `gh-pages` branch, GitHub Actions auto-deploy |
| **Cloudflare Pages** | `AI_SUPERPOWER_DEPLOY_TARGET=cloudflare-pages` | `wrangler pages deploy` via Cloudflare Workers |
| **Aliyun OSS** | `AI_SUPERPOWER_DEPLOY_TARGET=aliyun-oss` | `ossutil` or Aliyun CLI upload; requires `ALIYUN_ACCESS_KEY_ID` + `ALIYUN_ACCESS_KEY_SECRET` + `ALIYUN_BUCKET` + `ALIYUN_REGION` |
| **AWS S3** | `AI_SUPERPOWER_DEPLOY_TARGET=aws-s3` | `aws s3 sync` to S3 bucket; requires `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_BUCKET` + `AWS_REGION` |
| **Vercel** | `AI_SUPERPOWER_DEPLOY_TARGET=vercel` | `vercel --prod`; requires `VERCEL_TOKEN` |
| **Netlify** | `AI_SUPERPOWER_DEPLOY_TARGET=netlify` | `netlify deploy --prod`; requires `NETLIFY_AUTH_TOKEN` + `NETLIFY_SITE_ID` |

**Adding new targets:** Add new row to the table above. Coordinator reads `AI_SUPERPOWER_DEPLOY_TARGET` env var. If value is unrecognized, Coordinator reports error and falls back to listing supported targets.

**Target-specific env vars (set on ai-superpower host):**
```bash
# Aliyun OSS
export ALIYUN_ACCESS_KEY_ID=...
export ALIYUN_ACCESS_KEY_SECRET=...
export ALIYUN_BUCKET=my-bucket
export ALIYUN_REGION=cn-hangzhou

# AWS S3
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_BUCKET=my-bucket
export AWS_REGION=us-east-1
```

---

## MCP Tool Reference

All operations use `superpower-clockless mcp` tools, invoked via the MCP bridge. Below is the complete tool schema reference.

> **Full MCP tool documentation**: run `superpower-clockless mcp-info` to inspect tool names and schemas without starting the stdio loop.

### Tool: health
Check ai-superpower server health. No arguments.
```
Tool: health
```

### Tool: project_list
List projects with optional search filter and pagination.
```
Tool: project_list
Arguments: {"search": "keyword", "page_size": 50}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | string | No | Filter by project name/keyword |
| `page_size` | integer | No | Results per page (default 50, max 200) |

### Tool: project_get
Get a single project by ID.
```
Tool: project_get
Arguments: {"project_id": "PRJ-YYYYMMDD-XXX"}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | Yes | Project ID |

### Tool: proposal_list
List proposals with optional filters.
```
Tool: proposal_list
Arguments: {"project_id": "PRJ-YYYYMMDD-XXX", "search": "keyword", "page_size": 50}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | No | Filter by project |
| `search` | string | No | Filter by title/keyword |
| `page_size` | integer | No | Results per page (default 50, max 200) |

### Tool: proposal_get
Get a single proposal by ID.
```
Tool: proposal_get
Arguments: {"proposal_id": "P-YYYYMMDD-XXX"}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `proposal_id` | string | Yes | Proposal ID |

### Tool: proposal_create
Create a new proposal. Only `stage: "approved_for_dev"` is accepted at creation time.
```
Tool: proposal_create
Arguments: {"title": "My Proposal", "owner": "coordinator", "project_id": "PRJ-YYYYMMDD-XXX", "stage": "approved_for_dev"}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Proposal title |
| `owner` | string | Yes | Owner name |
| `project_id` | string | Yes | Project ID |
| `stage` | string | Yes | Must be `"approved_for_dev"` |

### Tool: proposal_update_fields
Update proposal fields (tech_expectations, notes, prd_path, tech_solution_path, project_path, deployment_url, etc.).
```
Tool: proposal_update_fields
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "fields": {"tech_expectations": "confirmed", "notes": "iteration notes"}}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `proposal_id` | string | Yes | Proposal ID |
| `fields` | object | Yes | Key-value pairs of fields to update |

### Tool: proposal_update_status
Transition proposal status through the state machine. Follows strict transitions: `intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev → in_tdd_test → in_test_acceptance → accepted → deployed → delivered`. Also: `in_dev → needs_revision → in_dev`, `in_test_acceptance → test_failed → in_dev`.
```
Tool: proposal_update_status
Arguments: {"proposal_id": "P-YYYYMMDD-XXX", "status": "in_dev"}
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `proposal_id` | string | Yes | Proposal ID |
| `status` | string | Yes | Target status |

### Example: Create project and proposal (MCP chain)
```
# 1. Create project
Tool: project_create  # Note: via ai-superpower CLI, not MCP
CLI: ai-superpower project create --name "MyProject" --git-repo "https://github.com/owner/repo"

# 2. List projects to get project_id
Tool: project_list
Arguments: {"search": "MyProject"}

# 3. Create proposal
Tool: proposal_create
Arguments: {"title": "Feature A", "owner": "coordinator", "project_id": "PRJ-YYYYMMDD-XXX", "stage": "approved_for_dev"}

# 4. Get the new proposal to confirm ID
Tool: proposal_list
Arguments: {"project_id": "PRJ-YYYYMMDD-XXX", "search": "Feature A"}
```

### Server Down Recovery
If MCP tools return connection errors:
```bash
# Check if superpower-clockless can reach the server
superpower-clockless doctor

# Check ai-superpower process
ps aux | grep -E 'uvicorn|fastapi' | grep -v grep

# Check ports
ss -tlnp | grep -E '8000|8001'
```

### Audit Log (via MCP)
```python
# Audit log is accessible through the ai-superpower REST API directly when needed for recovery
# Use MCP tool proposal_get to retrieve full proposal state
```

---

## Development Delivery Quality Checks

Before acceptance, must verify three hard criteria:

1. Build exit code: must be 0
2. Output directory non-empty: list core files to confirm
3. Core source/service files exist: verify critical files present

### Takeover Triggers

Coordinator should take over directly if any condition is met:
- Dev fails delivery 2 consecutive times
- Dev session interrupted by API/quota error
- Dev session abnormally short (<30s) yet claims completion
- Fix method is simple and clear

### Fix Recording

When Coordinator fixes directly, record to:
1. Project memory file (e.g. `MEMORY.md`) relevant section
2. Daily log (e.g. `memory/YYYY-MM-DD.md`)
3. Proposal's Notes or Main Fixes Applied field

---

## Backup and Rollback

### Auto-Backup (Automatic Proposal Backup)

ai-superpower internally tracks the cumulative count of proposals created. After every N proposals (default: 5, configurable via `AI_SUPERPOWER_BACKUP_INTERVAL` env var), the system automatically triggers a backup before the workflow can proceed past the `intake` → `clarifying` transition gate.

**Coordinator role — no manual backup execution needed:**

The Coordinator does NOT run backup scripts. It only:
1. Reads `last_backup` from proposal notes to confirm backup has run
2. If `last_backup` is absent and counter threshold is met, reports "Backup pending — please ensure ai-superpower auto-backup is active"
3. Records backup confirmation in the proposal audit trail

**Configuration (set on ai-superpower host):**
```bash
export AI_SUPERPOWER_BACKUP_INTERVAL=5  # default 5, set to any positive integer; 0 disables
```

**If backup interval env var is 0 or not set**: auto-backup is disabled (manual backup only).

### Manual Backup

```bash
source ~/.superpower-clockless/env  # Unix
# or: .\.\superpower-clockless\env.bat  # Windows
bash scripts/backup_proposals.sh
```

**Data source MUST be ai-superpower API — direct CSV read is prohibited.** `backup_proposals.sh` calls `backup_api.py` which paginates `/api/projects` and `/api/proposals` and converts JSON to CSV.

> **API endpoint gotchas**:
> - Path is `/api/{entity}`, NOT `/api/v1/{entity}` (the v1 prefix does NOT exist)
> - `page_size` max is 200 — passing 1000 returns HTTP 422
> - Paginate with `page=1`, `page=2`, ... until `len(items) >= total`

Backups stored at: `superpower-backups/backup_YYYYMMDD_HHMMSS/`

### Rollback

```bash
# List available backups
bash scripts/rollback_proposals.sh list

# Verify backup integrity
bash scripts/rollback_proposals.sh verify proposals_backup_YYYYMMDD_HHMMSS.tar.gz

# Full system rollback (to latest backup)
bash scripts/rollback_proposals.sh full

# Full system rollback to specific backup (N=1 is latest, N=2 is second latest)
bash scripts/rollback_proposals.sh full 3

# Rollback specific project
bash scripts/rollback_proposals.sh project PRJ-YYYYMMDD-XXX

# Rollback specific proposal
bash scripts/rollback_proposals.sh proposal P-YYYYMMDD-XXX
```

### Rollback Behavior

| Command | Data Restored |
|---------|---------------|
| `full N` | All CSV + markdown files in backup N |
| `project <id> N` | projects.csv entry + related proposals + mappings |
| `proposal <id> N` | Single proposal in proposals.csv + mappings |

**Safety measures:**
- Full system rollback: create emergency backup of current state first
- Project/proposal rollback: create emergency backup first
- All operations require `yes` confirmation

---

## Environment Variables

|| Variable | Description |
||----------|-------------|
|| `AI_SUPERPOWER_API_KEY` | API key (written by `superpower-clockless install` to `~/.superpower-clockless/env`; source it with `source ~/.superpower-clockless/env` on Unix or `.\.superpower-clockless\env.bat` on Windows) |
|| `AI_SUPERPOWER_URL` | API base URL, defaults to `http://127.0.0.1:8000` |

---

## Configuration

| Variable | Value | Description |
|----------|-------|-------------|
| superpower-root | `/home/hermes/proposals` | Root directory for all agent files |
| superpower-dev | `{superpower-root}/workspace-dev/<project>/proposals` | Dev workspace |
| superpower-pm | `{superpower-root}/workspace-pm/<project>/proposals` | PM workspace |
| superpower-test | `{superpower-root}/workspace-test/<project>/proposals` | Test workspace |
| superpower-research | `{superpower-root}/workspace-research/<project>/proposals` | Research workspace |
| superpower-proposals | `{superpower-root}/workspace-proposals/<project>` | Proposals (main index) workspace |
| superpower-backups | `{superpower-root}/backups` | Backup storage directory |

---

## Workspace Initialization

When creating a project with `--init-workspace`, the script creates:

```
workspace-dev/<project>/proposals/
workspace-dev/<project>/proposals/docs/index.md

workspace-pm/<project>/proposals/
workspace-pm/<project>/proposals/docs/index.md

workspace-test/<project>/proposals/
workspace-test/<project>/proposals/docs/index.md

workspace-research/<project>/proposals/
workspace-research/<project>/proposals/docs/index.md
```

Each `docs/index.md` contains a version tracking table for Proposal, PRD, Technical Solution, and Test Cases.

### Post-Acceptance: Sync PRD/Technical Solution to Dev Workspace

After proposal acceptance, sync PRD and technical solution files to `workspace-dev/proposals/` under the corresponding project directory, ensuring the project syncs to remote repo with these documents:

```bash
python3 scripts/sync-pm-to-dev.py <project_id> [--dry-run]

# Examples
python3 scripts/sync-pm-to-dev.py PRJ-20260422-001          # sync ai-novel-assistant
python3 scripts/sync-pm-to-dev.py PRJ-20260516-001 --dry-run  # preview only
```

Files from: `workspace-pm/proposals/{project_id}/` → `workspace-dev/proposals/{project_name}/`

Test case files (filenames containing `test`, `spec`, `test-case` in .md files) are also synced.

### Post-Acceptance: Generate OpenSpec SPEC

After proposal acceptance, generate OpenSpec spec files based on PRD and technical solution:

```bash
python3 scripts/generate-spec.py <project_id> [--dry-run]

# Examples
python3 scripts/generate-spec.py PRJ-20260422-001          # generate SPEC for ai-novel-assistant
python3 scripts/generate-spec.py PRJ-20260516-001 --dry-run  # preview only
```

Reads PRD and technical solution from `workspace-pm/proposals/{project_id}/`, generates:

```
workspace-dev/proposals/{project_name}/SPEC/
├── proposal.md        # Why/What/Capabilities/Impact (from PRD)
├── spec.md           # Requirements + GHERKIN scenarios
├── design.md         # Context/Goals/Decisions/Risks (from technical solution)
├── tasks.md          # Implementation checklist
└── .openspec.yaml    # Metadata (schema, project, creation date)
```

OpenSpec reference: https://github.com/YeLuo45/OpenSpec（schemas/spec-driven/templates/）

### Initialize SPEC for Existing Projects

Initialize OpenSpec SPEC for projects without proposals (legacy projects) from existing project files:

```bash
# Initialize SPEC for single project (by project name)
python3 scripts/generate-spec.py --init <project_name>
python3 scripts/generate-spec.py --init todolist                      # by name
python3 scripts/generate-spec.py --init ai-stock-simulation --name "AlphaTrader"  # with display name

# Initialize SPEC for all projects without SPEC
python3 scripts/generate-spec.py --init --all
python3 scripts/generate-spec.py --init --all --dry-run               # preview only
```

Read sources:
- `workspace-dev/proposals/{project_name}/README.md` (project description, features, tech stack)
- `workspace-dev/proposals/{project_name}/SPEC.md` (if exists)
- Template content when no source available

---

## Bug Prevention

| Issue | Prevention |
|-------|------------|
| SOUL.md / MEMORY.md conflicts after skill sync | When syncing prj-proposals-manager to a profile directory (e.g. rsync to `profiles/onepc/skills/`), the profile's SOUL.md may contain rule definitions that predate the skill spec and directly conflict with it (e.g. "write CSV first" vs API-mandate, or truncated state machines). Always check the profile's SOUL.md after syncing and align it to the skill spec — do not assume the sync alone makes the profile consistent. |
| Duplicate IDs | API auto-generates unique IDs, no manual management |
| CSV field misalignment | API enforces 20-field schema, no misalignment |
| Direct CSV tampering | API writes logged to audit log, fully auditable |
| Concurrent writes | FastAPI + file lock ensures data consistency |
| ID range conflicts | API allocates per-project, isolated conflicts |
| Data loss | Audit log supports replay recovery |
| Missing index entry on timeout cron fire | Index is derived — always check `proposals.json` first. If the proposal already has correct fields in proposals.json, the task is already done; skip manual index edit. The index will be regenerated on next sync. |
| Cron task specifies `proposal-index.md` update but data is already in `proposals.json` | proposals.json is the data source. If a cron fires to "update proposal-index.md" but proposals.json already contains the correct values (as verified by reading lines around the proposal ID), the task is already done — skip writing to the index. The index will be regenerated on next sync. |
| `sync-proposals-to-website.py` may not exist | The skill references this script for index reconciliation, but it was not found in `scripts/`. Do NOT rely on it for ghost proposal recovery. Instead, directly edit `proposals.json` to update proposal fields. |
| Ghost proposal: API returns 404 but proposals.json has entry with minimal fields | Proposal is orphaned in the API but may have functional descendants. Diagnostic path: (1) Check proposals.json entry fields — if `title=""` and only `id/status/priority/created` fields, it's a ghost. (2) **If title is empty, edit proposals.json directly to restore the original title** (this is the one exception to the "never edit proposals.json" rule). (3) Search API by project_id+title keyword to find the live copy. (4) Do NOT POST a new proposal to replace the ghost — this orphans the original ID. (5) **If functional descendants exist (same tech stack/title in newer proposals), update the descendant through full state machine transition (`intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev`).** See `references/ghost-proposal-functional-descendant.md` for the complete recovery workflow including state machine stepping. |
| `proposals.json` is NOT a flat proposal list | Top-level key is `projects`; proposals are nested inside each project as `project['proposals']`. Attempting to iterate it as a flat list will fail. |
| `sync-proposals-to-website.py` may not exist | The skill references this script for index reconciliation, but it was not found in `scripts/`. Do NOT rely on it for ghost proposal recovery. Instead, directly edit `proposals.json` to update proposal fields. |
| `proposal-index-missing-entry.md` (reference in Bug Prevention) | That reference file may not exist on disk. When diagnosing a missing index entry: (1) verify proposal exists in `proposals.json` by reading lines around the ID, (2) directly edit `proposals.json` to update fields if needed — this is the correct recovery path, (3) do NOT attempt to run a missing sync script. The index is derived, not the source of truth. |
| `sync-proposals-to-website.py` may not exist | The skill references this script for index reconciliation, but it was not found in `scripts/`. Do NOT rely on it for ghost proposal recovery. Instead, directly edit `proposals.json` to update proposal fields. |
| Cron job fires but proposal not in proposal-index.md | This is expected if the proposal was never written to the index. The index is derived from `proposals.json`, not the authoritative source. Practical fix: (1) verify proposal exists and has correct fields in `proposals.json`, (2) update fields there directly, (3) no sync script needed. |
| proposals.json already has correct values but cron says to update index | proposals.json is the data source. If a cron fires to "update proposal-index.md" but proposals.json already contains the correct values (as verified by reading lines around the proposal ID), the task is already done — skip writing to the index. The index will be regenerated on next sync. |
| API returns 404 but proposals.json has correct data | API may return 404 for proposals that exist in proposals.json with all correct fields (status, tech_expectations, tech_stack, etc.). When this happens: (1) verify the JSON entry has correct values, (2) conclude the data-layer task is complete, (3) do NOT attempt API re-POST or manual index edit. The index is derived and will sync later. |
| proposal-index.md path for cron jobs | Cron jobs may reference `~/.hermes/proposals/proposal-index.md` which does not exist. The actual path is `/home/hermes/proposals/proposal-index.md`. When the target file is missing, verify `proposals.json` directly and skip index reconciliation. |
| Two proposals.json copies auto-sync | `/home/hermes/proposals/proposals.json` and `/home/hermes/.hermes/proposals/proposals/proposals.json` stay in sync. Editing either one updates both. This matters when diagnosing ghost state — check the right copy for the context you're working in. |
| API returns "Proposal not found" but JSON has it | Proposal likely migrated to new API format — search API by project_id+title to find the migrated copy. Do NOT POST a new proposal to replace it — this orphans the original ID and doubles proposal count. Use backup/rollback to restore if needed. |
| API `status` field won't transition to `in_dev` | The `status` field follows a strict state machine. Check if `stage` field is already `in_dev` — that may satisfy the intent. The `status` field may require going through valid transitions: `intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev`. |
| CSV `project_id` may differ from API `project_id` | CSV (proposals.csv) uses human-readable names like `todo-list` while the API uses formal IDs like `PRJ-20250416-001`. When creating proposals via CSV, use the CSV's project_id field value. When querying via API, use the API's project_id. Do NOT assume they are the same string. |

---

## References
## References

| File | Purpose |
|------|---------|
| `references/proposal-index-missing-entry.md` | Conceptual: diagnosing missing proposal-index.md entries when proposals.json has the proposal. File may not exist on disk — verify JSON directly and edit JSON for recovery. Index is derived, not authoritative. |
| `references/ghost-proposal-functional-descendant.md` | Ghost proposal recovery when API returns 404 but functional descendant exists — state machine stepping for descendant updates |
| `references/proposals-json-structure.md` | proposals.json nested structure — reading/writing project-centric JSON mirror, ghost proposal patterns |
| `references/api-json-divergence.md` | When `proposals.json` has an entry but API returns 404 — diagnosis and resolution |
| `references/deployed-site-debugging.md` | Debugging deployed sites when local code diverges — analyze minified JS, identify deployed commit, find matching source |
| `references/cli-api-data-source-divergence.md` | CLI vs API data source divergence — why CLI reports "No projects" while API works |
| `references/cron-proposal-sync-failures.md` | Cron fires for non-existent proposals — diagnosis & handling |
| `references/cron-timeout-proposal-index-missing.md` | Cron timeout fires but proposal missing from proposal-index.md — practical fix: edit proposals.json directly |
| `references/ai-superpower-architecture.md` | Anti-tamper architecture & how ai-superpower works |
| `references/ai-superpower-cli-quirks.md` | CLI argument rules (e.g. git_repo must be https://) |
| `references/api-quick-ref.md` | HTTP API quick reference (curl commands) |
| `references/api-python-urllib-quick-ref.md` | Python urllib patterns for ai-superpower API (preferred over curl) |
| `references/data-recovery.md` | Data recovery methods (via audit log) |
| `references/local-path-population.md` | Local path population logic |
| `references/github-repo-rename.md` | GitHub repo rename handling |
| `references/merge-proposals-dirs.md` | Merging proposal directories |
| `references/openspec-integration.md` | OpenSpec integration |
| `references/vite-cache-issue.md` | Vite cache issue handling |
| `references/favorites-system.md` | Favorites system architecture |
| `references/bash-pitfalls.md` | Common shell script pitfalls |

## Scripts

| File | Purpose |
|------|---------|
| `backup_proposals.sh` | Backup proposal system (API-based CSV export) |
| `backup_api.py` | Python helper: paginate ai-superpower API → CSV |
| `rollback_proposals.sh` | Rollback proposal system (full/project/proposal-level) |

## API status vs stage field divergence

The ai-superpower API has **two separate status fields**:
- `status`: Follows a strict state machine. Cannot transition arbitrarily (e.g., `intake → in_dev` is invalid).
- `stage`: Can be set independently and often defaults to `in_dev`.

When a cron job asks to set `Current Status: in_dev` but the API `status` field is stuck at `intake`:
1. Check if `stage` is already `in_dev` — if so, the intent is satisfied functionally
2. Do NOT force a state machine violation to make `status` equal `stage`
3. The `status` field may require going through valid transitions (`intake → clarifying → prd_pending_confirmation → approved_for_dev → in_dev`)

## Related Skills
- `ai-superpower-iteration-workflow` — ai-superpower own iteration workflow
- `harness-desktop-iteration-workflow` — Desktop project iteration
- `dbg-card-game-workflow` — DBG card game development
- `pixel-pal-web-workflow` — PixelPal Web development