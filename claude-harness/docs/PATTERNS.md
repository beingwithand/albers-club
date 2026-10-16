# Pattern layers (v1, 2026-10-16)

This is meta-level thinking: it looks at patterns at several layers. The code is `scripts/patterns.py`, the
workflow is `skills/pattern-review` (run from `review-week`), and the records are the `Pattern`, `Encoding` and
`MetaPattern` types in `schema/ontology.yaml`.

## Layers (`pattern_level`)

| Level | What | Record | Where |
|---|---|---|---|
| L0 observation | raw events: prompts, corrections, mishaps, decisions, outcomes, tool blocks | Event | `$HARNESS_DATA/log/*.jsonl` |
| L1 episode | an event merged with its newest `label` (intent/situation/meta/labels); also project mishaps/decisions and built-in evidence | (derived) | in memory |
| L2 pattern | a regularity across 2 or more episodes. Kinds: request, preference, workflow, mistake, success, correction, temporal, domain-analogy, tool-friction | Pattern `pat_` | `patterns/patterns.jsonl` |
| L3 encoding | the artifact that operationalizes a pattern. Kinds: skill, command, hook, rule, agent, rubric-criterion, eval-task, default-setting, saved-workflow | Encoding `enc_` (`encodes` → Pattern) | `patterns/encodings.jsonl` |
| L4 principle | a cross-domain generalization of 2 or more L2/L3 items across 2 or more areas | Principle `P<n>` (`patterns` → Pattern) | `global/PRINCIPLES.md` |
| L5 meta-pattern | a pattern about the pattern system itself. It proposes changes to the ontology, mining, thresholds, cadence, encodings or principles | MetaPattern `mp_` (`about` → any) | `patterns/meta.jsonl` |

**Provenance runs all the way down:**
- Every Pattern lists its `evidence`: event ids, `mishap:<project>#n`, `insights:<n>`, `auto-memory:<path>`
  or `session-note:<ref>`. Its `sources` use the enum `log|label|mishap|decision|insights|usage|skill-doctor|auto-memory|session-note`.
- Every Encoding lists the patterns it `encodes`.
- Every principle names its patterns.

`abstraction_level` and `convergence` are deliberately not declared yet. They are a separate axis, orthogonal
to `pattern_level`.

## Lifecycle (`pattern_status`)

`candidate → proposed → approved → encoded`. Any of these can become `decaying` and then `retired`.
`encoded` becomes `reopened` when the encoding fails, and is re-encoded after that. The stores are append-only,
and the newest line per id wins. **Every transition is a proposal.** `ladder` and `meta` only print them;
`record` writes what the user approved and logs a `pattern_proposed`, `pattern_promoted` or `pattern_retired`
event.

| Rule | Default (`$HARNESS_DATA/patterns/config.json`) |
|---|---|
| mined candidate | ≥ 2 episodes in the last 12 weeks; joins a cluster on the same `kind_of_thing` or Dice ≥ 0.4 |
| candidate → proposed | support ≥ 3, sessions ≥ 2, last seen ≤ 8 weeks, confidence ≥ 0.45 |
| approved → L3 proposal | support ≥ 4, sessions ≥ 3, confidence ≥ 0.6. For mistake, correction and tool-friction: support ≥ 2 and sessions ≥ 2. Runs `eval_gate.py` if `evals/<area>/tasks` exists, otherwise `ungated` |
| L4 proposal | ≥ 2 approved/encoded patterns that share keywords (Dice ≥ 0.25) across ≥ 2 areas and have no principle yet |
| decay | approved/encoded with no support for 6 weeks, or a skill/command unused for 6 weeks (or reported with 0 invocations by /skill-doctor). Mistake, correction and tool-friction patterns that go quiet after encoding are **working**, so they do not decay |
| retire | decaying for 6 more weeks |
| reopen | 2 or more new mistake/correction episodes after the encoding, or the encoding overridden 2 or more times (label `override:<enc id>`) |
| review principle | a linked pattern reopened or retired, or episodes labelled `contradicts:P<n>` |

Confidence is `support/(support+2) × (0.5 + 0.5·min(1, sessions/3))`, halved when the pattern was last seen
more than `decay_weeks` ago.

## L5 signals (`meta_signal`)

- **reoccurrence-after-encoding:** an encoding failed to stop its pattern. If 2 or more encodings of one kind
  fail, propose a stronger kind (for example rule → hook).
- **encoding-overridden:** an encoding was overridden repeatedly.
- **encoding-unused:** /skill-doctor reports 0 invocations for an encoding.
- **correction-hotspot:** one area produces 40% or more of the corrections. Review it first and grow its eval set.
- **preference-drift:** opposite words on the same topic, older vs newer.
- **blind-spot:** an area with no episodes.
- **principle-conflict:** keyword opposition plus a shared topic between two principles.
- **kind-concentration:** one theme in half or more of the live patterns. Propose a principle family.
- **unclassified-share:** corrections that join no pattern. The labels or kinds are missing something.
- **label-gap:** most episodes are unlabeled. Change the cadence.

## Built-ins: Claude Code inputs and outputs (verified 2026-10-16)

Claude Code has **no official "repeated task → skill" recommender**; this system fills that gap. It uses the
built-ins below as inputs and outputs and does not reimplement them:

- **`/insights`** writes `~/.claude/usage-data/report.html`, an analysis of up to 200 recent local sessions
  (what you work on, friction points, suggestions). pattern-review paraphrases its friction points and repeated
  items into `--external` JSONL with `source: insights`. The reports are deleted after `cleanupPeriodDays`, so
  record what matters.
- **`/usage`** (press `w` for 7 days) attributes usage to skills, subagents, plugins and MCP. It is evidence for
  temporal, tool-friction and cost patterns, and for L5 (which encodings are expensive).
- **`/skill-doctor`** gives per-skill invocation counts and context cost, and flags skills that were never
  invoked. It is the main input for encoding decay and `encoding-unused`.
- **`/doctor`** and **`/doctor prompt-audit [path]`** audit CLAUDE.md and skills for outdated or conflicting
  instructions, and offer to move procedures into skills. pattern-review runs this as its L3/L4 hygiene step.
- **Auto memory:** `~/.claude/projects/<project>/memory/` holds notes of type user, feedback, project or
  reference, indexed by `MEMORY.md`. `feedback` notes (corrections and confirmed approaches) are read with
  `--auto-memory` as correction or preference evidence.
- **skill-creator plugin** (`/plugin install skill-creator@claude-plugins-official`) handles evals.json, A/B
  runs and description tuning. Use it to build and tune L3 skill encodings; `claude plugin eval` can gate them.
- **"You should know" mod** (`/plugin enable cc-plugin-you-should-know@builtin`) is off by default and has a
  background token cost. It is an optional live signal of silent tradeoffs.
- **Workflows:** `/workflows` → `s` saves a dynamic workflow as a command. That is the L3 kind `saved-workflow`.

## In-session

`global/CLAUDE.md` tells Claude to notice repeated requests and corrections during a session and to offer to log
them as pattern candidates. `retro` turns a session's repeats into L1→L2 seeds. The repo's
`patterns/seed_patterns.jsonl` holds the patterns already evidenced on 2026-10-16.
