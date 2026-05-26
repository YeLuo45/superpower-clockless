# OpenSpec Integration

OpenSpec (`https://github.com/YeLuo45/OpenSpec`) is a spec-driven development framework. The proposal system integrates with OpenSpec to generate project specs from accepted proposals or initialize specs for legacy projects.

## OpenSpec Schema

The `spec-driven` schema templates live at `schemas/spec-driven/templates/` in the OpenSpec repo:

| File | Purpose |
|------|---------|
| `proposal.md` | Why/What/Capabilities/Impact |
| `spec.md` | Requirements + GHERKIN scenarios |
| `design.md` | Context/Goals/Decisions/Risks |
| `tasks.md` | Implementation checklist |

## Two Modes of SPEC Generation

### 1. From Accepted Proposal (`generate-spec.py <project_id>`)

**Input**: PRD and tech-solution from `workspace-pm/proposals/{project_id}/`

**Output**: `workspace-dev/proposals/{project_name}/SPEC/`
```
├── proposal.md        # Why/What/Capabilities/Impact (from PRD)
├── spec.md           # Requirements + GHERKIN scenarios
├── design.md         # Context/Goals/Decisions/Risks (from tech solution)
├── tasks.md          # Implementation checklist
└── .openspec.yaml    # Metadata (schema, project, created date)
```

**Trigger**: After proposal acceptance (Step 9 in workflow)

### 2. Init for Existing Projects (`generate-spec.py --init <project_name>`)

**Input**: README.md, existing SPEC.md in project root, or template fallback

**Output**: Same `SPEC/` directory structure

**Trigger**: For legacy projects without proposals

**Usage**:
```bash
python3 scripts/generate-spec.py --init <project_name>
python3 scripts/generate-spec.py --init ai-stock-simulation --name "AlphaTrader"
python3 scripts/generate-spec.py --init --all   # batch init all projects without SPEC
```

## Data Extraction from README

`parse_readme_for_spec()` extracts:
- Project name (from first `# heading`)
- Tagline (first non-empty line after name)
- Description (first paragraph)
- Features (bullet points under "Feature" sections)
- Tech stack (lines containing React, Vue, Node, Python, FastAPI, etc.)

## .openspec.yaml Format

```yaml
schema: spec-driven
created: 2026-05-16
project: ai-stock-simulation
# For proposal-based: proposal: PRJ-20260412-009
# For init: init: true
```

## Key Decisions (2026-05-16)

1. SPEC lives in `workspace-dev/proposals/{project}/SPEC/` (not root)
2. init mode reads from README.md first, falls back to template
3. 78 projects lacked SPEC at launch of init feature
4. Existing `SPEC.md` in project root is NOT moved — init creates parallel `SPEC/` dir