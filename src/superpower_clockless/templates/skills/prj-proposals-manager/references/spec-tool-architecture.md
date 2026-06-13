# Spec Tool Architecture — Why Two Systems, When to Use Which

The prj-proposals-manager lifecycle now integrates **two spec systems**. This is a deliberate
architectural split, not redundancy. Future work on this skill or on integrating additional
spec tools must respect the split — do not try to unify the two or substitute one for the other.

## The split at a glance

| | spec-kit | OpenSpec |
|---|---|---|
| Lifecycle phase | **Pre-acceptance** (TDD layer) | **Post-acceptance** (delivery layer) |
| Trigger state | Step 5 (PRD confirmed) → Step 8 (test report) | Step 9+ (accepted, post-deployment docs) |
| Audience | Dev agent, Test agent, Reviewer | Future maintainers, release notes, change records |
| Output location | `workspace-test/<project>/proposals/<PRJ>/` | `workspace-dev/<project>/openspec/changes/<change>/` |
| Files | `test-cases.md`, `checklist.md`, `test-report.md`, `checklist-status.md`, `spec-kit/{spec,plan,tasks}.md` | `proposal.md`, `design.md`, `tasks.md`, `specs/<capability>/spec.md` |
| Driver | PRD user stories (testable) | Accepted change scope (deployable) |
| Generates test code? | **Yes** — task IDs reference `tests/{contract,integration,unit}/` paths | No — purely documentation |
| Authoritative when? | Status is `in_test_acceptance` or `test_failed` | Status is `accepted`, `deployed`, or `delivered` |

## Why two systems, not one

Three reasons drove the split:

1. **Different audience and timing.** TDD artifacts (test cases, plans, checklists) need to be
   produced early — before code is written — and discarded once the feature ships. Delivery
   artifacts (proposal, design, specs) need to be retained as a permanent record of *why* a
   change was made. Different retention, different format, different author.
2. **Different schema.** spec-kit speaks the language of TDD: User Story priority (P1/P2/P3),
   Independent Test, Given/When/Then scenarios, tests-first task ordering. OpenSpec speaks the
   language of capability evolution: ADDED Requirements, capability names as identifiers,
   Impact sections. A unified schema would have to compromise on both.
3. **Different downstream consumers.** spec-kit output feeds test runners and the dev agent
   (tasks.md drives implementation order). OpenSpec output feeds release notes, changelogs,
   and the ai-superpower website's `/changes` view. Forcing one file to serve both contexts
   makes both contexts worse.

## Decision tree — which tool to invoke?

```
Q: Is this a pre-code, test-design artifact?
   ├── Yes  → spec-kit (via scripts/generate-tdd-spec.py)
   │         Modes:
   │           default (Step 6b) — test-cases.md + checklist.md + report template
   │           --full           — adds spec-kit/{spec,plan,tasks}.md
   │           --report JSON    — renders test-report.md from results (Step 8)
   └── No   → Is it a post-acceptance delivery artifact?
              ├── Yes  → OpenSpec (via scripts/generate-spec.py)
              │         Modes:
              │           <PRJ>  — read PRD+tech-solution, generate 5 files
              │           --init <name>  — bootstrap legacy project from README
              └── No   → Neither. Use raw markdown in workspace-pm or workspace-research.
```

## Boundary rules (do not violate)

- **Never put spec-kit output under `workspace-dev/`** — it is test-phase material, not delivery
  material, and would pollute the OpenSpec change set.
- **Never put OpenSpec output under `workspace-test/`** — it is post-acceptance documentation
  and would be misleading alongside active test artifacts.
- **Do not regenerate spec-kit files from OpenSpec files (or vice versa).** The two systems
  consume different source documents. spec-kit reads the PRD's user stories; OpenSpec reads
  the tech-solution's capability list. If you find yourself wanting to bridge them, you have
  probably crossed a phase boundary that should not be crossed.
- **Capability names in OpenSpec are kebab-case, deduped, and stripped of backticks.** User
  story IDs in spec-kit follow `US{N}` where N increments per priority slot (P1, P2, P3…).
  These naming conventions are not interchangeable.

## Common mistakes and their fixes

### "I'll just generate both from one script"
This is tempting. Don't. The two scripts (`generate-spec.py` and `generate-tdd-spec.py`)
have different input contracts, different output schemas, and different timing in the
lifecycle. Coupling them means a failure in one phase blocks the other, and the schema
overhead (one file with both TDD and delivery sections) makes both downstream consumers
unhappy.

### "I need a test artifact after acceptance, can I use spec-kit?"
No. spec-kit's role is to drive the test cycle. Post-acceptance work uses regular regression
tests in the project's test directory (`tests/`), not the spec-kit artifacts. The spec-kit
files become historical record only — kept in `workspace-test/<project>/proposals/<PRJ>/`
for traceability, not consumed by the system.

### "Can I use OpenSpec to plan a feature that hasn't been built yet?"
No. OpenSpec is for recording *what changed*. A pre-build planning document belongs in the
PRD or tech-solution. Once the change is accepted, OpenSpec captures the *why* and *what*
for posterity.

### "I want to extend the spec systems — do I add a third?"
Only if the new system's lifecycle phase is genuinely orthogonal to both TDD and delivery.
Examples of legitimate additions: a **compliance** layer (produces `compliance/{control,evidence}.md`
between PRD and TDD), or a **release-notes** layer (consumes OpenSpec output, produces
player-facing or customer-facing release notes). For anything that overlaps with spec-kit's
TDD scope or OpenSpec's delivery scope, extend the existing tool rather than adding a new one.

## Implementation note — the format() pitfall

When generating markdown files from templates (both `generate-spec.py` and
`generate-tdd-spec.py`), the `str.format()` approach has a hidden gotcha: if the source
PRD or tech-solution contains curly-brace identifiers like `{project_id}`, `{user_id}`,
or `{entity.name}`, `format()` raises `KeyError` because it tries to resolve them as
template placeholders.

**Fix:** use `{placeholder_name_placeholder}` (or any non-conflicting name) in the
template, then pass the actual identifier as a `format()` kwarg. Concretely:

```python
# WRONG — KeyError if PRD contains "{project_id}"
template = "Project: {project_id}"
template.format(project_id=prj_id)
# Works for this case, but fails if PRD also contains literal {project_id}

# RIGHT — escape the placeholder name
template = "Project: {project_id_placeholder}"
template.format(project_id_placeholder=prj_id)
# Then post-process to rename {project_id_placeholder} back to {project_id}
# in the rendered output, OR use str.replace() instead of format() entirely.
```

Alternatively, use `str.Template` (with `$project_id` syntax) or plain `str.replace()` to
avoid the format() placeholder namespace entirely. See `scripts/generate-tdd-spec.py`
and `scripts/generate-spec.py` for working examples of the rename-then-format pattern.

## Verification protocol

When a spec generation script is added or modified, run all three modes against a real PRD
(e.g. `PRJ-20260417-001`) and verify the output structurally — don't just `py_compile`:

1. **Default mode** — confirm `test-cases.md` has TC IDs and Given/When/Then, `checklist.md`
   has CHK IDs, `checklist-status.md` exists.
2. **--full mode** — confirm `spec-kit/{spec,plan,tasks}.md` exist, `tasks.md` has Tests
   sub-sections before Implementation sub-sections, and Constitution Check is present.
3. **--report mode** — feed a mock JSON with at least one passing and one failing test,
   confirm the report renders pass rate, verdict, and detailed results sections.

A script that compiles but produces malformed output is worse than one that fails loudly —
silent schema drift breaks downstream consumers (test runners, acceptance reviewers) without
any error to investigate.
