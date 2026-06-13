# spec-kit Integration

spec-kit (`https://github.com/YeLuo45/spec-kit` — fork of `github/spec-kit`) is GitHub's Spec-Driven Development toolkit. The proposal system integrates spec-kit for **TDD-focused pre-OpenSpec states** that OpenSpec doesn't cover.

## Scope Split: spec-kit vs OpenSpec

| State | Tool | Output Location |
|-------|------|-----------------|
| Step 5/6 (Tech Solution) | spec-kit | `workspace-test/<project>/proposals/<PRJ>/spec-kit/{spec,plan,tasks}.md` |
| Step 6b (TDD Test Cases) | spec-kit | `workspace-test/<project>/proposals/<PRJ>/{test-cases,checklist}.md` |
| Step 7 (Handoff to Dev) | spec-kit | Tasks with TDD test tasks (Phase 3+ per US) |
| Step 8 (Test Acceptance) | spec-kit | `workspace-test/<project>/proposals/<PRJ>/{test-report,checklist-status}.md` |
| Step 9+ (Post-Acceptance) | **OpenSpec** | `workspace-dev/<project>/openspec/changes/<change>/{proposal,design,tasks,specs}/` |

spec-kit is the **TDD layer**; OpenSpec is the **specification layer** for delivered artifacts.

## spec-kit Templates Used (canonical from github/spec-kit)

| Template | Adapted File | TDD Focus |
|----------|--------------|-----------|
| `templates/spec-template.md` | `spec-kit/spec.md` | User Stories with Given/When/Then + Independent Test |
| `templates/plan-template.md` | `spec-kit/plan.md` | `**Testing**` field + `tests/{contract,integration,unit}/` structure |
| `templates/tasks-template.md` | `spec-kit/tasks.md` | "Tests for User Story N" subsections (TDD-first) |
| `templates/checklist-template.md` | `checklist.md` | "Unit tests for English" — req quality validation |
| `templates/constitution-template.md` | (out of scope, project-level) | Project principles (not per-proposal) |

## generate-tdd-spec.py — Three Modes

The `scripts/generate-tdd-spec.py` script (in this skill's scripts/) handles TDD outputs.

### Mode 1: Step 6b — Generate TDD Test Cases (default)

```bash
# Generate test-cases.md + checklist.md + Step 8 templates
python3 scripts/generate-tdd-spec.py PRJ-20260417-001
python3 scripts/generate-tdd-spec.py PRJ-20260417-001 --dry-run
```

**Input**: PRD from `workspace-pm/proposals/{project_id}/`

**Output** (in `workspace-test/<project>/proposals/<project_id>/`):
- `test-cases.md` — Structured TDD test cases (ID, US ref, Type, Preconditions, Steps, Expected, GHERKIN)
- `checklist.md` — Requirements quality checklist (CHK001-CHK014)
- `test-report.md` — Step 8 acceptance report template (Test Expert fills in)
- `checklist-status.md` — Step 8 pass/fail per CHK item template

### Mode 2: Steps 5/6/6b — Full spec-kit Generation (--full)

```bash
# Add spec-kit/{spec,plan,tasks}.md to Mode 1 output
python3 scripts/generate-tdd-spec.py PRJ-20260417-001 --full
```

**Additional output** (in `spec-kit/` subdirectory):
- `spec-kit/spec.md` — User stories with priority + Given/When/Then acceptance scenarios
- `spec-kit/plan.md` — Tech plan with `**Testing**` field + `tests/{contract,integration,unit}/` structure
- `spec-kit/tasks.md` — Phase-organized tasks (Setup / Foundational / US1-P1 / US2-P2 / Polish) with **TDD tests-first** subsections

### Mode 3: Step 8 — Render Test Report (--report)

```bash
# Render test-report.md from a JSON file of test results
python3 scripts/generate-tdd-spec.py PRJ-20260417-001 --report results.json
```

**Input**: `--report results.json` is a JSON list of `{"id": "TC-...", "status": "pass|fail|skip", "duration_ms": N, "message": "..."}`

**Output**: `test-report.md` filled in with pass/fail counts, verdict, and failure analysis. Updates `checklist-status.md` similarly.

## TDD Methodology (per spec-kit)

spec-kit's core TDD principle: **tests are written BEFORE implementation, not after**.

In `tasks.md`, each User Story phase has TWO sub-sections:
1. **Tests for User Story N (TDD — write FIRST)** — contract + integration + unit test scaffolding
2. **Implementation for User Story N** — only after tests are in place

The Checkpoint at the end of each US phase: "All T00N* tests pass AND T00N* implementation passes".

In `spec.md`, each user story has:
- **Independent Test** field — how to verify this story works on its own
- **Acceptance Scenarios** (Given/When/Then) — GHERKIN format, directly translatable to test cases

## TDD Test Case Format (test-cases.md)

```
### TC-XXX-NNN: <Title>

- **ID**: TC-XXX-NNN
- **User Story**: US-X (Priority Pn)
- **Type**: unit | integration | contract
- **Preconditions**: <state before test>
- **Steps**:
  1. <action>
  2. <action>
- **Expected**: <observable outcome>
- **GHERKIN**: Given <state>, When <action>, Then <outcome>
- **Source**: spec.md §USx
```

- **ID format**: `TC-<capability-slug>-NNN` (sequential within capability)
- **Type**: contract (API/schema) | integration (cross-component) | unit (per-function)
- **GHERKIN**: 1:1 mirror of `spec.md` acceptance scenario
- **Source**: traceable back to the spec-kit spec.md US section

## Constitution Check (in plan.md)

Every plan.md includes a Constitution Check that enforces the project's quality rules:

```markdown
- [ ] I. TDD Discipline: All tests written FIRST, implementation follows
- [ ] II. Coverage Threshold: ≥ 80% line/branch coverage required
- [ ] III. Independent Testability: Each user story can be tested in isolation
```

Projects can extend the constitution with their own principles (logging, security, etc.).

## Workspace Allocation

| Workspace | Used For |
|-----------|----------|
| `workspace-pm/proposals/<PRJ>/` | PRD + tech-solution (input source) |
| `workspace-test/proposals/<project>/<PRJ>/` | spec-kit + TDD artifacts |
| `workspace-test/proposals/<project>/<PRJ>/spec-kit/` | spec-kit spec/plan/tasks |
| `workspace-dev/proposals/<project>/openspec/changes/<change>/` | OpenSpec post-acceptance |

This separation keeps the **TDD work-in-progress** separate from the **delivered spec**.

## Critical spec-kit Schema Rules (from real schema.yaml)

1. **User Story priority MUST be P1, P2, P3, ...** (no skipping; P1 = MVP)
2. **Each user story MUST be independently testable** (MVP-sliced)
3. **Acceptance Scenarios use Given/When/Then** (not just "should do X")
4. **Testing field in plan.md is MANDATORY** (TDD per skill spec)
5. **Tasks: Tests subsection MUST come BEFORE Implementation** (TDD order)
6. **Checklist is "unit tests for English"** — validates requirement quality, NOT implementation

## Workflow Integration

```
Step 5/6 (Tech Solution)
  → generate-tdd-spec.py <PRJ> --full
  → outputs spec-kit/{spec,plan,tasks}.md
  → Test Expert reviews spec.md + plan.md

Step 6b (TDD Test Cases)
  → generate-tdd-spec.py <PRJ>
  → adds test-cases.md + checklist.md to same dir
  → Test Expert finalizes test cases

Step 7 (Handoff to Dev)
  → Dev uses spec-kit/tasks.md (TDD-first tasks)
  → Writes failing tests first, then implementation

Step 8 (Test Expert Acceptance)
  → Test Expert runs test-cases.md
  → generate-tdd-spec.py <PRJ> --report results.json
  → Updates test-report.md + checklist-status.md
  → If pass: proceed to Step 9 (delivery, OpenSpec)
  → If fail: status → test_failed, dev revises
```

## Common Pitfalls

| Issue | Prevention |
|-------|------------|
| Implementation before tests | Tasks.md forces "Tests for User Story N" subsection FIRST |
| Generic acceptance criteria | spec.md requires Given/When/Then (not "should be fast") |
| P1 missing | Each user story MUST have a priority; P1 is non-negotiable |
| TDD tasks buried in implementation | Each US phase has 2 explicit subsections (Tests / Implementation) |
| `tests/unit/` missing | plan.md's Test Code section is mandatory: contract + integration + unit |
| Test cases not traceable | Each TC- has Source: `spec.md §USx` field |
| Constitution Check skipped | plan.md includes it as section with checkboxes |

## Authoritative Reference

- **Local clone**: `/home/hermes/opensource/spec-kit/`
- **Templates**: `templates/*-template.md` (canonical, 573 lines total)
- **Preset commands**: `presets/lean/commands/speckit.*.md` (workflow invocation)
- **Boss's fork**: https://github.com/YeLuo45/spec-kit
- **Upstream**: https://github.com/github/spec-kit
