# OpenSpec Integration

OpenSpec (`https://github.com/YeLuo45/OpenSpec`) is a spec-driven development framework. The proposal system integrates with OpenSpec to generate project specs from accepted proposals or initialize specs for legacy projects.

## Authoritative Reference

- **Repo**: https://github.com/YeLuo45/OpenSpec
- **Schema**: `schemas/spec-driven/schema.yaml` (v1)
- **Templates**: `schemas/spec-driven/templates/{proposal,spec,design,tasks}.md`
- **Real-world examples**: `openspec/changes/<change-name>/` in the OpenSpec repo

## Real OpenSpec Directory Structure

OpenSpec output lives at `<project-root>/openspec/changes/<change-name>/`:

```
<project-root>/openspec/changes/<YYYY-MM-DD>-<slug>/
├── .openspec.yaml             # schema: spec-driven, created: YYYY-MM-DD
├── proposal.md                # Why / What Changes / Capabilities (New + Modified) / Impact
├── design.md                  # Context / Goals+Non-Goals / Decisions / Risks+Trade-offs
├── tasks.md                   # ## N. <Group> / - [ ] N.M <task>
└── specs/
    └── <capability-name>/
        └── spec.md            # ## ADDED Requirements / ### Requirement: <name>
                               #   #### Scenario: <name> / - **WHEN** / - **THEN**
```

For the OpenSpec project itself, `<project-root>/openspec/changes/...` is the OpenSpec repo's own spec dir.

## .openspec.yaml Format

Minimal (real OpenSpec):
```yaml
schema: spec-driven
created: 2026-02-20
```

prj-proposals-manager extension (for traceability):
```yaml
schema: spec-driven
created: 2026-06-13
proposal: PRJ-20260417-001   # from accepted-proposal mode
# OR
init: true                    # from init mode (bootstrap for legacy project)
```

## proposal.md Sections (in order)

| Section | Source | Required |
|---------|--------|----------|
| `## Why` | PRD 背景与目标 / 背景 / Why | yes |
| `## What Changes` | PRD 功能需求 / What Changes | yes |
| `## Capabilities` → `### New Capabilities` | PRD functional requirements `### N. <name>` headers | yes |
| `## Capabilities` → `### Modified Capabilities` | PRD 修改的功能 section (if present) | no |
| `## Impact` | PRD 影响 / Impact | yes |

**Capabilities contract**: Each capability listed in `New Capabilities` MUST have a corresponding `specs/<capability>/spec.md` file. The capability name becomes the directory name (kebab-case, no backticks, normalized).

## design.md Sections (in order)

| Section | Source |
|---------|--------|
| `## Context` | tech-solution 背景 / Context / 概述 (or PRD-derivation) |
| `## Goals / Non-Goals` | tech-solution 目标 / 非目标 / Goals / Non-Goals |
| `## Decisions` | tech-solution 技术决策 / 方案 / Decisions |
| `## Risks / Trade-offs` | tech-solution 风险 / Risks |

If no tech-solution.md exists, design.md is generated from PRD's 背景/功能需求 sections as fallback.

## tasks.md Format

```markdown
## 1. <Group Name>

- [ ] 1.1 <task description>
- [ ] 1.2 <task description>

## 2. <Group Name>

- [ ] 2.1 <task description>
```

Source order: PRD 实施计划 / Implementation Plan / Steps / Tasks (first found) → fallback to synthesized from 功能需求.

## specs/<capability>/spec.md Format

```markdown
## ADDED Requirements

### Requirement: <Name>

<requirement text — use SHALL for normative>

#### Scenario: <Scenario Name>

- **WHEN** <condition>
- **THEN** <expected outcome>
```

**Critical** (from OpenSpec schema.yaml):
- 4 hashtags for `#### Scenario:` (3 hashtags fails silently)
- Each Requirement MUST have at least one Scenario
- SHALL/MUST for normative, avoid should/may

## generate-spec.py — Two Modes

The `scripts/generate-spec.py` script (in this skill's scripts/) handles both modes.

### Mode 1: From Accepted Proposal

**Input**: PRD + tech-solution from `workspace-pm/proposals/{project_id}/`

**Output**: `workspace-dev/proposals/{project_name}/openspec/changes/{today}-{slug}/`

```bash
# Generate SPEC from a project's PRD/tech-solution
python3 scripts/generate-spec.py PRJ-20260417-001

# Preview without writing files
python3 scripts/generate-spec.py PRJ-20260417-001 --dry-run
```

**Trigger**: After proposal acceptance (status: `accepted` or `delivered` in Step 9/11 of workflow)

**Data extracted**:
- Project name: from `proposals.csv` (project_name field) or PRD frontmatter
- PRD: latest `*-prd.md` in `workspace-pm/proposals/{project_id}/`
- Tech solution: latest `*-tech-solution.md` in same dir (optional; PRD fallback)
- Capabilities: regex extraction from `### N. <name> — <desc>` patterns under `## 功能需求`
- Requirements: one spec per capability (kebab-case normalized, deduped)
- Tasks: from `## 实施计划` or synthesized from `## 功能需求`

### Mode 2: Init for Existing Projects

**Input**: README.md / SPEC.md in `workspace-dev/proposals/{project_name}/` (no proposal exists)

**Output**: Same `<project-root>/openspec/changes/{today}-init-{slug}/` with template-only content

```bash
# Init a single project
python3 scripts/generate-spec.py --init openspec --name "OpenSpec Design"

# Preview only
python3 scripts/generate-spec.py --init openspec --dry-run

# Batch init all projects without openspec/
python3 scripts/generate-spec.py --init-all
python3 scripts/generate-spec.py --init-all --dry-run
```

**Trigger**: For legacy projects without proposals; bootstrap minimal SPEC for review

**Data extracted**:
- Name: first `# heading` from README.md
- Description: first non-heading paragraph
- Sections: template placeholders (to be filled in by reviewer)

## Key Decisions (2026-06-13)

1. **Output path**: `<project>/openspec/changes/<change>/` (not `SPEC/`) — matches real OpenSpec repo structure
2. **For OpenSpec project**: `<OpenSpec-repo>/openspec/changes/<change>/` (one less level)
3. **Capability naming**: kebab-case, no backticks, dedupe by normalized name to prevent spec.md overwrites
4. **Modified Capabilities**: only emitted when PRD has explicit `## 修改的功能` section (avoid duplication with New)
5. **Init mode**: uses template-only content (no PRD to derive from); user fills in placeholders
6. **Existing `SPEC.md`**: NOT moved — init creates parallel `openspec/changes/<init>/` dir

## Common Pitfalls (Real OpenSpec)

| Issue | Prevention |
|-------|------------|
| `#### Scenario` with 3 hashtags | Always use exactly 4 (`####`) |
| Empty Scenario list | Each Requirement MUST have ≥1 Scenario |
| Capability not in `specs/` | Each New Capability name = `specs/<name>/spec.md` directory |
| `should`/`may` in requirements | Use SHALL/MUST for normative behavior |
| Modified requirements with partial content | Copy ENTIRE requirement block, then edit |
| Multiple `### Requirement:` in one spec | Each scenario tied to its parent requirement |
