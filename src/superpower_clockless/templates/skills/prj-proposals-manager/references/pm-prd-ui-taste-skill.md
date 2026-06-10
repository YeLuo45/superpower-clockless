# PM PRD UI Design — taste-skill Reference (2026-06-10)

**For**: PM role when generating PRD documents (Step 3 of the proposal lifecycle)
**Source**: https://github.com/YeLuo45/taste-skill
**Applies to**: All PRD documents that get rendered as UI (PDF export, web display, GitHub Pages)

## Why this reference exists

PRD documents are typically generated as Markdown but rendered as UI for stakeholders. The visual quality of the rendered PRD affects:

- Readability of acceptance criteria
- Scannability of the requirements table
- Stakeholder trust in the document quality
- Consistency across multiple proposals in a project portfolio

Generic "AI-generated" PRD UIs look templated (default fonts, generic tables, no hierarchy). The `taste-skill` repo has curated anti-slop design skills that solve this.

## Recommended skill stack for PRD UI

For PM-generated PRD documents, use these 3 skills together:

### 1. minimalist-ui (primary)
**Repo path**: `YeLuo45/taste-skill/skills/minimalist-skill/`
**Why**: PRD = editorial document. Clean editorial-style interfaces with warm monochrome palette, typographic contrast, and flat bento grids are ideal for technical specs.
**Apply**: Section dividers, requirements table styling, status badges
**Don't apply**: Marketing/landing page elements (PRD isn't selling anything)

### 2. output-skill (LLM output enforcement)
**Repo path**: `YeLuo45/taste-skill/skills/output-skill/`
**Why**: LLM truncation is the #1 cause of "incomplete PRD" complaints. This skill enforces complete output, bans placeholder patterns.
**Apply**: ALWAYS for any PRD generation task — prevents `[...]`, `// TODO: continue`, premature stop
**Don't apply**: Doesn't apply to UI design, only to LLM output behavior

### 3. brandkit (optional, for project portfolio consistency)
**Repo path**: `YeLuo45/taste-skill/skills/brandkit/`
**Why**: If a project has 5+ proposals, they should share visual identity. Brandkit provides the project-level token system.
**Apply**: When generating 3+ related PRDs in a session, share typography/color tokens
**Don't apply**: One-off PRDs, no need for portfolio consistency

## PRD-specific UI patterns

When rendering PRD sections, apply these minimalist-ui patterns:

| Section | Treatment |
|---------|-----------|
| Title | Large serif, generous whitespace, single column |
| Status badges | Pill shape, muted color (gray-200/700), monospace ID |
| Requirements table | Striped rows, left-aligned text, generous padding |
| Acceptance criteria | Numbered list with checkbox icons (☐) |
| Risk register | Two-column table, severity color-coded left border |
| Decision log | Timeline-style, dates in left margin |
| Diagrams (Mermaid) | Monospace, no background, full-width |
| Code blocks | Monospace, syntax highlight, copy button top-right |

## Anti-patterns (avoid)

- ❌ Hero sections / carousels (PRD isn't marketing)
- ❌ Gradient backgrounds, glassmorphism, blur effects
- ❌ Animated transitions (PRD should be static, scannable)
- ❌ Decorative icons / emoji (signal noise)
- ❌ Color-coded paragraphs (use status badges instead)
- ❌ Aggressive marketing CTAs ("Get started!", "Try now!")
- ❌ "Designed with X" footers

## Integration with PM workflow

The PM role should:

1. **Before generating PRD**: Load the `minimist-ui` and `output-skill` skills (via skill_view)
2. **During generation**: Apply typography/table patterns from minimalist-ui
3. **After generation**: Verify output completeness via output-skill's "no truncation" check
4. **For project portfolios (3+ proposals)**: Pull brandkit tokens first, share across documents

## Concrete example

```markdown
<!-- BAD: Generic AI PRD -->
# My Feature PRD
## Overview
This is a great new feature that will help users...

## Requirements
| ID | Description |
|----|-------------|
| 1 | Must work |
| 2 | Should be fast |

## Acceptance Criteria
- Users can do X
- System handles Y
```

```markdown
<!-- GOOD: minimalist-ui PRD -->

# My Feature — Product Requirements Document

| Field      | Value                       |
|------------|----------------------------|
| Proposal   | `P-20260608-005`            |
| Owner      | coordinator                 |
| Status     | `prd_pending_confirmation`  |
| Updated    | 2026-06-10                  |

## 1. Overview

[Editorial-style intro paragraph. No marketing speak.]

## 2. Requirements

| ID    | Requirement                         | Priority | Notes       |
|-------|-------------------------------------|----------|-------------|
| REQ-1 | User authentication via OAuth 2.0   | P0       | See §4.2    |
| REQ-2 | Real-time data sync (≤ 500ms p95)   | P0       | See §4.3    |
| REQ-3 | Audit log retention ≥ 90 days       | P1       | Compliance  |

## 3. Acceptance Criteria

- [ ] Users can sign in with existing OAuth provider
- [ ] Dashboard loads within 500ms (p95) on 3G
- [ ] Audit log survives 90-day retention window
- [ ] All P0 requirements covered by automated tests

## 4. Technical Constraints

[Listed as bullets, not paragraphs]
- Latency budget: ≤ 500ms p95
- Browser support: evergreen Chrome/Firefox/Safari/Edge
- Dependency policy: no npm packages > 100KB gzipped
```

## When NOT to use taste-skill

- Internal-only design docs (no UI rendering)
- Highly technical architecture documents (use diagrams + tables, not editorial style)
- Compliance/regulatory filings (follow that document's template)
- Slides / presentations (different design system)

## See also

- `https://github.com/YeLuo45/taste-skill` — upstream skill repo
- `references/mcp-aisp-cli.md` — how PM uses mcp_aisp.py to update proposal fields
- ai-superpower SKILL.md § "数据源" — where PRD paths are stored