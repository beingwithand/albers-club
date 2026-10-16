---
name: fanout-plan
description: Decide whether and how wide to fan out before spawning any subagents. Classifies the task into a tier (0 inline, 1 helper, 2 small, 3 full, V verification, S map-reduce), picks pattern, width, models and token budget from docs/FANOUT.md, applies the usage budget, writes a plan block to PROGRESS.md and asks the user when required. Use before every fan-out and before verifying any client/employer-bound output.
argument-hint: "<task summary> [--client]"
---

# Fan-out plan

Task: $ARGUMENTS

The policy is in `${CLAUDE_PLUGIN_ROOT}/docs/FANOUT.md`. Read §3 to §5 there if any step below is unclear. Keep this skill quick: it should take about 5 tool calls at most.

## 1. Read the usage budget
```
python3 -I "${CLAUDE_PLUGIN_ROOT}/hooks/usage_guard.py" --fanout-budget
```
It prints JSON with these keys: `level`, `max_width`, `tier3`, `workers`, `verify_min`, `five_hour_pct`, `seven_day_pct`. The thresholds are the ones the usage guard hook uses:
- `conserve`: 5h or 7d ≥ 70%
- `ask`: 7d > 75%
- `stop`: either ≥ 90%
- `unknown`: no state, or stale state

If a `fanout_budget:` line was injected more recently in this conversation, it gives the same answer.

## 2. Classify (first match wins)
1. **Never fan out:**
   - a coupled code edit → **tier 1** (1 writer plus 1 fresh-context reviewer)
   - a quick question or one-file change → **tier 0**
   - anything that needs the full conversation context → **tier 0**
2. **Many uniform items** (more than about 10 files, contracts or segments, each handled the same way) → **tier S**: pilot 5 items, then one agent per item, ≤16 concurrent.
3. **Broad or exhaustive research or audit** → **tier 3**, 5–10 per batch. More than 10 goes through a workflow (`/deep-research`).
4. **Search needing more than about 3 sources, OR mixing source types** (papers or docs, GitHub, Reddit/HN, press) → **tier 2**, 2–4 agents. The same tier covers comparisons, a design choice with 3 angles, and debugging with 3 hypotheses.
5. **A subtask that would dump more than about 1k irrelevant tokens,** or needs distinct tools → **tier 1**.
6. **Otherwise** → **tier 0**. A quick lookup is 3–10 calls inline.

**Then, separately, the verification tier:**
- **Client- or employer-bound** (deliverable, synopsis, translation for a client, job application or cover letter, invoice, client email, or `--client`) → **tier V is mandatory.** Use 2–3 lens verifiers (fidelity, rules/requirements, language/style), run the executable checks first, and pick a judge model ≥ the producer, preferably a different one.
- **High-stakes uncertain claims** → add 3 refuters per claim.
- **Everything else** → 1 verifier (the `verify` skill).

## 3. Apply the budget
| `level` | Width | Models | Tier 3 | Tier V (client/employer) |
|---|---|---|---|---|
| normal | table width | per routing | allowed | 3 lenses (2 for short emails) |
| unknown | table width | per routing | **ask first** | 3 |
| conserve | **halve** (min 1); S ≤ 8 concurrent | **sonnet/haiku only** | allowed at 3–5 | 2 |
| ask (7d > 75%) | halve | sonnet/haiku only | **ask first** | 2 |
| stop (≥ 90%) | **0: no fan-out** | — | no | **still runs: 2 verifiers on sonnet/haiku.** Say so, and mark the verdict "reduced strength" if the producer was opus or fable |

**Ask the user before starting** (one message stating N agents, models and estimated tokens) when any of these holds:
- tier 3 with `tier3=ask`
- more than 25 agents
- more than 1.5M estimated tokens
- the plan exceeds `max_width`

Wait for a yes. If the user says no, offer the next tier down.

## 4. Estimate tokens
`est_tokens ≈ N × (35k + calls × 6k) + 10k × N`. This is rough, from FANOUT.md §6.

Call budgets:
- tier 0/1 simple: 3–10 calls
- tier 2/3 workers: 10–15 calls each
- verifiers: scoped to the criteria

## 5. Write the plan block to `PROGRESS.md` (under "In progress") before spawning
```
### Fan-out plan — <date> <task>
- tier: 2 | pattern: parallel-search | width: 3 (budget max_width=10, level=normal)
- agents: web-researcher ×3 (sonnet, same effort/tools) | calls: ≤15 each | est_tokens: ~350k
- split: papers+docs / GitHub / Reddit+HN  (boundaries: no overlap; each lists unreachable sources)
- verify: V ×3 lenses (opus) — client-bound | or: 1 verifier
- asked user: n/a | yes (<date>) — reason
- uncovered: (fill after run)
```

## 6. Hand back
Return the plan block and say "go" or "ask". When it is "ask", ask the question yourself.

The caller then:
- briefs each worker (objective, inputs as paths, output format and path, call budget, boundaries)
- runs the siblings with identical model, effort and tools
- dedupes, then verifies
- aggregates by majority or median
- lists failed workers as uncovered
- logs `fanout_tier`, `fanout_n` and `est_tokens` on the `task` event (FANOUT.md §8)
