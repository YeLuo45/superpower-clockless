# Multi-Agent Variant Pattern (2026-06-11)

**Reference implementation**: https://github.com/YeLuo45/ma-prj-proposal-manager

This reference describes how to extend the `prj-proposals-manager` single-agent SPA into a multi-agent UI. The same pattern works for any workflow skill where:
- A primary data record (e.g. proposal) carries a stage and an owner
- Multiple roles participate in the lifecycle (intake → clarify → PRD → dev → test → deliver)
- The system has an audit log of who-did-what

## When to use

Build a `ma-*` variant when:

| Signal | Why it matters |
|---|---|
| The workflow has 3+ distinct roles (coordinator, pm, dev, test, boss) | Per-role views prevent the "every agent sees everything" problem |
| Each role owns specific stages | Lets you filter by stage scope → assign queue without database queries |
| You need to show "who has touched this proposal" | The audit log is the source of truth for handoffs |
| Boss wants oversight but agents want focus | Agent-aware dashboard gives each role their own queue + cross-role visibility |

If the workflow has only one role or no audit log, the pattern doesn't add value — stick with the base skill.

## The 5 components of a multi-agent variant

### 1. Agent roster (config + hook)

A list of agents, each with: `id, name, role, icon, color, description, scope[], initials`. `scope` is the array of stages this agent owns.

**Three-source resolution** (priority order):
1. `localStorage('ma_agent_roster')` — admin-edited JSON override
2. `/config/agents.yaml` — bundled defaults (fetched at runtime)
3. Inline `DEFAULT_ROSTER` — hardcoded fallback

This lets users customize without redeploying.

Default roster for prj-proposals-manager:

```yaml
- { id: coordinator, role: coordinator, scope: [intake, clarifying],    icon: 🧭, color: '#3b82f6' }
- { id: pm,         role: pm,         scope: [prd_pending_confirmation], icon: 📋, color: '#8b5cf6' }
- { id: dev,        role: dev,        scope: [in_dev],                   icon: 🛠️, color: '#10b981' }
- { id: test,       role: test,       scope: [in_test_acceptance, test_failed], icon: 🧪, color: '#f59e0b' }
- { id: boss,       role: boss,       scope: [accepted, deployed, delivered],    icon: 👑, color: '#ef4444' }
```

### 2. Two new routes

```jsx
<Route path="/agents" element={<Agents />} />             {/* roster grid */}
<Route path="/agents/:agentId" element={<AgentDashboard />} />  {/* per-agent queue */}
```

`/agents` shows all agents in a card grid with their current queue size. `/agents/:id` shows the filtered queue for one agent.

### 3. Agent-aware queue filter

A proposal belongs to agent `X` if:
- `proposal.stage ∈ agent.scope`, **OR**
- `proposal.owner.toLowerCase() === agent.name.toLowerCase()` (manual override)
- `proposal.owner.toLowerCase() === agent.id` (short form)

```js
const isAgentQueue = (proposal, agent) => {
  const stage = proposal.stage || proposal.status;
  const owner = (proposal.owner || '').toLowerCase();
  return (agent.scope || []).includes(stage)
    || owner === agent.name.toLowerCase()
    || owner === agent.id;
};
```

### 4. Handoff timeline component

Reconstructs the chain of agents who touched a proposal from the audit log:

```jsx
function AgentHandoffTimeline({ proposalId }) {
  const { handoffs } = useHandoffs(proposalId);
  // Each handoff: { ts, op, field, old, new, actor }
  // Render as vertical timeline with avatar per actor
}
```

`useHandoffs` calls MCP `get_audit` with `entity='proposal'`, filters by `id=proposalId`, sorts by `ts`.

### 5. Generic MCP caller (extended `useMcp`)

The base `useMcp` only exposes domain-specific methods. The multi-agent variant adds:

```js
const call = useCallback(async (toolName, args = {}) => {
  return withClient(async (client) =>
    await client.callTool({ name: toolName, arguments: args })
  );
}, [withClient]);

const getAudit = useCallback((filter) => call('get_audit', filter), [call]);
```

This lets the handoff component reach `get_audit` without writing a new method per tool.

## File structure delta

When forking `prj-proposals-manager` into `ma-prj-proposal-manager`:

```
ma-prj-proposal-manager/
├── config/agents.yaml              # NEW: default roster
├── public/config/agents.yaml        # NEW: served at /config/agents.yaml
├── src/hooks/
│   ├── useAgentRoster.js           # NEW: 3-source roster loader
│   ├── useHandoffs.js              # NEW: audit log → handoff chain
│   └── useMcp.js                   # +5 lines: call(), getAudit(), helpers
├── src/components/
│   ├── AgentRoster.jsx             # NEW: card grid
│   └── AgentHandoffTimeline.jsx    # NEW: vertical timeline
├── src/pages/
│   ├── Agents.jsx                  # NEW: /agents page
│   └── AgentDashboard.jsx          # NEW: /agents/:id page
└── src/App.jsx                      # +2 Route entries
```

That's it. ~600 lines of new code, all additive. Original `/` and `/project/:id` routes unchanged.

## Tests (vitest, ~30 tests)

The pattern typically needs:

| Test | What it covers |
|---|---|
| `useAgentRoster.test.js` | 3-source fallback, localStorage override, saveRoster/resetRoster, agentForStage lookup |
| `useHandoffs.test.js` | `deriveActorList` collapse logic, missing actor handling, empty input |
| `AgentRoster.test.jsx` | Empty state, multi-card render, queue count display |
| `AgentHandoffTimeline.test.jsx` | (optional) Renders audit entries with correct agent colors |

Total ~25-30 tests, all under 1s per file.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| `act(...) is not supported in production builds of React` | Run with `NODE_ENV=test npx vitest run` (NOT plain `npx vitest run`) |
| `npm install` omits dev dependencies | `NODE_ENV=development npm install --include=dev` |
| `useMcp` test mocks production build | Same `NODE_ENV=test` fix as above |
| `fetch('/config/agents.yaml')` 404 in dev | Place file in `public/config/`, not `config/` (Vite serves `public/` at root) |
| Agent for "unknown" stage | `agentForStage` returns `null` — handle in UI ("no owner") |
| Audit log too large | Paginate with `get_audit({page, page_size})` — don't load all |

## Pattern: "useAgentRoster + useMcp extension"

The two hooks together form a generic multi-agent pattern:

```js
// In any new component:
const { roster, agentForStage, agentById } = useAgentRoster();
const mcp = useMcp();  // extended with call()

// Per-agent view:
const agent = agentById('pm');
const proposals = (await mcp.call('list_proposals', {})).items
  .filter(p => (agent.scope || []).includes(p.stage));
```

This works for any agent-aware dashboard beyond the proposal lifecycle.

## When NOT to do this

- Single-role workflow (no real benefit)
- No audit log (handoff timeline can't be reconstructed)
- Workflow has 1-2 stages (overkill)
- Users need role-switching, not role-filtering (build a multi-tenant app instead)

## See also

- ma-prj-proposal-manager: https://github.com/YeLuo45/ma-prj-proposal-manager
- `references/mcp-aisp-cli.md` — agent-side CLI for the same MCP backend
- `references/duplicate-project-workflow.md` — another v5.0.0 feature
- ai-superpower SKILL.md § "MCP 工具" — list of all 20 MCP tools
