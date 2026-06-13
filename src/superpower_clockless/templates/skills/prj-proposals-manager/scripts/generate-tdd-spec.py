#!/usr/bin/env python3
"""
generate-tdd-spec.py — Generate spec-kit TDD artifacts from prj-proposals-manager data.

This complements generate-spec.py (which generates OpenSpec post-acceptance artifacts).
This script generates spec-kit TDD artifacts for the pre-OpenSpec states:

  Step 5/6  (Tech Solution)    → spec-kit/plan.md
  Step 6b   (TDD Test Cases)   → spec-kit/spec.md + test-cases.md + checklist.md
  Step 8    (Test Acceptance)  → test-report.md + checklist-status.md
  Step 3    (PM Intake)        → spec-kit/constitution.md (project principles)

Reference: https://github.com/YeLuo45/spec-kit  (templates/, presets/)
           (upstream: https://github.com/github/spec-kit)
"""

import argparse
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

# ---------- Paths (override via env if needed) ----------
SUPERPOWER_ROOT = Path(os.environ.get("SUPERPOWER_ROOT", "/home/hermes/proposals"))
PM_PROPOSALS = SUPERPOWER_ROOT / "workspace-pm" / "proposals"
DEV_PROPOSALS = SUPERPOWER_ROOT / "workspace-dev" / "proposals"
TEST_PROPOSALS = SUPERPOWER_ROOT / "workspace-test" / "proposals"  # New TDD workspace
PROPOSALS_CSV = SUPERPOWER_ROOT / "proposals.csv"

# ---------- spec-kit TDD templates (canonical from github/spec-kit, adapted) ----------

# spec.md — User Stories with Given/When/Then + Independent Test
SPECKIT_SPEC_TEMPLATE = """# Feature Specification: {feature_name}

**Feature Branch**: `[###-feature-name]`
**Created**: {created}
**Status**: {status}
**Source Proposal**: {proposal_ref}
**Tests Required**: YES (TDD per spec-kit methodology)

## User Scenarios & Testing *(mandatory)*

> Each user story must be INDEPENDENTLY TESTABLE — implementing just ONE of them
> must still produce an MVP that delivers value. Assign priorities (P1, P2, P3...).

{user_stories}

## Requirements *(mandatory)*

{requirements}

## Success Criteria *(mandatory)*

{success_criteria}
"""

USER_STORY_TEMPLATE = """### User Story {priority} - {title}

{body}

**Why this priority**: {why_priority}

**Independent Test**: {independent_test}

**Acceptance Scenarios**:

{scenarios}

---
"""

REQUIREMENT_TEMPLATE = """### Requirement: {name}

{text}

{scenario}
"""

# plan.md — Tech Plan with Testing + Project Structure
SPECKIT_PLAN_TEMPLATE = """# Implementation Plan: {feature_name}

**Created**: {created}
**Source Proposal**: {proposal_ref}
**Spec**: [spec.md](./spec.md)

## Technical Context

**Language/Version**: {language}
**Primary Dependencies**: {dependencies}
**Storage**: {storage}
**Testing**: {testing}  ← **TDD-mandatory per skill spec**
**Target Platform**: {target_platform}
**Project Type**: {project_type}
**Performance Goals**: {performance_goals}
**Constraints**: {constraints}
**Scale/Scope**: {scale_scope}

## Constitution Check

{constitution_check}

## Project Structure

### Documentation (this feature)

```
spec-kit/
├── spec.md              # This specification
├── plan.md              # This plan
├── tasks.md             # Phase-organized task list (TDD-augmented)
├── checklist.md         # Requirements quality checklist
└── test-cases.md        # Structured test cases (TDD)

workspace-test/.../proposals/{project_id_placeholder}/
├── test-cases.md        # Working test cases for Test Expert
├── test-report.md       # Step 8 acceptance report
└── checklist-status.md  # Step 8 pass/fail per item
```

### Source Code (repository root)

```
{source_structure}
```

### Test Code (TDD-mandatory)

```
tests/
├── contract/            # API contract tests (schema/format)
├── integration/         # Cross-component tests
└── unit/                # Per-function/per-class tests
```

**Structure Decision**: {structure_decision}
"""

# tasks.md — Phase-organized with TDD Tests for each user story
SPECKIT_TASKS_TEMPLATE = """# Tasks: {feature_name}

**Input**: spec.md (required) + plan.md (required)
**Source Proposal**: {proposal_ref}

**Tests**: TDD-mandatory per skill spec — every user story phase includes a Tests subsection.
Tests run FIRST; implementation follows only after test scaffolding passes.

**Organization**: Tasks grouped by user story priority. Each story can be implemented
and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story tag (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize dependencies
- [ ] T003 [P] Configure linting and formatting

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure blocking all user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup test framework (vitest/jest/pytest — see plan.md Testing field)
- [ ] T005 [P] Setup CI test runner
- [ ] T006 [P] Setup coverage reporting
- [ ] T007 Create base abstractions all stories depend on

**Checkpoint**: Test framework runs `npm test` / `pytest` with empty test suite — 0 failures

{user_story_phases}

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T{last_id} [P] Update documentation
- [ ] T{last_id_plus_1} [P] Performance benchmarking
- [ ] T{last_id_plus_2} Code coverage report (≥80%)

## Dependencies & Execution Order

- Phase 1 (Setup) → Phase 2 (Foundational) → User Story phases in priority order → Polish
- Within each User Story: Tests first (TDD) → Implementation → Self-check
- Multiple user stories can be worked in parallel after Foundation phase

## Implementation Strategy

- **MVP First**: Implement User Story 1 (P1) end-to-end → demo → iterate
- **TDD Discipline**: For each task T00N, write failing test FIRST, then implementation
"""

USER_STORY_PHASE_TEMPLATE = """## Phase {phase_num}: User Story {priority} - {title} {mvp_badge}

**Goal**: {goal}

**Independent Test**: {independent_test}

### Tests for User Story {priority} (TDD — write FIRST) ⚠️

- [ ] T{test_id} [P] [US{us}] Write contract test for {title} in `tests/contract/test_{us_slug_placeholder}.py`
- [ ] T{test_id_plus_1} [P] [US{us}] Write integration test for {title} in `tests/integration/test_{us_slug_placeholder}.py`
- [ ] T{test_id_plus_2} [P] [US{us}] Write unit tests for {title} in `tests/unit/test_{us_slug_placeholder}.py`

### Implementation for User Story {priority}

- [ ] T{impl_id} [US{us}] Implement {title} per spec.md acceptance scenarios
- [ ] T{impl_id_plus_1} [US{us}] Verify all tests pass for {title}
- [ ] T{impl_id_plus_2} [US{us}] Self-check acceptance scenarios from spec.md

**Checkpoint**: User Story {priority} complete when all T{test_id}* tests pass AND T{impl_id}* implementation passes
"""

# checklist.md — Requirements quality checklist
SPECKIT_CHECKLIST_TEMPLATE = """# Requirements Quality Checklist: {feature_name}

**Purpose**: "Unit tests for English" — validate requirements quality, clarity, completeness
**Created**: {created}
**Source Proposal**: {proposal_ref}

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** —
they validate quality of requirements, NOT implementation correctness.

**NOT for verification/testing**:
- ❌ NOT "Verify the button clicks correctly"
- ❌ NOT "Test error handling works"
- ❌ NOT "Confirm the API returns 200"

**FOR requirements quality validation**:
- ✅ "Are visual hierarchy requirements defined for all card types?" (completeness)
- ✅ "Is 'prominent display' quantified with specific sizing?" (clarity)
- ✅ "Are hover state requirements consistent across interactive elements?" (consistency)
- ✅ "Does the spec define what happens when logo image fails to load?" (edge cases)

## Requirements Clarity

- [ ] CHK001 Are all functional requirements expressed in Given/When/Then format?
- [ ] CHK002 Are all priorities (P1/P2/P3) explicitly assigned?
- [ ] CHK003 Is each user story independently testable (MVP-sliced)?
- [ ] CHK004 Are all "prominent"/"fast"/"responsive" requirements quantified?

## Requirements Completeness

- [ ] CHK005 Are edge cases (empty input, max load, error states) covered?
- [ ] CHK006 Are accessibility requirements defined (keyboard nav, ARIA, contrast)?
- [ ] CHK007 Are error handling requirements explicit (not just "handle errors")?
- [ ] CHK008 Are data validation requirements (input format, length, range) specified?

## Requirements Consistency

- [ ] CHK009 Are naming conventions consistent across all requirements?
- [ ] CHK010 Are cross-cutting concerns (logging, monitoring, auth) consistent?
- [ ] CHK011 Are similar UI interactions described uniformly?

## Test Traceability

- [ ] CHK012 Does each requirement have ≥1 acceptance scenario (Given/When/Then)?
- [ ] CHK013 Is the TDD test plan (tests/contract + integration + unit) complete?
- [ ] CHK014 Are non-functional requirements (perf, security) testable?

## Notes

- Check items off as completed: `[x]`
- Items are numbered sequentially for easy reference
- Each `CHK` ID is referenced from test-report.md for traceability
"""

# test-cases.md — Structured TDD test cases (skill's existing format)
TEST_CASES_TEMPLATE = """# Test Cases: {feature_name}

**Source Proposal**: {proposal_ref}
**Generated**: {created}
**TDD Approach**: Each test case is derived from a spec.md user story acceptance scenario
**Test Framework**: {testing}

## Test Case Format

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
```

## Test Cases by User Story

{test_cases}
"""

TEST_CASE_TEMPLATE = """### TC-{cap_short}-001: {title}

- **ID**: TC-{cap_short}-001
- **User Story**: US-{priority} (Priority P{priority})
- **Type**: {test_type}
- **Preconditions**: {preconditions}
- **Steps**:
{steps}
- **Expected**: {expected}
- **GHERKIN**: {gherkin}
- **Source**: spec.md §{ref}

---
"""

# test-report.md — Step 8 acceptance report
TEST_REPORT_TEMPLATE = """# Test Report: {feature_name}

**Source Proposal**: {proposal_ref}
**Test Date**: {test_date}
**Tester**: Test Expert (TDD acceptance per spec-kit methodology)
**Source spec**: spec-kit/spec.md
**Source test cases**: test-cases.md

## Summary

- **Total test cases**: {total}
- **Passed**: {passed}
- **Failed**: {failed}
- **Skipped**: {skipped}
- **Pass rate**: {pass_rate}%

## Verdict

{verdict}

## Detailed Results

{detailed_results}

## Failure Analysis

{failure_analysis}

## Recommendations

{recommendations}
"""

# checklist-status.md — Step 8 pass/fail per CHK item
CHECKLIST_STATUS_TEMPLATE = """# Checklist Status: {feature_name}

**Test Date**: {test_date}
**Source**: spec-kit/checklist.md

## Status

{status_table}

## Summary

- **Total items**: {total}
- **Passed**: {passed}
- **Failed**: {failed}
- **N/A (not applicable)**: {na}

## Failed Items Detail

{failed_detail}
"""


# ---------- Helpers ----------

def log(msg, *, dry=False):
    prefix = "[DRY-RUN] " if dry else ""
    print(f"{prefix}{msg}", flush=True)


def find_proposal_dir(project_id: str) -> Path:
    candidates = [
        PM_PROPOSALS / project_id,
        PM_PROPOSALS / f"PRJ-{project_id}",
    ]
    if not project_id.startswith("PRJ-"):
        candidates.append(PM_PROPOSALS / f"PRJ-{project_id}")
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError(
        f"Project {project_id} not found in {PM_PROPOSALS}"
    )


def find_project_name(project_id: str) -> str:
    if PROPOSALS_CSV.exists():
        with open(PROPOSALS_CSV, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = row.get("project_id", "").strip()
                if pid in (project_id, f"PRJ-{project_id}"):
                    name = row.get("project_name", "").strip()
                    if name:
                        return name
    for d in PM_PROPOSALS.iterdir():
        if d.is_dir() and d.name == project_id:
            for prd in d.glob("*-prd.md"):
                m = re.search(r"^-\s+\*\*Project\*\*:\s+(\S+)", prd.read_text(encoding="utf-8"), re.MULTILINE)
                if m:
                    return m.group(1)
    return project_id.lower().replace("prj-", "")


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unnamed"


def read_first(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_section(text: str, header: str) -> str:
    pattern = rf"^##\s+{re.escape(header)}\s*$(.*?)(?=^##\s+|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def write_file(path: Path, content: str, dry: bool):
    if dry:
        log(f"  would write: {path.relative_to(SUPERPOWER_ROOT)} ({len(content)} bytes)", dry=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log(f"  wrote: {path.relative_to(SUPERPOWER_ROOT)} ({len(content)} bytes)")


# ---------- PRD parsing for TDD ----------

def parse_prd_for_tdd(pm_dir: Path) -> dict:
    """Parse PRD for TDD user stories / requirements."""
    prds = sorted(pm_dir.glob("*-prd.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not prds:
        raise FileNotFoundError(f"No *-prd.md in {pm_dir}")
    prd_text = prds[0].read_text(encoding="utf-8")
    title_m = re.search(r"^#\s+PRD:\s*(.+)$", prd_text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else prds[0].stem

    # Extract functional requirements as user stories
    func_section = extract_section(prd_text, "功能需求")
    user_stories = extract_user_stories(func_section)

    return {
        "title": title,
        "feature_name": re.sub(r"^PRD:\s*", "", title),
        "prd_text": prd_text,
        "user_stories": user_stories,  # list of {priority, title, body, scenarios, ...}
        "requirements": extract_requirements_section(func_section),
        "success_criteria": extract_success_criteria(prd_text),
        "_source": str(prds[0]),
    }


def extract_user_stories(func_section: str) -> list:
    """Parse PRD's `### N. <name>` patterns as P1/P2/P3 user stories."""
    if not func_section:
        return []
    stories = []
    for i, m in enumerate(re.finditer(
            r"^###\s+(\d+\.\s+)?`?([\w\s-]+)`?\s*[—\-:：]\s*(.+?)(?=^###\s+|^##\s+|\Z)",
            func_section, re.MULTILINE | re.DOTALL), 1):
        cap_name = (m.group(2) or "").strip().strip("`").lower()
        cap_name = re.sub(r"[^a-z0-9\s-]", "", cap_name)
        cap_name = re.sub(r"\s+", "-", cap_name).strip()
        if not cap_name or cap_name in ("new", "modified", "general"):
            continue
        body = (m.group(3) or "").strip()
        # Split into description (first paragraph) and params/details
        lines = [l for l in body.split("\n") if l.strip()]
        desc = lines[0] if lines else body[:200]
        # Try to find Given/When/Then or extract from structured params
        scenarios = extract_gherkin_scenarios(body)
        stories.append({
            "priority": min(i, 3),  # P1, P2, P3
            "us": i,
            "slug": cap_name,
            "title": cap_name.replace("-", " ").title(),
            "body": desc,
            "details": body[:500],  # Full PRD section for reference
            "scenarios": scenarios or [{
                "given": f"the {cap_name} is invoked",
                "when": "the user provides valid input",
                "then": f"{cap_name} completes successfully",
            }],
            "independent_test": f"Can be tested by triggering {cap_name} with valid input and observing expected behavior",
        })
    return stories[:5]  # Cap at 5 user stories


def extract_gherkin_scenarios(text: str) -> list:
    """Try to extract GHERKIN scenarios from PRD text."""
    scenarios = []
    # Pattern: **WHEN** / **THEN** or - **Given** / **When** / **Then**
    for m in re.finditer(
            r"(?:-\s+)?\*\*?(?:Given|When|Then)\*?\*?\s+(.+?)(?=(?:-\s+)?\*\*?(?:Given|When|Then)|$|\Z)",
            text, re.MULTILINE | re.DOTALL):
        scenarios.append({"given": "precondition (auto)", "when": m.group(1).strip()[:200], "then": "expected outcome (auto)"})
    return scenarios[:3]


def extract_requirements_section(func_section: str) -> str:
    """Extract formal requirements list for spec.md."""
    if not func_section:
        return "_To be defined from user stories._"
    lines = ["### Functional Requirements\n"]
    for m in re.finditer(
            r"^###\s+(\d+\.\s+)?`?([\w\s-]+)`?\s*[—\-:：]\s*(.+?)(?=^###\s+|^##\s+|\Z)",
            func_section, re.MULTILINE | re.DOTALL):
        cap_name = (m.group(2) or "").strip().strip("`")
        desc_first_line = ((m.group(3) or "").strip().split("\n")[0] or "").strip()
        if cap_name and desc_first_line:
            lines.append(f"- **FR-{slugify(cap_name).upper()[:20]}**: {cap_name} — {desc_first_line[:120]}")
    return "\n".join(lines) if len(lines) > 1 else "_To be defined._"


def extract_success_criteria(prd_text: str) -> str:
    """Extract or synthesize success criteria."""
    section = extract_section(prd_text, "验收标准")
    if not section:
        section = extract_section(prd_text, "Success Criteria")
    if section:
        return section
    # Synthesize from goals
    return "- [ ] All P1 user stories implemented and passing TDD tests\n- [ ] All P2 user stories implemented and passing TDD tests\n- [ ] Test coverage ≥ 80% (lines, branches)\n- [ ] No critical bugs in `npm run build` / `pytest`\n- [ ] All CHK items in checklist.md pass"


def parse_tech_solution_for_tdd(pm_dir: Path) -> dict:
    """Parse tech solution for plan.md fields."""
    tss = sorted(pm_dir.glob("*-tech-solution.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not tss:
        return {}
    ts_text = tss[0].read_text(encoding="utf-8")
    return {
        "language": _extract_field(ts_text, "语言") or "TypeScript 5.x / Node 20",
        "dependencies": _extract_field(ts_text, "依赖") or "React 19, Vite 5, Tailwind 4",
        "storage": _extract_field(ts_text, "存储") or "localStorage / GitHub API",
        "testing": _extract_field(ts_text, "测试") or "vitest 2.x + @testing-library/react (TDD mandatory)",
        "target_platform": _extract_field(ts_text, "目标平台") or "Web (browser)",
        "project_type": _extract_field(ts_text, "项目类型") or "web-app",
        "performance_goals": _extract_field(ts_text, "性能目标") or "Initial load < 1.5s, p95 < 200ms",
        "constraints": _extract_field(ts_text, "约束") or "Zero new heavy deps; web crypto API preferred",
        "scale_scope": _extract_field(ts_text, "规模") or "Single-page app, < 100 components",
        "source_structure": _extract_field(ts_text, "目录结构") or "src/\n├── components/\n├── pages/\n├── services/\n├── hooks/\n└── utils/",
        "structure_decision": _extract_field(ts_text, "结构决策") or "Web app (single project) with Vite build",
    }


def _extract_field(text: str, key: str) -> str:
    """Extract a field value from a tech-solution document."""
    for line in text.split("\n"):
        if key in line and ("：" in line or ":" in line):
            sep = "：" if "：" in line else ":"
            return line.split(sep, 1)[1].strip()
    return ""


# ---------- Main: TDD test case generation ----------

def generate_tdd_artifacts(project_id: str, *, full: bool = False, dry: bool = False):
    """Generate TDD artifacts for Step 6b (and optionally full spec-kit for Steps 5/6)."""
    pm_dir = find_proposal_dir(project_id)
    project_name = find_project_name(project_id)
    prd = parse_prd_for_tdd(pm_dir)
    tech = parse_tech_solution_for_tdd(pm_dir)
    today = date.today().isoformat()

    log(f"Project: {project_id} ({project_name})", dry=dry)
    log(f"PRD: {prd['_source']}", dry=dry)
    log(f"User stories extracted: {len(prd['user_stories'])}", dry=dry)

    # Output dir: workspace-test/{project}/proposals/{project_id}/
    test_dir = TEST_PROPOSALS / project_name / "proposals" / project_id
    spec_kit_dir = test_dir / "spec-kit"
    log(f"Output: {test_dir}", dry=dry)

    if not dry:
        spec_kit_dir.mkdir(parents=True, exist_ok=True)

    # 1. test-cases.md (Step 6b main output)
    test_cases_md = render_test_cases(prd, project_id, today, tech.get("testing", "TDD-mandatory"))
    write_file(test_dir / "test-cases.md", test_cases_md, dry)

    # 2. checklist.md (Step 6b req quality gate)
    checklist_md = SPECKIT_CHECKLIST_TEMPLATE.format(
        feature_name=prd["feature_name"],
        created=today,
        proposal_ref=project_id,
    )
    write_file(test_dir / "checklist.md", checklist_md, dry)

    if full:
        # 3. spec-kit/spec.md (Step 5/6 user stories with GHERKIN)
        spec_md = render_spec(prd, project_id, today)
        write_file(spec_kit_dir / "spec.md", spec_md, dry)

        # 4. spec-kit/plan.md (Step 5/6 tech plan with Testing)
        plan_md = render_plan(prd, project_id, tech, today)
        write_file(spec_kit_dir / "plan.md", plan_md, dry)

        # 5. spec-kit/tasks.md (Step 6b/7 TDD-augmented tasks)
        tasks_md = render_tasks(prd, project_id, today)
        write_file(spec_kit_dir / "tasks.md", tasks_md, dry)

    # 6. test-report.md TEMPLATE (Step 8 fills in)
    report_md = TEST_REPORT_TEMPLATE.format(
        feature_name=prd["feature_name"],
        proposal_ref=project_id,
        test_date=today,
        total="[TBD after test execution]",
        passed="[TBD]",
        failed="[TBD]",
        skipped="[TBD]",
        pass_rate="[TBD]",
        verdict="[pending test execution — fill after Step 8]",
        detailed_results="[Test Expert fills in after running test-cases.md]",
        failure_analysis="_No failures yet._",
        recommendations="_None yet._",
    )
    write_file(test_dir / "test-report.md", report_md, dry)

    # 7. checklist-status.md TEMPLATE (Step 8 fills in)
    check_status = CHECKLIST_STATUS_TEMPLATE.format(
        feature_name=prd["feature_name"],
        test_date=today,
        status_table="| CHK ID | Description | Status | Notes |\n|---|---|---|---|\n| _TBD after test execution_ | | | |",
        total="[TBD]",
        passed="[TBD]",
        failed="[TBD]",
        na="[TBD]",
        failed_detail="_None yet._",
    )
    write_file(test_dir / "checklist-status.md", check_status, dry)

    log(f"\n✓ TDD artifacts at: {test_dir}", dry=dry)
    if full:
        log(f"  + full spec-kit at: {spec_kit_dir}", dry=dry)
    return test_dir


def render_spec(prd: dict, project_id: str, today: str) -> str:
    user_stories_md = ""
    for s in prd["user_stories"]:
        scenarios_md = "\n".join(
            f"{i}. **Given** {sc['given']}, **When** {sc['when']}, **Then** {sc['then']}"
            for i, sc in enumerate(s["scenarios"], 1)
        )
        user_stories_md += USER_STORY_TEMPLATE.format(
            priority=s["priority"],
            title=s["title"],
            body=s["body"],
            why_priority=f"P{s['priority']} priority — {s['details'][:80]}",
            independent_test=s["independent_test"],
            scenarios=scenarios_md,
        )
    return SPECKIT_SPEC_TEMPLATE.format(
        feature_name=prd["feature_name"],
        created=today,
        status="Draft",
        proposal_ref=project_id,
        user_stories=user_stories_md or "_No user stories extracted._",
        requirements=prd["requirements"],
        success_criteria=prd["success_criteria"],
    )


def render_plan(prd: dict, project_id: str, tech: dict, today: str) -> str:
    if not tech:
        tech = {
            "language": "TypeScript 5.x",
            "dependencies": "React + Vite",
            "storage": "localStorage",
            "testing": "vitest + @testing-library/react (TDD mandatory)",
            "target_platform": "Web",
            "project_type": "web-app",
            "performance_goals": "Initial load < 1.5s",
            "constraints": "Zero heavy deps",
            "scale_scope": "< 100 components",
            "source_structure": "src/{{components,pages,services,hooks,utils}}/",
            "structure_decision": "Single web app",
        }
    return SPECKIT_PLAN_TEMPLATE.format(
        feature_name=prd["feature_name"],
        created=today,
        proposal_ref=project_id,
        project_id_placeholder=project_id,
        **tech,
        constitution_check="- [ ] I. TDD Discipline: All tests written FIRST, implementation follows\n- [ ] II. Coverage Threshold: ≥ 80% line/branch coverage required\n- [ ] III. Independent Testability: Each user story can be tested in isolation",
    )


def render_tasks(prd: dict, project_id: str, today: str) -> str:
    user_story_phases = ""
    last_id = 7  # T001-T007 reserved for setup + foundation
    for s in prd["user_stories"]:
        us_slug = s["slug"]
        test_id = last_id + 1
        impl_id = test_id + 3
        user_story_phases += USER_STORY_PHASE_TEMPLATE.format(
            phase_num=s["priority"] + 2,  # Phase 3 = US1
            priority=s["priority"],
            us=s["priority"],
            title=s["title"],
            mvp_badge="🎯 MVP" if s["priority"] == 1 else "",
            goal=s["body"],
            independent_test=s["independent_test"],
            test_id=test_id,
            test_id_plus_1=test_id + 1,
            test_id_plus_2=test_id + 2,
            us_slug_placeholder=us_slug,
            impl_id=impl_id,
            impl_id_plus_1=impl_id + 1,
            impl_id_plus_2=impl_id + 2,
        )
        last_id = impl_id + 2
    return SPECKIT_TASKS_TEMPLATE.format(
        feature_name=prd["feature_name"],
        proposal_ref=project_id,
        user_story_phases=user_story_phases or "_No user stories extracted._",
        last_id=last_id,
        last_id_plus_1=last_id + 1,
        last_id_plus_2=last_id + 2,
    )


def render_test_cases(prd: dict, project_id: str, today: str, testing: str) -> str:
    """Render structured test cases from PRD user stories."""
    test_cases_md = ""
    for s in prd["user_stories"]:
        cap_short = s["slug"][:20].upper()
        for i, sc in enumerate(s["scenarios"], 1):
            test_cases_md += TEST_CASE_TEMPLATE.format(
                cap_short=cap_short,
                title=f"{s['title']} — {sc.get('when', 'happy path')[:60]}",
                priority=s["priority"],
                test_type="integration" if i == 1 else "unit",
                preconditions=sc.get("given", "fresh state"),
                steps="\n".join(f"  {j+1}. {step}" for j, step in enumerate([
                    f"Setup: {sc.get('given', 'baseline state')}",
                    f"Action: {sc.get('when', 'invoke capability')}",
                    "Observe output",
                ])),
                expected=sc.get("then", "behavior matches spec"),
                gherkin=f"Given {sc.get('given', 'state')}, When {sc.get('when', 'action')}, Then {sc.get('then', 'outcome')}",
                ref=f"US{s['priority']}",
            )
    return TEST_CASES_TEMPLATE.format(
        feature_name=prd["feature_name"],
        proposal_ref=project_id,
        created=today,
        testing=testing,
        test_cases=test_cases_md or "_No test cases extracted._",
    )


# ---------- Main: report mode (Step 8) ----------

def render_report_from_execution(project_id: str, results: list, dry: bool = False):
    """Generate test-report.md and checklist-status.md from test execution results.

    results: list of {"id": "TC-XXX-NNN", "status": "pass|fail|skip", "duration_ms": int, "message": str}
    """
    pm_dir = find_proposal_dir(project_id)
    project_name = find_project_name(project_id)
    prd = parse_prd_for_tdd(pm_dir)
    test_dir = TEST_PROPOSALS / project_name / "proposals" / project_id
    today = date.today().isoformat()

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    skipped = sum(1 for r in results if r["status"] == "skip")
    pass_rate = f"{(passed / total * 100):.1f}" if total else "0.0"
    verdict = "✓ ACCEPTED" if failed == 0 and total > 0 else "✗ FAILED — revision required"

    detailed = "\n".join(
        f"| {r['id']} | {r['status'].upper()} | {r.get('duration_ms', '?')}ms | {r.get('message', '')} |"
        for r in results
    )
    failure_detail = "\n".join(
        f"- **{r['id']}**: {r.get('message', 'no detail')}"
        for r in results if r["status"] == "fail"
    ) or "_None._"
    recommendations = ("- All tests pass — proceed to delivery (Step 9)\n- Update test cases for next iteration"
                      if failed == 0 else "- Revise implementation per failure messages\n- Re-run test suite\n- Update proposal status: test_failed → in_test_acceptance")

    report_md = TEST_REPORT_TEMPLATE.format(
        feature_name=prd["feature_name"],
        proposal_ref=project_id,
        test_date=today,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        pass_rate=pass_rate,
        verdict=verdict,
        detailed_results=detailed or "_No results._",
        failure_analysis=failure_detail,
        recommendations=recommendations,
    )
    write_file(test_dir / "test-report.md", report_md, dry)
    log(f"\n✓ Test report at: {test_dir / 'test-report.md'}", dry=dry)


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser(
        description="Generate spec-kit TDD artifacts from prj-proposals-manager data",
        epilog="Reference: https://github.com/YeLuo45/spec-kit (upstream: github/spec-kit)",
    )
    p.add_argument("project_id", nargs="?", help="Project ID (e.g. PRJ-20260417-001)")
    p.add_argument("--full", action="store_true",
                   help="Also generate full spec-kit/{spec,plan,tasks}.md (Steps 5/6/6b)")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    p.add_argument("--report", metavar="RESULTS_JSON",
                   help="Step 8 mode: render test-report.md from results JSON file")
    args = p.parse_args()

    if args.report:
        import json
        with open(args.report) as f:
            results = json.load(f)
        # First arg is project_id
        if not args.project_id:
            p.print_help()
            sys.exit(1)
        render_report_from_execution(args.project_id, results, dry=args.dry_run)
        return

    if not args.project_id:
        p.print_help()
        sys.exit(1)

    generate_tdd_artifacts(args.project_id, full=args.full, dry=args.dry_run)


if __name__ == "__main__":
    main()
