#!/usr/bin/env python3
"""
skill-soul-audit.py — Automated SOUL.md / SKILL.md / MEMORY.md / USER.md alignment audit.

Validates 17 baseline items documented in references/soul-alignment-checklist.md.
Exits 0 if all checks pass, 1 if any conflict is found.

Usage:
    python3 scripts/skill-soul-audit.py [<skill-name>]
    # Default skill: prj-proposals-manager

Examples:
    # Audit the default prj-proposals-manager skill
    python3 scripts/skill-soul-audit.py

    # Audit a different skill
    python3 scripts/skill-soul-audit.py ai-superpower-iteration-workflow

    # JSON output for downstream tooling
    python3 scripts/skill-soul-audit.py --json

When to run:
    - After boss records a new preference in USER.md
    - After any SOUL.md update
    - Before merging a new skill version
    - When boss reports behavior that "doesn't match what USER.md says"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKILLS_ROOT = Path.home() / ".hermes" / "skills"
DEFAULT_SKILL = "prj-proposals-manager"


def check_owner_field(skill_dir: Path) -> dict:
    """Audit item #11: --owner should be '小墨' (matching SOUL.md), not 'coordinator'."""
    md_files = list(skill_dir.rglob("*.md"))
    bad_owner_examples = []
    good_owner_examples = []
    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'--owner\s+["\']?coordinator["\']?', content):
            # Allow explanatory notes that mention "coordinator" as a role name
            line_no = content[: m.start()].count("\n") + 1
            line_text = content.splitlines()[line_no - 1] if line_no <= len(content.splitlines()) else ""
            # If line is in a note/comment that explains "coordinator is role name, not value", skip
            if "角色名" in line_text or "ROLE NAME" in line_text or "role name" in line_text.lower():
                continue
            bad_owner_examples.append(f"{f.relative_to(skill_dir)}:{line_no}")
        for m in re.finditer(r'--owner\s+["\']?小墨["\']?', content):
            line_no = content[: m.start()].count("\n") + 1
            good_owner_examples.append(f"{f.relative_to(skill_dir)}:{line_no}")
    return {
        "check": "Owner field value (#11)",
        "pass": len(bad_owner_examples) == 0,
        "good_examples": len(good_owner_examples),
        "conflicts": bad_owner_examples,
    }


def check_state_machine_diagram(skill_dir: Path) -> dict:
    """Audit item #12: ASCII state machine diagram must show test_failed → in_test_acceptance loop."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"check": "State machine diagram (#12)", "pass": False, "note": "SKILL.md missing"}
    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    # Look for the diagram block (between ``` marks) and check for test_failed loop arrow
    has_diagram = "test_failed" in content
    has_loop_arrow = bool(
        re.search(r"test_failed.*re-test|re-test.*test_failed", content)
        or re.search(r"test_failed.*返回 in_dev|dev 返修", content)
    )
    return {
        "check": "State machine diagram completeness (#12)",
        "pass": has_diagram and has_loop_arrow,
        "has_diagram": has_diagram,
        "has_loop_arrow": has_loop_arrow,
    }


def check_unattended_mode(skill_dir: Path) -> dict:
    """Audit item #13: All confirmation gates (Step 4, 5, 10, 11) must have In Unattended Mode."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"check": "Unattended mode coverage (#13)", "pass": False}
    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    # Count "In Unattended Mode" subsections (English) + "无人值守模式（Step" (Chinese)
    en_count = len(re.findall(r"In Unattended Mode \(Step \d+", content))
    zh_count = len(re.findall(r"无人值守模式（Step \d+", content))
    # Need at least 4 (Step 4, 5, 10, 11)
    return {
        "check": "Unattended mode coverage (#13)",
        "pass": en_count >= 4 or zh_count >= 4,
        "en_subsections": en_count,
        "zh_subsections": zh_count,
        "expected": 4,
    }


def check_delivery_report_fields(skill_dir: Path) -> dict:
    """Audit item #14: 4 必含字段 in Communication Style / 沟通风格 section."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"check": "Delivery report 4 必含字段 (#14)", "pass": False}
    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    required = ["项目链接", "部署分支", "项目ID", "项目 ID", "提案ID", "提案 ID"]
    # Or English equivalents in same section
    en_required = ["Project link", "Deploy branch", "Project ID", "Proposal ID"]
    found_cn = [r for r in required if r in content]
    found_en = [r for r in en_required if r in content]
    total_found = len(set(found_cn + found_en))
    return {
        "check": "Delivery report 4 必含字段 (#14)",
        "pass": total_found >= 4,
        "found": list(set(found_cn + found_en)),
        "expected": 4,
    }


def check_iteration_sizing(skill_dir: Path) -> dict:
    """Audit item #15: Iteration Sizing section with 5-30 任意 range."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"check": "Iteration sizing (#15)", "pass": False}
    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    has_section = "## Iteration Sizing" in content or "## 迭代轮次" in content
    has_range = "5-30" in content or "5-30 任意" in content
    return {
        "check": "Iteration sizing (#15)",
        "pass": has_section and has_range,
        "has_section": has_section,
        "has_range": has_range,
    }


def check_communication_style(skill_dir: Path) -> dict:
    """Audit item #16: Communication Style section with 中文 preference."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"check": "Communication style (#16)", "pass": False}
    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    has_section = "## Communication Style" in content or "## 沟通风格" in content
    has_lang_pref = "中文" in content or "Chinese" in content
    return {
        "check": "Communication style (#16)",
        "pass": has_section and has_lang_pref,
        "has_section": has_section,
        "has_language_preference": has_lang_pref,
    }


def check_mcp_only(skill_dir: Path) -> dict:
    """Audit item #17: All API examples use mcp_aisp.py; legacy aisp CLI/REST reserved for emergency."""
    md_files = list(skill_dir.rglob("*.md"))
    mcp_count = 0
    aisp_cli_count = 0
    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        mcp_count += len(re.findall(r"mcp_aisp\.py", content))
        # aisp proposal/project CLI references (not in reverse-example docs)
        aisp_cli_count += len(
            re.findall(r"`aisp proposal (get|list|update|create)`|`aisp project (get|list|create|update)`", content)
        )
    return {
        "check": "MCP-only access (#17)",
        "pass": mcp_count > 50 and aisp_cli_count < 5,  # tolerate reverse-example docs
        "mcp_references": mcp_count,
        "legacy_aisp_cli_references": aisp_cli_count,
    }


def check_soul_md_v4_artifacts() -> dict:
    """Audit items #1-#10: SOUL.md v4-era drift."""
    soul_files = list(Path.home().glob(".hermes/SOUL.md")) + list(
        (Path.home() / ".hermes" / "profiles").rglob("SOUL.md")
    )
    v4_patterns = [
        r"in_acceptance\b",
        r"in_tdd_test\b",
        r"needs_revision\b",
        r"CSV 是数据源",
        r"proposal_manager_cli\.py proposal (add|update)",
    ]
    conflicts = []
    for f in soul_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        for pat in v4_patterns:
            for m in re.finditer(pat, content):
                line_no = content[: m.start()].count("\n") + 1
                conflicts.append(f"{f.relative_to(Path.home())}:{line_no}: {m.group()}")
    return {
        "check": "SOUL.md v4 artifacts (#1-#10)",
        "pass": len(conflicts) == 0,
        "soul_files_scanned": len(soul_files),
        "conflicts": conflicts[:10],  # cap output
    }


def check_duplicate_state_machine() -> dict:
    """Audit item #9: Only ONE '## 提案状态' section per SOUL.md."""
    soul_files = list(Path.home().glob(".hermes/SOUL.md")) + list(
        (Path.home() / ".hermes" / "profiles").rglob("SOUL.md")
    )
    duplicates = []
    for f in soul_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        count = content.count("^## 提案状态") + len(re.findall(r"^## 提案状态", content, re.MULTILINE))
        if count > 1:
            duplicates.append(f"{f.relative_to(Path.home())}: {count} '## 提案状态' sections")
    return {
        "check": "Duplicate state machine sections (#9)",
        "pass": len(duplicates) == 0,
        "duplicates": duplicates,
    }


ALL_CHECKS = [
    check_soul_md_v4_artifacts,
    check_duplicate_state_machine,
    check_owner_field,
    check_state_machine_diagram,
    check_unattended_mode,
    check_delivery_report_fields,
    check_iteration_sizing,
    check_communication_style,
    check_mcp_only,
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "skill",
        nargs="?",
        default=DEFAULT_SKILL,
        help=f"Skill name to audit (default: {DEFAULT_SKILL})",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--skill-root", type=Path, default=SKILLS_ROOT, help="Skills root directory")
    args = parser.parse_args()

    skill_dir = args.skill_root / args.skill
    if not skill_dir.exists():
        print(f"ERROR: skill not found at {skill_dir}", file=sys.stderr)
        return 2

    results = []
    for check in ALL_CHECKS:
        try:
            if check is check_owner_field or check is check_state_machine_diagram \
               or check is check_unattended_mode or check is check_delivery_report_fields \
               or check is check_iteration_sizing or check is check_communication_style \
               or check is check_mcp_only:
                results.append(check(skill_dir))
            else:
                results.append(check())
        except Exception as e:
            results.append({"check": check.__name__, "pass": False, "error": str(e)})

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"=== skill-soul-audit: {args.skill} ===\n")
        n_pass = sum(1 for r in results if r.get("pass"))
        n_fail = len(results) - n_pass
        for r in results:
            status = "✓ PASS" if r.get("pass") else "✗ FAIL"
            print(f"[{status}] {r.get('check', '?')}")
            # Print detail keys (skip 'check' and 'pass')
            for k, v in r.items():
                if k in ("check", "pass"):
                    continue
                if isinstance(v, list) and v:
                    print(f"    {k}: {len(v)} item(s)")
                    for item in v[:3]:
                        print(f"      - {item}")
                    if len(v) > 3:
                        print(f"      ... and {len(v) - 3} more")
                elif isinstance(v, int):
                    print(f"    {k}: {v}")
                elif isinstance(v, str):
                    print(f"    {k}: {v}")
        print(f"\n=== Summary: {n_pass} pass, {n_fail} fail (out of {len(results)} checks) ===")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
