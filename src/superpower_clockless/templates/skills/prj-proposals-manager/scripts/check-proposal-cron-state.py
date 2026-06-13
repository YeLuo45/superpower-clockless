#!/usr/bin/env python3
"""
check-proposal-cron-state.py — One-shot diagnostic for cron-fire proposals.

Consolidates the 5-step recipe from
references/cron-misconfigured-recurring-timeout.md into a single script.

Usage:
    python3 check-proposal-cron-state.py P-YYYYMMDD-XXX [--target-keys k1,k2,...]
Output: structured stdout that maps directly to a [DONE] cron response.

Exit codes:
    0 = data layer already correct (DONE)
    1 = data layer needs action (caller should perform the update)
    2 = proposal not found in ai-superpower
    3 = ai-superpower CSV missing or unreachable

v5 update (2026-06-08, revised 2026-06-13): This script's logic still works (data is source of truth,
skip writes when correct), but it currently reads `proposals.json` (v4 mirror).
v5 verification should use `mcp_aisp.py get-proposal --proposal-id P-...` (MCP, via unified CLI) or
grep ai-superpower's `~/.ai-superpower/proposals.csv` directly. Future versions
of this script will use MCP. For now, the recipe in
`references/cron-misconfigured-recurring-timeout.md` has the v5 verification path.
The script's continued use of urllib for cron diagnostics is the documented
exception to the "MCP-only" rule (see SKILL.md § "Emergency: REST API").
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

PROPOSALS_ROOT = Path("/home/hermes/proposals")
JSON_PATH = PROPOSALS_ROOT / "proposals.json"
CSV_PATH = PROPOSALS_ROOT / "proposals.csv"
INDEX_PATH = PROPOSALS_ROOT / "proposal-index.md"
CRON_JOBS_PATH = Path("/home/hermes/.hermes/cron/jobs.json")
CRON_OUTPUT_ROOT = Path("/home/hermes/.hermes/cron/output")

# Canonical target field set for a tech-confirm timeout-approved pattern
DEFAULT_TARGET_KEYS = [
    "tech_expectations",
    "technical_expectations",
    "tech_expectations_timeout_resolution",
    "technical_expectations_timeout_resolution",
    "current_status",
    "stage",
    "status",
    "tech_stack",
    "technical_stack",
]


def load_proposals_json() -> dict | None:
    if not JSON_PATH.exists():
        return None
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR] Failed to read {JSON_PATH}: {e}", file=sys.stderr)
        return None


def find_proposal(data: dict, proposal_id: str) -> dict | None:
    """proposals.json uses a project-centric nested structure."""
    for project in data.get("projects", []):
        for p in project.get("proposals", []):
            if p.get("id") == proposal_id:
                return p
    return None


def check_data_layer(proposal: dict, target_keys: list[str]) -> tuple[bool, list[str]]:
    """Returns (all_correct, missing_or_wrong_keys)."""
    issues = []
    for key in target_keys:
        val = proposal.get(key)
        if val is None or val == "" or val == "pending":
            issues.append(f"{key}={val!r}")
    return (len(issues) == 0, issues)


def check_cron_misconfiguration(proposal_id: str) -> list[dict]:
    """Inspect cron jobs referencing the proposal; report misconfigured ones."""
    if not CRON_JOBS_PATH.exists():
        return []
    try:
        jobs = json.loads(CRON_JOBS_PATH.read_text(encoding="utf-8")).get("jobs", [])
    except (json.JSONDecodeError, OSError):
        return []
    relevant = [j for j in jobs if proposal_id in json.dumps(j, ensure_ascii=False)]
    out = []
    for j in relevant:
        sched = j.get("schedule", {}) or {}
        expr = sched.get("expr", "?")
        kind = sched.get("kind", "?")
        enabled = j.get("enabled", "?")
        job_id = j.get("id", "?")
        # Count output log files
        log_dir = CRON_OUTPUT_ROOT / job_id
        log_count = len(list(log_dir.iterdir())) if log_dir.is_dir() else 0
        out.append(
            {
                "id": job_id,
                "name": j.get("name", "?"),
                "schedule_expr": expr,
                "schedule_kind": kind,
                "enabled": enabled,
                "log_count": log_count,
                "is_misconfigured": (
                    kind == "cron"
                    and expr.startswith("*/")
                    and log_count > 3
                    and enabled is True
                ),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal_id", help="e.g. P-20260502-017")
    parser.add_argument(
        "--target-keys",
        default=",".join(DEFAULT_TARGET_KEYS),
        help="Comma-separated field names to verify (default: tech-confirm set)",
    )
    args = parser.parse_args()
    target_keys = [k.strip() for k in args.target_keys.split(",") if k.strip()]

    report = {
        "proposal_id": args.proposal_id,
        "paths": {
            "proposals_json": str(JSON_PATH),
            "proposals_json_exists": JSON_PATH.exists(),
            "proposal_index": str(INDEX_PATH),
            "proposal_index_exists": INDEX_PATH.exists(),
        },
        "data_layer": None,
        "cron": [],
        "verdict": None,
    }

    data = load_proposals_json()
    if data is None:
        report["verdict"] = "ERROR: proposals.json unreadable"
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 3

    proposal = find_proposal(data, args.proposal_id)
    if proposal is None:
        report["verdict"] = (
            f"NOT_FOUND: {args.proposal_id} not in proposals.json (ghost proposal?)"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    all_correct, issues = check_data_layer(proposal, target_keys)
    report["data_layer"] = {
        "found": True,
        "title": proposal.get("title", ""),
        "stage": proposal.get("stage", ""),
        "status": proposal.get("status", ""),
        "current_status": proposal.get("current_status", ""),
        "all_target_keys_correct": all_correct,
        "issues": issues,
    }

    cron_info = check_cron_misconfiguration(args.proposal_id)
    report["cron"] = cron_info

    if all_correct:
        misconfigured = [c for c in cron_info if c["is_misconfigured"]]
        if misconfigured:
            report["verdict"] = (
                f"DONE_AT_DATA_LAYER: all target fields correct in proposals.json. "
                f"⚠️ {len(misconfigured)} cron job(s) misconfigured (recurring, see cron[].id)."
            )
        else:
            report["verdict"] = "DONE_AT_DATA_LAYER: all target fields correct."
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    else:
        report["verdict"] = (
            f"NEEDS_ACTION: {len(issues)} field(s) not at target: {', '.join(issues)}"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
