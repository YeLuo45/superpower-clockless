# Multi-Agent Roster Completeness (2026-06-12)

## Why this exists

When designing a multi-agent extension of prj-proposals-manager (e.g.
`ma-prj-proposal-manager`), it is tempting to copy the implicit 5 roles from
the skill's own description (Coordinator / PM / Dev / Test Expert / Research
Analyst) and stop there. **This misses stages** that already exist in the
ai-superpower state machine but have no agent owner.

Boss caught me on 2026-06-12 with the question **"为什么缺少市场研究 agent"**.
The state machine has `research_direction_pending` and `ideation` as legitimate
stages, but no agent in the original 5-role set owns them. v1.1.0 of
ma-prj-proposal-manager added `market_research` and `designer` to fill the
gaps.

## The rule

**Before writing `agents.yaml` or any "agent → stage" mapping, enumerate the
full ai-superpower state machine and assign an owner to every stage.**

```bash
grep -A 10 "VALID_PROPOSAL_STATUSES" /home/hermes/ai-superpower/src/ai_superpower/models.py
grep -A 10 "VALID_PROPOSAL_STAGES"   /home/hermes/ai-superpower/src/ai_superpower/models.py
```

Any stage with no owner = a missing agent.

## The 7-agent minimum complete set (v1.1.0 verified)

| # | Agent | Icon | Scope (status) |
|---|---|---|---|
| 1 | **market_research** | 🔍 | `research_direction_pending`, `research` |
| 2 | **coordinator**    | 🧭 | `intake` |
| 3 | **designer**       | 💡 | `ideation` |
| 4 | **pm**             | 📋 | `clarifying`, `prd_pending_confirmation` |
| 5 | **dev**            | 🛠️ | `in_tdd_test`, `in_dev` |
| 6 | **test**           | 🧪 | `in_test_acceptance`, `test_failed` |
| 7 | **boss**           | 👑 | `accepted`, `needs_revision`, `deployed`, `delivered` |

Reference implementation:
- `/home/hermes/projects/ma-prj-proposal-manager/config/agents.yaml`
- `/home/hermes/projects/ma-prj-proposal-manager/src/hooks/useAgentRoster.js` (DEFAULT_ROSTER)

## Workflow that produces this

```
1. Read ai-superpower state machine enums
2. Tabulate every status + every stage
3. For each stage, decide: "is this naturally owned by one of the 5 default
   roles, or does it need a new agent?"
4. If new agent needed → add to roster with icon + color + scope
5. Verify every stage has exactly one owner
6. Build tests covering agentForStage for every status
```

## Why 5 was the wrong default

The 5 implicit roles in the skill's description (Coordinator / PM / Dev / Test
Expert / Research Analyst) were:

- Coordinator — `intake`, `clarifying` (overloaded)
- PM — `prd_pending_confirmation`
- Dev — `in_dev`
- Test — `in_test_acceptance`
- Boss — `accepted`, `delivered`

The blind spots:
- `research_direction_pending` and `research` — silently had no agent
- `ideation` — silently had no agent
- `in_tdd_test` — silently had no agent (folded into "dev" only by luck)
- `needs_revision` — silently had no agent (folded into "boss" only by luck)

The fix is the table above, not adding "more" agents — the right answer was to
**redistribute** `clarifying` from coordinator to pm, and to recognize
`market_research` + `designer` as their own roles.

## Lessons for future roster design

- **Never trust a doc's character list as the source of truth** for an agent
  system. The state machine is.
- **Boss will catch missing agents fast** because they show up as "no owner"
  badges in the per-agent dashboard.
- **5-agent minimalism is wrong** for any non-trivial project. 7 is the floor
  when the state machine has explicit research + ideation phases.
- **The same lesson applies to any state machine** — the 7-agent pattern
  generalizes: list states → assign owners → verify coverage.
