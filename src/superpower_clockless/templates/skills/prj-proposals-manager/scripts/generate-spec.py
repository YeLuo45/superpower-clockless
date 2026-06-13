#!/usr/bin/env python3
"""
generate-spec.py — Generate OpenSpec SPEC files from prj-proposals-manager data.

Two modes:
  1. From accepted proposal:  generate-spec.py <project_id> [--dry-run]
     Reads PRD + tech-solution from workspace-pm, generates openspec/changes/<change>/
     under workspace-dev/<project_name>/.

  2. Init for existing project:  generate-spec.py --init <project_name> [--name DISPLAY]
     Reads README.md / SPEC.md from workspace-dev/<project_name>/, generates openspec/.

Reference: https://github.com/YeLuo45/OpenSpec  (schemas/spec-driven/)
Real OpenSpec layout: openspec/changes/<change-name>/{proposal.md, design.md, tasks.md, specs/<capability>/spec.md, .openspec.yaml}
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
PROPOSALS_CSV = SUPERPOWER_ROOT / "proposals.csv"

# ---------- OpenSpec schema reference ----------
# Authoritative source: https://github.com/YeLuo45/OpenSpec/blob/main/schemas/spec-driven/templates/
OPENSPEC_PROPOSAL_TEMPLATE = """## Why

{why}

## What Changes

{what_changes}

## Capabilities

### New Capabilities

{new_capabilities}

### Modified Capabilities

{modified_capabilities}

## Impact

{impact}
"""

OPENSPEC_DESIGN_TEMPLATE = """## Context

{context}

## Goals / Non-Goals

**Goals:**
{goals}

**Non-Goals:**
{non_goals}

## Decisions

{decisions}

## Risks / Trade-offs

{risks}
"""

OPENSPEC_TASKS_TEMPLATE = """{task_groups}
"""

OPENSPEC_SPEC_TEMPLATE = """## ADDED Requirements

### Requirement: {requirement_name}
{requirement_text}

#### Scenario: {scenario_name}
- **WHEN** {when}
- **THEN** {then}
"""

OPENSPEC_YAML_TEMPLATE = """schema: spec-driven
created: {created}
{proposal_line}
"""


# ---------- Helpers ----------

def log(msg, *, dry=False):
    prefix = "[DRY-RUN] " if dry else ""
    print(f"{prefix}{msg}", flush=True)


def find_proposal_dir(project_id: str) -> Path:
    """Find the workspace-pm directory for a project_id."""
    candidates = [
        PM_PROPOSALS / project_id,
        PM_PROPOSALS / f"PRJ-{project_id}",
    ]
    # Also try without PRJ- prefix
    if not project_id.startswith("PRJ-"):
        candidates.append(PM_PROPOSALS / f"PRJ-{project_id}")
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError(
        f"Project {project_id} not found in {PM_PROPOSALS}. "
        f"Tried: {[str(c) for c in candidates]}"
    )


def find_project_name(project_id: str) -> str:
    """Look up project name in proposals.csv (or workspace-pm)."""
    if PROPOSALS_CSV.exists():
        with open(PROPOSALS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("project_id", "").strip()
                if pid == project_id:
                    name = row.get("project_name", "").strip()
                    if name:
                        return name
                # Also try matching PRJ- prefix
                if pid == f"PRJ-{project_id}" or f"PRJ-{pid}" == project_id:
                    name = row.get("project_name", "").strip()
                    if name:
                        return name
    # Fallback: scan workspace-pm for any project matching
    for d in PM_PROPOSALS.iterdir():
        if d.is_dir() and d.name == project_id:
            # Try to find name in any prd.md
            for prd in d.glob("*-prd.md"):
                content = prd.read_text(encoding="utf-8")
                m = re.search(r"^-\s+\*\*Project\*\*:\s+(\S+)", content, re.MULTILINE)
                if m:
                    return m.group(1)
    # Last resort
    return project_id.lower().replace("prj-", "")


def slugify(s: str) -> str:
    """Convert to OpenSpec change-name slug (lowercase, hyphens)."""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "unnamed"


def read_first(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def extract_section(text: str, header: str, next_headers: list = None) -> str:
    """Extract content under a markdown ## header until the next ## header."""
    next_headers = next_headers or []
    pattern = rf"^##\s+{re.escape(header)}\s*$(.*?)(?=^##\s+|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def parse_prd(pm_dir: Path) -> dict:
    """Parse PRD into proposal.md sections."""
    # Find the most recent prd.md
    prds = sorted(pm_dir.glob("*-prd.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not prds:
        raise FileNotFoundError(f"No *-prd.md found in {pm_dir}")
    prd_text = prds[0].read_text(encoding="utf-8")
    prd_name = prds[0].name

    # Extract proposal ID + title
    pid_match = re.search(r"^#\s+PRD:\s*(.+)$", prd_text, re.MULTILINE)
    title = pid_match.group(1).strip() if pid_match else prd_name.replace(".md", "")

    # Map PRD sections to OpenSpec proposal sections
    has_modified = bool(extract_section(prd_text, "修改的功能") or extract_section(prd_text, "Modified Functionalities"))
    return {
        "title": title,
        "why": extract_section(prd_text, "背景与目标")
                or extract_section(prd_text, "背景")
                or extract_section(prd_text, "Why")
                or "_See PRD for motivation._",
        "what_changes": extract_section(prd_text, "功能需求")
                or extract_section(prd_text, "What Changes")
                or "_See PRD for detailed requirements._",
        "new_capabilities": extract_capabilities(prd_text, "new"),
        "modified_capabilities": extract_capabilities(prd_text, "modified") if has_modified else "",
        "impact": extract_section(prd_text, "影响")
                or extract_section(prd_text, "Impact")
                or "_See PRD for affected components._",
        "_source": str(prds[0]),
    }


def extract_capabilities(text: str, kind: str) -> str:
    """Extract capability list from PRD functional requirements.

    Args:
        text: PRD text
        kind: "new" or "modified" — for differentiation, but we extract all
              and let the user prune in the proposal.
    """
    # Try functional-requirements section, look for ### N. <name>
    section = extract_section(text, "功能需求")
    if not section:
        return "- _No new capabilities specified._"
    caps = []
    seen = set()
    for m in re.finditer(r"^###\s+(\d+\.\s+)?`?([\w-]+(?:\s+[\w-]+)*)`?\s*[—\-:：]\s*(.+)$",
                         section, re.MULTILINE):
        cap_name_raw = m.group(2)
        # Strip backticks and normalize
        cap_name = re.sub(r"[^a-z0-9\s-]", "", cap_name_raw.lower()).strip()
        cap_name = re.sub(r"\s+", "-", cap_name)
        desc = (m.group(3) or "").strip()[:80]
        if not cap_name or cap_name in seen:
            continue
        if cap_name in ("new", "modified", "deleted", "deprecated", "general"):
            continue
        seen.add(cap_name)
        caps.append(f"- `{cap_name}`: {desc}")
    if not caps:
        return "- _No new capabilities specified._"
    return "\n".join(caps[:5])  # Top 5 capabilities


def parse_tech_solution(pm_dir: Path) -> dict:
    """Parse tech solution into design.md sections."""
    tss = sorted(pm_dir.glob("*-tech-solution.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not tss:
        # Fall back: use PRD's technical section
        return None
    ts_text = tss[0].read_text(encoding="utf-8")

    return {
        "context": extract_section(ts_text, "背景")
                or extract_section(ts_text, "Context")
                or extract_section(ts_text, "概述")
                or "_See tech solution for context._",
        "goals": extract_section(ts_text, "目标")
                or extract_section(ts_text, "Goals")
                or "- _See tech solution._",
        "non_goals": extract_section(ts_text, "非目标")
                or extract_section(ts_text, "Non-Goals")
                or "- _See tech solution._",
        "decisions": extract_section(ts_text, "技术决策")
                or extract_section(ts_text, "Decisions")
                or extract_section(ts_text, "方案")
                or "_See tech solution for design decisions._",
        "risks": extract_section(ts_text, "风险")
                or extract_section(ts_text, "Risks")
                or "_See tech solution for risk analysis._",
        "_source": str(tss[0]),
    }


def extract_requirements_from_prd(prd_text: str) -> list:
    """Extract requirements from PRD for spec.md generation.

    Returns a list of {capability, name, description, scenarios} dicts.
    Deduped by capability name to prevent spec.md overwrites.
    """
    section = extract_section(prd_text, "功能需求")
    if not section:
        return []
    reqs = []
    seen_caps = set()
    for m in re.finditer(r"^###\s+(\d+\.\s+)?`?([\w-]+(?:\s+[\w-]+)*)`?\s*[—\-:：]\s*(.+?)(?=^###\s+|^##\s+|\Z)",
                         section, re.MULTILINE | re.DOTALL):
        cap_name_raw = m.group(2)
        # Strip backticks and normalize
        cap_name = re.sub(r"[^a-z0-9\s-]", "", cap_name_raw.lower()).strip()
        cap_name = re.sub(r"\s+", "-", cap_name)
        if not cap_name or cap_name in seen_caps:
            continue
        if cap_name in ("new", "modified", "general"):
            continue
        seen_caps.add(cap_name)
        cap_body = (m.group(3) or "").strip()
        # First non-empty line is the description
        lines = [l for l in cap_body.split("\n") if l.strip()]
        desc = lines[0] if lines else cap_body[:200]
        reqs.append({
            "capability": cap_name,
            "name": cap_name.replace("-", " ").title(),
            "description": desc[:300],
            "scenarios": extract_scenarios(cap_body),
        })
    return reqs[:3]  # Top 3 requirements per spec


def extract_scenarios(text: str) -> list:
    """Extract WHEN/THEN scenarios from a requirement block."""
    scenarios = []
    for m in re.finditer(r"^-\s+\*\*WHEN\*\*\s+(.+?)$", text, re.MULTILINE):
        when = m.group(1).strip() or "the user invokes this capability"
        # Find matching THEN
        after = text[m.end():]
        then_m = re.search(r"^-\s+\*\*THEN\*\*\s+(.+?)$", after, re.MULTILINE)
        then = (then_m.group(1).strip() if then_m else "the operation completes successfully") or "the operation completes successfully"
        scenarios.append({"when": when, "then": then})
        if len(scenarios) >= 3:
            break
    if not scenarios:
        scenarios.append({
            "when": "the user invokes this capability",
            "then": "it SHALL behave as described above",
        })
    return scenarios


def extract_tasks_from_prd(prd_text: str) -> str:
    """Extract tasks.md checklist from PRD implementation plan."""
    # Try 实施计划 / Implementation / 步骤 sections
    for header in ["实施计划", "实现步骤", "Implementation Plan", "Steps", "Tasks"]:
        section = extract_section(prd_text, header)
        if section:
            return section
    # Fallback: synthesize from functional requirements
    section = extract_section(prd_text, "功能需求")
    if not section:
        return "## 1. Implementation\n\n- [ ] 1.1 See PRD for detailed tasks."
    lines = ["## 1. Core Implementation"]
    for i, m in enumerate(re.finditer(r"^###\s+(\d+\.\s+)?`?([\w-]+)`?", section, re.MULTILINE), 1):
        cap_name = m.group(2)
        if cap_name in ("new", "modified"):
            continue
        lines.append(f"- [ ] 1.{i} Implement `{cap_name}`")
    lines.append("")
    lines.append("## 2. Testing & Validation")
    lines.append("- [ ] 2.1 Unit tests for new functionality")
    lines.append("- [ ] 2.2 Integration tests")
    lines.append("")
    lines.append("## 3. Documentation")
    lines.append("- [ ] 3.1 Update README/docs")
    return "\n".join(lines)


# ---------- Init mode (for projects without proposal) ----------

def parse_readme_for_init(project_path: Path, display_name: str = None) -> dict:
    """Parse existing README.md / SPEC.md to bootstrap a SPEC."""
    readme = project_path / "README.md"
    spec_md = project_path / "SPEC.md"
    content = ""
    src = "template"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        src = "README.md"
    elif spec_md.exists():
        content = spec_md.read_text(encoding="utf-8")
        src = "SPEC.md"
    # Extract name + description
    name = display_name or project_path.name
    title_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_m:
        name = display_name or title_m.group(1).strip()
    desc = ""
    lines = content.split("\n")
    for line in lines[1:]:
        if line.strip() and not line.startswith("#"):
            desc = line.strip()
            break
    return {
        "name": name,
        "description": desc or f"Init-mode spec for {name}",
        "source": src,
    }


# ---------- Main: from accepted proposal ----------

def generate_from_proposal(project_id: str, dry: bool = False):
    pm_dir = find_proposal_dir(project_id)
    project_name = find_project_name(project_id)
    log(f"Project dir: {pm_dir}", dry=dry)
    log(f"Project name: {project_name}", dry=dry)

    prd = parse_prd(pm_dir)
    log(f"PRD source: {prd['_source']}", dry=dry)

    design = parse_tech_solution(pm_dir)
    if design:
        log(f"Tech solution source: {design['_source']}", dry=dry)
    else:
        log("No tech-solution.md — using PRD-derived design.md", dry=dry)
        design = {
            "context": prd.get("why", ""),
            "goals": "See PRD functional requirements",
            "non_goals": "_To be determined_",
            "decisions": prd.get("what_changes", ""),
            "risks": "_See PRD impact section_",
        }

    # Extract change name from PRD title
    title = prd.get("title", "")
    change_slug = slugify(title)[:50]
    today = date.today().isoformat()
    change_name = f"{today}-{change_slug}"
    out_dir = DEV_PROPOSALS / project_name / "openspec" / "changes" / change_name

    log(f"Output: {out_dir}", dry=dry)

    if not dry:
        (out_dir / "specs").mkdir(parents=True, exist_ok=True)

    # 1. .openspec.yaml
    yaml_content = OPENSPEC_YAML_TEMPLATE.format(
        created=today,
        proposal_line=f"proposal: {project_id}",
    )
    write_file(out_dir / ".openspec.yaml", yaml_content, dry)

    # 2. proposal.md
    proposal_content = OPENSPEC_PROPOSAL_TEMPLATE.format(
        why=prd["why"],
        what_changes=prd["what_changes"],
        new_capabilities=prd["new_capabilities"],
        modified_capabilities=prd["modified_capabilities"],
        impact=prd["impact"],
    )
    write_file(out_dir / "proposal.md", proposal_content, dry)

    # 3. design.md
    design_content = OPENSPEC_DESIGN_TEMPLATE.format(
        context=design["context"],
        goals=design["goals"],
        non_goals=design["non_goals"],
        decisions=design["decisions"],
        risks=design["risks"],
    )
    write_file(out_dir / "design.md", design_content, dry)

    # 4. tasks.md
    prd_text = read_first(Path(prd["_source"]))
    tasks_content = extract_tasks_from_prd(prd_text)
    write_file(out_dir / "tasks.md", tasks_content, dry)

    # 5. specs/<capability>/spec.md
    reqs = extract_requirements_from_prd(prd_text)
    if reqs:
        for req in reqs:
            cap_dir = out_dir / "specs" / req["capability"]
            if not dry:
                cap_dir.mkdir(parents=True, exist_ok=True)
            # Combine all scenarios for this requirement
            scenario_blocks = []
            for i, sc in enumerate(req["scenarios"], 1):
                scenario_blocks.append(OPENSPEC_SPEC_TEMPLATE.format(
                    requirement_name=req["name"] if i == 1 else f"{req['name']} (cont.)",
                    requirement_text=req["description"] if i == 1 else "_Continuation of requirement above._",
                    scenario_name=f"Scenario {i}",
                    when=sc["when"],
                    then=sc["then"],
                ))
            spec_content = "\n".join(scenario_blocks)
            write_file(cap_dir / "spec.md", spec_content, dry)
        log(f"Generated {len(reqs)} spec(s) under specs/", dry=dry)
    else:
        log("No requirements extracted — generating minimal spec.md", dry=dry)
        write_file(out_dir / "specs" / "general" / "spec.md",
                   "## ADDED Requirements\n\n### Requirement: General\n_To be defined._\n",
                   dry)

    log(f"\n✓ Generated OpenSpec SPEC at: {out_dir}", dry=dry)
    if dry:
        log("(dry-run: no files written)", dry=dry)
    return out_dir


# ---------- Main: init mode ----------

def generate_init(project_name: str, display_name: str = None, dry: bool = False):
    project_path = DEV_PROPOSALS / project_name
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project not found: {project_path}")
    info = parse_readme_for_init(project_path, display_name)
    log(f"Init from {info['source']} for project: {info['name']}", dry=dry)

    today = date.today().isoformat()
    change_slug = slugify(info["name"])[:50]
    change_name = f"{today}-init-{change_slug}"
    out_dir = project_path / "openspec" / "changes" / change_name

    log(f"Output: {out_dir}", dry=dry)

    if not dry:
        (out_dir / "specs").mkdir(parents=True, exist_ok=True)

    # .openspec.yaml with init: true marker
    yaml_content = OPENSPEC_YAML_TEMPLATE.format(
        created=today,
        proposal_line="init: true",
    )
    write_file(out_dir / ".openspec.yaml", yaml_content, dry)

    # proposal.md
    proposal_content = OPENSPEC_PROPOSAL_TEMPLATE.format(
        why=f"Initialize OpenSpec SPEC for existing project: {info['name']}\n\n{info['description']}",
        what_changes="- _Bootstrap spec for existing project, generated from README/SPEC.md_",
        new_capabilities="- _To be defined from existing functionality_",
        modified_capabilities="",
        impact="_Initial SPEC generation, no code changes_",
    )
    write_file(out_dir / "proposal.md", proposal_content, dry)

    # design.md (template)
    design_content = OPENSPEC_DESIGN_TEMPLATE.format(
        context=f"Existing project: {info['name']}\n\n{info['description']}",
        goals="- _Define from existing project README_",
        non_goals="- _To be determined_",
        decisions="_To be added when spec is reviewed_",
        risks="_To be assessed_",
    )
    write_file(out_dir / "design.md", design_content, dry)

    # tasks.md
    write_file(out_dir / "tasks.md",
               "## 1. Review Bootstrap\n\n- [ ] 1.1 Review generated proposal.md\n- [ ] 1.2 Fill in capabilities section\n- [ ] 1.3 Add concrete requirements to specs/\n",
               dry)

    # specs/
    if not dry:
        (out_dir / "specs" / "general").mkdir(parents=True, exist_ok=True)
    write_file(out_dir / "specs" / "general" / "spec.md",
               "## ADDED Requirements\n\n### Requirement: To Be Defined\n_To be extracted from existing project functionality._\n",
               dry)

    log(f"\n✓ Init SPEC at: {out_dir}", dry=dry)


# ---------- File write helper ----------

def write_file(path: Path, content: str, dry: bool):
    if dry:
        log(f"  would write: {path.relative_to(SUPERPOWER_ROOT)} ({len(content)} bytes)", dry=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log(f"  wrote: {path.relative_to(SUPERPOWER_ROOT)} ({len(content)} bytes)")


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser(
        description="Generate OpenSpec SPEC files from prj-proposals-manager data",
        epilog="Reference: https://github.com/YeLuo45/OpenSpec (schemas/spec-driven/)",
    )
    p.add_argument("project_id", nargs="?", help="Project ID (e.g. PRJ-20260417-001) for proposal mode")
    p.add_argument("--init", metavar="PROJECT_NAME", help="Init mode: bootstrap SPEC for existing project")
    p.add_argument("--name", help="Display name for init mode")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    p.add_argument("--init-all", action="store_true", help="Init mode: bootstrap all projects without SPEC")
    args = p.parse_args()

    if args.init_all:
        # Batch init
        count = 0
        for d in sorted(DEV_PROPOSALS.iterdir()):
            if not d.is_dir():
                continue
            if (d / "openspec").is_dir():
                log(f"skip (has openspec/): {d.name}")
                continue
            try:
                generate_init(d.name, dry=args.dry_run)
                count += 1
            except Exception as e:
                log(f"error: {d.name}: {e}")
        log(f"\n{'Would init' if args.dry_run else 'Initialized'}: {count} project(s)")
        return

    if args.init:
        generate_init(args.init, args.name, dry=args.dry_run)
        return

    if not args.project_id:
        p.print_help()
        sys.exit(1)

    generate_from_proposal(args.project_id, dry=args.dry_run)


if __name__ == "__main__":
    main()
