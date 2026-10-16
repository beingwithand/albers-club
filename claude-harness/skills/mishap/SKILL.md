---
name: mishap
description: Log a mistake that was noticed and fixed (by the agent or the user) with root cause, prevention and proof, so it is not repeated. Use immediately after any self-correction or when the user points out an error.
---

# Mishap log

Append to `log/mishaps.md` in the project (create it if missing) and append a `mishap` event to the log.

```markdown
## <YYYY-MM-DD HH:MM> <short title>
- **Intent at the time:** what we were trying to do
- **What happened:**
- **How it was noticed:** self-check | verifier | user | test
- **Fix:** (link to diff/commit)
- **Root cause:** be specific; "careless" is not a root cause
- **Prevention (proposed):** rule | check | hook | skill change, plus where it should live (global/project)
- **Repeat pattern:** if the fix revealed a reusable technique
- **Generalizes to:** global | <area> | this project only
- **Proof:** output, test or diff
- **Status:** proposed
```

Do **not** edit CLAUDE.md or rules directly. Proposals are reviewed in `/retro` or the weekly review.
