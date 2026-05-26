# Superpower Clockless

This agent is wired to the ai-superpower API engine and the prj-proposals-manager lifecycle skill.

Core rules:
- All proposal/project data operations go through ai-superpower API or CLI.
- Do not directly edit CSV data files.
- Use proposal lifecycle states and acceptance gates from prj-proposals-manager.
- Prefer `AI_SUPERPOWER_API_KEY` from the environment.

Default local API: `http://127.0.0.1:8000`
