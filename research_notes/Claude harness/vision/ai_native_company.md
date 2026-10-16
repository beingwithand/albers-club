# Albers as an AI-native company: operating model and harness changes (1 → ~5 people)

Research note, 2026-10-16. Serves `claude-harness/docs/VISION.md` goals 2 and 4 ("Albers is AI-native", "people and agents work together").

**Question.** How should Albers (albers.club: the Resonance reader app, the Canopy notes app, and freelance KO↔EN translation and annotation) run as an AI-native company? Today it is one founder who leans heavily on AI. It should grow to about 5 fully AI-native people, all working through the shared `claude-harness` plugin, with continuous RL-style improvement and explicit communication between humans, and between humans and agents.

**Deliverables in this note:**
- team structure (§3)
- rituals (§4)
- the human↔agent communication protocol (§5)
- accountability (§6)
- data boundaries and security (§7)
- an onboarding checklist (§8)
- a hiring rubric (§9)
- performance loops (§10)
- the team-level learning loop (§11)
- ontology additions (§12)
- a concrete list of harness changes (§13)
- rollout triggers (§14)

**Confidence tags** follow `fanout_policy_research.md`:
- **[H]** a primary source I read in full
- **[M]** snippets or strong secondary sources
- **[L]** blog-level or vendor marketing

**Unreachable during this run.** These hosts failed DNS (ENOTFOUND), so their claims rest on search snippets [M]: zapier.com, arxiv.org, linear.app, cerebras.ai and caseyaccidental.com. The Shape Up search returned only irrelevant results, so Shape Up is described from its well-known published method [M, from memory: verify before quoting].

---

## 0. TL;DR

1. **Agents are never accountable. A named human always is.** Copy Linear's rule: issues are *assigned* only to humans and *delegated* to agents, "because an agent cannot be held accountable" [M]. Every artifact the harness produces carries `owner: person:<id>` and `produced_by: agent:<name>@<person>`.
2. **The harness becomes the company's operating system, and its rules become org policy.** Move the marketplace to an org GitHub (`albers-club/claude-harness`). On Claude Team, deliver it through **server-managed settings** using `extraKnownMarketplaces`, `enabledPlugins`, `strictKnownMarketplaces` and `disableSideloadFlags` [H, code.claude.com/docs/en/plugins/org]. Per-group policy isn't supported from the console, so there is one org-wide config [H/M].
3. **Split everything into org, personal and client compartments.** This applies to `CLAUDE.md`, `PRINCIPLES.md`, `$HARNESS_DATA` and the vault. Personal logs stay personal. Only *derived, consented, de-identified* records flow up to the shared team learning loop. Client/NDA text never leaves its compartment.
4. **Use a written, handbook-first culture.** Decide in writing first, then announce (GitLab) [M]. Big decisions get a 2-page memo read in silence at the start of the meeting (Amazon-lite) [M]. Every decision is a `D-` record with a decider, a reversibility class and a review date.
5. **One weekly 60-minute review, with four standing segments** (§4.2):
   - outcomes and bets
   - **decision review** (decisions due for checking)
   - **pattern review** (team-level L2→L3 promotions)
   - **eval review** (gate results, regressions, cost)
6. **Shape Up-lite cadence.** Work in 6-week cycles plus a 2-week cool-down that is *the harness's own improvement sprint*. Every bet has an appetite, a human DRI and a written pitch.
7. **"Ask the human" rules become a hook-backed protocol, not etiquette.** There are 12 explicit triggers (§5.4), an `ask` record with a deadline and a default, and routing to the *owner*, not to whoever is online.
8. **Hire for verification, judgment and context engineering, not for prompt tricks.** Run a paid 3–4h AI-allowed work sample, submitted *with the transcript*. Weights: verification 30, judgment and taste 20, context engineering 20, eval design 15, communication and handoff 15. Zapier's "unacceptable" tier is the do-not-hire bar [M].
9. **Measure outcomes, verification pass rate and accepted harness contributions. Never measure tokens.** Token leaderboards were killed at Meta and Amazon over "tokenmaxxing" [M]. Analytics stay at team level and out of individual reviews. Shopify-style "AI reflexes" are expected, but they are evidenced by *artifacts*, not usage counts [M].
10. **Ontology additions (§12):**
    - types: `Member` (a person in a Party role), `Role`, `Grant`, `Ask`, `Delegation`, `Review` (the ritual record), `Consent`
    - an actor grammar: `person:<id>`, `agent:<name>@<person>`, `harness@<person>`, `service:<name>`
    - fields: `owner`, `on_behalf_of`, `visibility` and `sensitivity` on every record
    - new event types: `ask`, `ask_answered`, `handoff_accepted`, `approval`, `review`, `access_change`, `onboarding_step`

---

## 1. What 2025–2026 practice says (evidence)

| Topic | Finding | Conf. | Implication for Albers |
|---|---|---|---|
| **Baseline expectation** | Shopify memo (Lütke, Apr 2025): "Reflexive AI usage is now a baseline expectation". AI use is in performance and peer review. Teams must show AI can't do the work before asking for headcount. Prototyping starts with AI | [M] (The Logic, Ben's Bites) | Adopt the *headcount test* literally (§14). Adopt the expectation, but evidence it with artifacts rather than usage numbers |
| **Hiring bar** | Zapier AI-fluency rubric: V1 May 2025, V2 Mar 31, 2026. Tiers: Unacceptable, Capable, Adoptive, Transformative. "Unacceptable" is the bar they don't hire at, and "transformative" is under 5% of candidates. It measures mindset as much as skill | [M] (zapier.com unreachable; Zapier blog snippets) | Use the tiers as the *floor* screen and our own rubric for depth (§9) |
| **AI-allowed interviews** | Cerebras (Jul 2026) scores problem framing, verification, judgment, communication and ownership. Cadence's proposed weights: verification 40 / judgment 30 / ownership 20 / communication 10. Karat: a working solution no longer proves reasoning, so score how candidates audit model output | [L–M] (vendor blogs) | The signal is *catching the model being wrong*. Plant a defect in the exercise |
| **Accountability** | Linear: you stay the primary assignee and the agent is a contributor. "Issues can only be assigned to humans, and only delegated to agents", because an agent can't be held accountable | [M] (Linear docs and blog snippets) | The `Delegation` type, plus `owner` as a required field |
| **Accountability gap** | An arXiv paper (2608.15678) maps human responsibility onto workflow artifacts. GitHub's enterprise terms put responsibility on the customer and contain no duty to verify | [M] (arxiv unreachable) | Make accountability explicit *in the artifacts* (PR, D-record, deliverable sign-off) |
| **Securing an AI-native SDLC** | Anthropic (Jason Clinton, Jul 2026), with AI writing about 80% of merged code:<br>• single-purpose agent identities with minimum permissions<br>• boundaries on *actions*, not instructions<br>• agents talk "over the same channels as humans"<br>• secure-coding rules in CLAUDE.md and org skills, updated when a bug class is found<br>• `/security-review` before a PR<br>• narrow review agents that must "write a proof"<br>• risk tiering, with critical code under human review<br>• agents can't deploy, and "every approval is logged with the signals and reasoning"<br>• new AI reviewers run in *shadow mode* first<br>• every agent action is routed to the SIEM, treating agents as "a new type of insider threat" | [H] (claude.com blog, fetched) | Almost all of this scales down to 5 people (§6, §7). Shadow mode is the right way to introduce any new verifier or skill |
| **Anthropic internal usage** | "How Anthropic teams use Claude Code":<br>• it is the "first stop" for programming<br>• CLAUDE.md files are used for onboarding<br>• runbooks are condensed into markdown<br>• non-technical teams (legal, finance, marketing) build their own tools<br>• the most successful teams "share discoveries across technical and non-technical users" | [H] (fetched) | Non-engineers (translator, annotator) are first-class harness users and authors |
| **Anthropic internal survey** (Dec 2025; 132 people, 53 interviews) | About 27% of Claude-assisted work wouldn't have been done otherwise. People feel more "full-stack". There are concerns about **mentorship, collaboration and skill erosion**. Only 0–20% of tasks can be fully delegated | [M] (secondary coverage) | Build in no-AI reps and pairing (§10.4). Don't design for full delegation |
| **Team plan admin** | Analytics at claude.ai/analytics/claude-code:<br>• lines accepted, accept rate, DAU and sessions<br>• contribution metrics via the GitHub app (PRs labeled `claude-code-assisted`)<br>• a leaderboard and CSV export<br>The analytics API is Enterprise-only, and contribution metrics aren't available under ZDR | [H] (docs fetched) | Use team-level adoption only. **Turn the leaderboard off or ignore it** (§10) |
| **Managed plugins** | Server-managed settings (Owner role) or MDM/`managed-settings.json`. The keys are:<br>• `extraKnownMarketplaces` and `enabledPlugins` (force-enable)<br>• `strictKnownMarketplaces` (allowlist, including `{"source":"skills-dir"}`)<br>• `blockedMarketplaces`, `disableSideloadFlags`<br>• `allowManagedHooksOnly`, `strictPluginOnlyCustomization`<br>Release channels come from two marketplaces on different refs. Console settings apply to *every* user, with no per-group targeting | [H] (docs fetched) | §7.4 gives the concrete managed-settings JSON |
| **Code Review** (managed) | Team and Enterprise, running on Anthropic infrastructure. Multi-agent find → verify → rank → post. It never approves or blocks. `REVIEW.md` is read from the base branch only. Not available under ZDR, HIPAA or CMEK | [H] (docs fetched; the page no longer says "research preview", consistent with the Oct 15 GA in `recent_anthropic_updates.md`) | Turn it on for the Resonance and Canopy repos. A human merges |
| **Claude Tag (Slack)** | Beta since Jun 23, 2026 (Team/Enterprise). One Claude identity per channel, with memory scoped to configured channels. Admins choose channels, tools and token limits, and activity logs are kept. Channel work bills to the org and DMs bill to the individual | [M] | A good fit for the shared `#ops` channel *later*. Agent work then becomes visible "on the same channels as humans" |
| **Team onboarding** | `/team-onboarding` (Claude Code 2.1.101, Apr 2026) generates a ramp-up guide from 30 days of local usage, with a share link on subscription plans. Practitioners: review it before sharing, and keep durable rules in version-controlled files | [M] | Run it from the founder's account before hire #1, then curate its output into `docs/ONBOARDING.md` |
| **"Onboard everyone as an engineer"** | SuperMe (Antonov & Winters, 2026): a non-engineer gets GitHub, the repo and an AI IDE in week 1, and their tooling exposes setup gaps. Meta's bootcamp aims for a first-week ship | [M] | Every hire (translator included) gets the repo and ships one harness PR in week 1 |
| **Compounding engineering** | Every (Kieran Klaassen, Aug 2025): "each unit of engineering work should make subsequent units easier". Plan → work → review → **codify** the learnings | [M] | This is our pattern ladder (L2→L3), applied at team level (§11) |
| **Tokenmaxxing** | Meta's "Claudeonomics" board and Amazon's Kiro Rank were retired after gaming (May 2026). LeadDev 2026: 58% of orgs measure AI by tokens, and 57% of those say it's ineffective | [M] | Never rank people by usage (§10) |
| **Written culture** | GitLab: handbook as the single source of truth. "Write things down first… then announce via Slack or email". Amazon: a six-pager read silently for about 20 min at the start, deliberately not pre-sent | [M] | §5.1 and §4.2 |
| **ADRs and agents** | ADRs capture choices "future people and agents would otherwise have to rediscover". Agents make implicit structural decisions while scaffolding, with no recorded rationale | [L–M] | The verifier checks: "did this change make a decision with no `D-` record?" |
| **Small team + many agents** | Practitioner consensus: 3–7 people supervising many agents. **Human review capacity, not agent capacity, is the bottleneck.** Governance, not capability, limits solo operators | [L] | Size fan-out to *review* capacity. Each person has a review budget (§6.3) |
| **Zero Trust for Agents** | Anthropic framework (May 27, 2026): agent identity and authentication first, per-task permissions, memory-poisoning defenses, maturity levels | [M] | Per-person agent identities and capability grants (§7) |
| **NDA and AI in translation** | Agencies range from a full ban on AI/MT for subcontractors (e.g. Atlas Translations, 2024) to clause models: no cloud MT/TM/OCR, delete project TMs after delivery, no cross-client reuse (ProZ SecurePro) | [M] | Classify clients by tier (§7.3). The existing `docs/LOCAL_ONLY.md` becomes tier C2 policy |

---

## 2. Design principles for a multi-person harness

These extend `global/PRINCIPLES.md`. They are proposed and need approval through `distill-principles`.

- **T1. One accountable human per artifact.** Agents are delegates, never owners (Linear). An artifact without `owner` fails `schema_check`.
- **T2. Files, not people, are the source of truth.** A fact that lives only in someone's chat, DM or head doesn't exist. Write it first, then announce it (GitLab). This extends P11.
- **T3. Same channels for humans and agents.** Agent work is visible where human work is visible: PRs, decision records and the `#ops` thread. There are no private agent side channels for shared work (Anthropic SDLC).
- **T4. Personal by default, shared by promotion.** A person's logs, preferences and style memory are theirs. Things move up to team scope only through an explicit, evidenced, consented promotion. This mirrors the L2→L3 ladder.
- **T5. Compartments are physical, not just labels.** Client/NDA content lives in per-client compartments. Agents running there have narrower tools (no web, no cloud converters). This extends `LOCAL_ONLY.md`.
- **T6. Review capacity is the budget.** Plan delegation by *human review minutes available*, not by tokens. Fan-out that nobody can review is waste. This extends P18.
- **T7. Shadow before trust.** A new skill, verifier, rule or teammate's agent setup runs in shadow mode (it suggests, a human approves) until its eval and approval record justify autonomy (Anthropic SDLC).
- **T8. Measure outcomes, not activity** (Goodhart). Tokens, sessions and lines accepted are diagnostics, never targets.

---

## 3. Team structure (1 → ~5)

### 3.1 Roles

At 5 people a role is a *hat*, not a headcount. One person can wear several hats. Every hat has a human DRI and a default agent roster.

| Role (hat) | DRI from | Owns | Default agents (from `agents/`) | Approves |
|---|---|---|---|---|
| **Founder / operator** | day 0 (founder) | Strategy, bets, money, clients, hiring; final call on irreversible decisions | orchestrator, web-researcher, job-tracker, interviewer | `D-` records of class `irreversible`; principles; budgets |
| **Harness steward** | founder now; **rotates per cycle** from hire #2 | The plugin repo, the ontology, evals, managed settings and the release train | librarian, verifier, coder | Merges to `claude-harness` `main`; eval-gate exceptions; ontology PRs (with the founder) |
| **Product engineer** (Resonance, Canopy) | hire #1 or #2 | App code, releases, app-store presence, user feedback loop | coder, verifier, browser-operator | Code merges in the app repos (after Code Review and the tests) |
| **Language lead** (translation, annotation) | founder now; hire #1 or #2 | Client deliverables, glossaries, style guides, QA rubrics, platform accounts | translator, annotation-assistant, intake-extractor, verifier (tier V) | Client-bound deliverables (sign-off, §6.2) |
| **Growth / ops generalist** | hire #3–4 | Site (albers.club), content, support inbox, invoicing, vendor accounts | web-researcher, browser-operator, intake-extractor | Outbound comms to the public; invoices (founder co-signs above a threshold) |
| **Security / privacy officer** | founder (hat) | Access grants, offboarding, the client-tier register, incident response | (none: human only) | `Grant` records; tier C2 exceptions |

**Org shape.** The team is flat, with one founder and up to 4 hat-holders. No managers below the founder until about 8 people.

**Pairing is scheduled, not left to chance.** The Anthropic survey found that mentorship and collaboration are what AI erodes [M]. So each person has a fixed weekly 45-minute pair session with a rotating partner. One person drives and the other reviews the agent loop.

### 3.2 Humans and their agents: the "fleet" unit

- Each human runs a **personal fleet**: their Claude Code sessions, routines and subagents. These share the org plugin but have *their own* `$HARNESS_DATA`, preferences and style memory.
- **Agent identity is `agent:<name>@<person>`** (e.g. `agent:translator@p-jw`). The same agent definition run by two people produces two identities, so we can attribute behavior and compare personal configurations.
- **Shared, non-personal agents** (Code Review, a future Claude Tag channel identity, scheduled routines owned by the org) have the identity `service:<name>`. Each always has a human `owner` (§12).
- **Span of control** follows T6. One person reviews the output of at most **one tier-3 fan-out per day**, plus routine tier 0–2 work. If more is queued, the work waits or another human picks it up through a handoff (§5.3).

### 3.3 Where work lives (single source of truth)

| Thing | Lives in | Notes |
|---|---|---|
| Bets, pitches, cycle plan | `albers-ops` repo: `cycles/<YYYY>-C<n>/` | One `pitch-<slug>.md` per bet |
| Tasks | GitHub Issues in each repo (or Linear later), **assigned to a human**, with agent delegation as a label | `delegated:agent:<name>` label; `owner` = assignee |
| Decisions | `decisions.md` per project; cross-cutting ones in `albers-ops/decisions/` | `D-YYYYMMDD-n`, append-only |
| Handbook (how we work) | `albers-ops/handbook/` (this note becomes `handbook/operating-model.md`) | GitLab-style: change the handbook *first*, then announce |
| Harness | `albers-club/claude-harness` (org marketplace) | Already a plugin |
| Personal logs | each person's private `harness-data-<handle>` repo | Never read by others without a `Grant` |
| Team learning store | `albers-club/team-data` (private) | Only promoted, consented, de-identified records (§7.2) |
| Client material | per-client compartment `clients/<client-id>/` (see §7.3) | Tiered |
| Chat | Slack (or Lark): `#ops`, `#ship`, `#asks`, `#client-<id>` | Chat is for *pointers and pings*. Content lives in files |

---

## 4. Rituals

Every ritual produces a `Review` record (§12) in `albers-ops/reviews/`, so the rituals themselves are logged, labeled and improvable. Times assume one shared time zone. If people are spread out, run the async version (written pre-reads, comments closing at a set time).

### 4.1 Daily: async check-in (written, ≤5 min, no meeting)

One post per person in `#ops`. The agent drafts it from yesterday's `$HARNESS_DATA` log, and the human edits it.

```
Yesterday: <done, with proof links>   Today: <1–3 items, DRI = me>
Asks open: <ask ids, who owes what>   Blocked: <item → who/what unblocks>
Agent spend: <tier-3 runs planned today, est tokens>   Review queue: <n items waiting on me>
```
**Rule:** if your review queue has more than 5 items, you don't start new fan-outs (T6).

### 4.2 Weekly review: 60 minutes, Monday

The **pre-read** is generated on Sunday by the `team-review-week` skill (§13). It is one doc of 2 pages or fewer, read **silently for the first 10 minutes** (Amazon-lite). It isn't sent out in advance, so everyone reads the same final version.

| # | Segment | Time | Input | Output |
|---|---|---|---|---|
| 0 | Silent read | 10' | pre-read | comments inline |
| 1 | **Outcomes and bets** | 10' | cycle hill chart; shipped items with proof; client deliveries; revenue | bet status (on-track / scope-hammer / kill) |
| 2 | **Decision review** | 10' | `D-` records whose `review_date` is this week; their `expected_outcome` vs actual | each record marked `held` / `revise` / `reverse`, plus a new D- record if reversed |
| 3 | **Pattern review** (team) | 10' | each person's `pattern-review` L2 proposals with `support_people ≥ 2` | promote to team L3 (skill, rule, hook), keep personal, or reject. The steward drafts the PRs |
| 4 | **Eval review** | 10' | eval-gate runs this week: pass/regress per dimension (correctness, corrections, cost, time, style, outcome); held-out deltas; ungated proposals; verifier calibration (agreement with human sign-off) | merge / hold / revert; new eval tasks to add (from real misses) |
| 5 | **Asks, mishaps, risks** | 7' | asks overdue; mishaps with `severity ≥ medium`; access changes; usage and cost vs budget | owners and deadlines |
| 6 | Wrap | 3' | — | `Review` record written; action items as issues with human assignees |

Decisions are made in the meeting only for items already in the pre-read. Anything new becomes an `Ask` or a pitch for next week.

### 4.3 Cycle rhythm: Shape Up-lite (6 + 2 weeks) [M, from the published method]

- **Pitches** (≤2 pages):
  - problem
  - **appetite** (time budget, e.g. 2 or 6 weeks of one person plus their fleet)
  - solution sketch
  - rabbit holes
  - no-gos
  - **eval or success metric** (P5)
  - human DRI
- **Betting table** (60 min, at the end of cool-down): the founder plus the hat-holders pick bets. The cycle carries no backlog, and unpicked pitches simply expire.
- **Circuit breaker:** a bet that isn't done by the end of its appetite is stopped and re-pitched, never silently extended. This matches P17's "say the trade-off explicitly".
- **Cool-down (2 weeks) = harness sprint.**
  - Fix team-level mishaps.
  - Clear the eval backlog.
  - Retire decayed rules (`review-week` step 5).
  - Ship the harness release (stable channel).
  - Absorb SOTA updates: new Claude Code features, adopted only if they beat the evals (VISION goal 3).
  - Hold the onboarding-doc refresh.

### 4.4 Monthly (30 min): harness release and access review

- Promote `latest` to `stable` for the plugin (§7.4 release channels), with release notes listing each change and its eval evidence.
- Access review: list every `Grant`, revoke stale ones, and confirm offboarded accounts are gone. Check analytics *at team level* for adoption dips, which signal friction [H, analytics doc].

### 4.5 Quarterly (half-day): principles and operating-model review

- Run `distill-principles` across *all* members' approved patterns.
- Revisit this handbook.
- Check the decisions from the past quarter that were marked `irreversible`.
- Rotate the harness steward.

---

## 5. Communication protocol (human↔human↔agent)

### 5.1 Channel rules

1. **Write first, then announce** (GitLab). A Slack message about a decision must link the `D-` record. A message about work must link the issue or PR.
2. **Chat is ephemeral, files are durable.** Anything someone will need in a week goes to a file. The `retro` and `handoff` skills already enforce this for agents. Now it applies to humans too.
3. **Low-context by default.** Write as if the reader (human or agent) has no context: link everything, and spell out the ask, the deadline and the default. The HANDOFF cold-read test (6/6) is the quality bar for any handoff between people.
4. **Agents post in the same places as humans** (T3). Agent comments are prefixed `[agent:<name>@<person>]`. Commits carry trailers (§5.6).
5. **Response-time norms:**
   - `#asks` items marked `blocking`: same working day
   - normal asks: 2 working days
   - FYI: no reply expected
   - Tag the urgency explicitly. Don't use DMs for work.

### 5.2 Human → agent brief (any delegation, extends FANOUT §6.3)

Every non-trivial delegation (human to own agent, or human to another human's agent through a handoff) uses this block, stored in `PROGRESS.md` or the issue body:

```yaml
brief:
  owner: person:p-<handle>            # accountable human (T1)
  on_behalf_of: person:p-<handle>     # if delegated by someone else, e.g. client lead
  objective: <one sentence, outcome not activity>
  why: <intent>                       # P7
  inputs: [paths/ids]
  done_when: [criteria agreed up front]  # P9; verifier checks only these
  sensitivity: public|private|client-confidential|third-party-personal
  compartment: <client-id | none>
  budget: {tier: 0|1|2|3|V|S, est_tokens: N, review_minutes: N}
  ask_human_if: [defaults from §5.4 + task-specific]
  deadline: <date>
```

### 5.3 Human → human handoff (extends `skills/handoff` and HANDOFF.md)

The current template is session→session. Add a header and two sections so it works person→person:

```markdown
# HANDOFF: <project> — <task>
from: person:p-a   to: person:p-b   owner_after_accept: person:p-b | stays person:p-a
git_commit: … branch: … written: … by: <model/session>
sensitivity: …   compartment: …   grants_needed: [<grant ids or "none">]

## 0. What I need from you (one paragraph, the ask)
## 1–7 (unchanged: goal and intent, state with proof, decisions, dead ends, open questions, next 3 actions, verify first)
## 8. Context the files don't hold
Client mood, promises made verbally, who to call, what I'd do if I were you.
## 9. Acceptance
- [ ] cold-read by `to` (human), not only by a fresh subagent: questions answered inline
- [ ] `to` ran "Verify first" and it matched
- accepted_at: <ts>   → logs `handoff_accepted`; ownership moves only now
```

**Rules:**
- Ownership doesn't transfer until `handoff_accepted` is logged. Until then the sender is still accountable.
- The agent cold-read test (6/6) is required *before* a human handoff is sent, so the receiver's time isn't wasted.
- A handoff into a client compartment checks that the receiver has the `Grant` (§7). The hook refuses otherwise.

### 5.4 "Ask the human" rules (agent → owner)

An agent **must stop and raise an `Ask`** to its *owner* (not "whoever is online") when any of these holds. Items 1–6 already exist in `global/CLAUDE.md` and FANOUT.md. Items 7–12 are new for a team.

1. External side effects: submit, pay, send email, post publicly, apply.
2. A client- or employer-bound deliverable is ready (tier V done). Sign-off is human (§6.2).
3. A split verdict or `needs-human` from verifiers.
4. Usage is at or above 75% (7-day) before tier 3; above 25 agents or 1.5M tokens; or the usage `stop` level.
5. An irreversible or destructive operation (delete, force-push, migrate prod data, revoke access).
6. Scope ambiguity that changes the plan (interview-first, P15).
7. **Cross-owner write.** The change touches files, issues or decisions owned by *another* person. Ask that person, not your own owner.
8. **Compartment crossing.** Any content would move between compartments or sensitivity levels (e.g. using client A's glossary for client B).
9. **Contradiction with a decision record.** The plan conflicts with an `accepted` D- record. The agent must cite it and ask, never silently override.
10. **Personal data of a teammate.** Reading another member's logs, preferences or calendar without a `Grant`.
11. **Policy and harness edits.** Proposals to change rules, skills, rubrics, evals or managed settings go as PRs to the steward. They are never applied directly (already true for evals: `guard_protected.py`).
12. **Spending or commitments.** Purchases, new SaaS, new connectors, or promises of dates to clients.

**The Ask record** (§12) carries:
- `question`
- `options`, with the agent's recommendation and why
- `default_if_no_answer`, and whether the default is *safe to apply* (if it isn't, the work stays blocked)
- `deadline`
- `blocking`
- `owner_to_answer`

Asks are posted to `#asks` with a link, and the answer is logged as `ask_answered`. **A recurring ask is a pattern candidate.** If the same kind of ask is answered the same way 3 or more times, propose turning it into a rule. That is the RL loop applied to the protocol itself.

### 5.5 Decision records (extends skill `why` and the `Decision` type)

| Field | New? | Meaning |
|---|---|---|
| `decider` | new | one `person:` id (DACI "Driver/Approver" collapsed for a small team) |
| `consulted` | new | person ids, plus any `agent:` that produced the analysis |
| `class` | new | `two-way-door` (reversible: the decider alone, announce afterwards) / `one-way-door` (irreversible: memo plus a weekly-review slot, founder approves) |
| `status` | new | `proposed → accepted → held / revised / reversed / superseded` |
| `review_date` | exists | required for both classes (two-way default +6 weeks, one-way +1 cycle) |
| `expected_outcome` | exists | a checkable prediction, reviewed in §4.2 segment 2 |
| `visibility` | new | `team` / `project` / `personal` |

**Agent rule.** When the verifier finds that a diff or deliverable embodies a choice with lasting consequences (a new dependency, schema, pricing, a client-facing commitment, an architecture change) and no D- record exists, it fails the `rules` lens with "undocumented decision". This closes the "agents make implicit decisions" gap [L–M].

**When to write a memo instead.** A one-way-door decision, or anything spending more than one cycle of one person, gets a ≤2-page narrative memo (problem, options with evidence, recommendation, risks, what would change our mind). It is read silently in the weekly review. Agents may draft the memo, and the human DRI signs it.

### 5.6 Attribution in artifacts

- **Git:** every agent-assisted commit gets trailers (the harness already adds `Co-Authored-By`). Add:
  ```
  Owner: p-<handle>
  Agent: agent:<name>@p-<handle>
  Verified-By: <verification event id | none>
  Decision: D-YYYYMMDD-n (if any)
  ```
  Managed Code Review labels merged PRs `claude-code-assisted` [H]. We add our own fields because those labels carry no owner.
- **Deliverables:** the client-bound metadata sidecar (`<file>.meta.json`, *not* sent to the client) records the owner, producer agents and models, verifier lenses with verdicts, and sign-off.
- **Docs:** frontmatter has `owner:` and `produced_by:`.

---

## 6. Responsibility and accountability for agent output

### 6.1 Rules

1. **The owner answers for it**, as if they had written it themselves. "The agent did it" is never an acceptable explanation in a review, but it *is* valid root-cause data for a mishap.
2. **Mishaps are blameless toward the person and specific about the system.** Root cause goes to the layer that failed: brief, skill, rule, verifier, eval gap or human review skipped. The fix goes into the harness (Anthropic: when an agent finds a bug class, update the guidance file) [H].
3. **Verification strength scales with blast radius.** This reuses FANOUT tiers:

| Risk tier | Examples | Gate before it leaves the owner |
|---|---|---|
| R0 personal / internal draft | notes, research for yourself | self-check |
| R1 internal shared | handbook edit, harness PR, internal doc | 1 verifier plus the steward's review for harness changes |
| R2 product | Resonance/Canopy code, site | tests, managed Code Review, `/security-review`, then a **human merge** by someone other than the owner when available (until hire #1, the founder plus Code Review) |
| R3 client / employer | translations, annotation batches, applications, invoices | tier V (2–3 lenses, executable checks first), then owner sign-off. A second human reads it if `client_tier=C2` or the contract value is above a threshold |
| R4 irreversible / legal / money | contracts, payments, prod data deletion, access revocation | one-way-door D- record plus founder approval. Agents prepare and never execute |

### 6.2 Sign-off

A deliverable is "signed" when the owner logs an `approval` event that references the verification events. The `verify_gate` hook already blocks "done" without a verification event. Extend it so that R3 deliverables also need an `approval` event by a `person:` actor. **No agent can produce an approval event**: the hook checks that `actor` starts with `person:` and came from a `UserPromptSubmit` path.

### 6.3 Review budget

Each person declares their weekly review minutes in their daily check-in rollup. The orchestrator's `fanout-plan` adds a `review_minutes` estimate (about 2 minutes per verified finding, about 10 minutes per client page) and asks before planning work that exceeds the remaining budget. This puts T6 into practice. Calibrate the estimate against logged real review times after about 20 runs.

---

## 7. Data boundaries, privacy and security at team scale

### 7.1 Scopes (extends `scope_grammar` with an *owner* and a *visibility* dimension)

| Visibility | Who can read | Stored in | Examples |
|---|---|---|---|
| `public` | anyone | site repo, public docs | albers.club pages, published app copy |
| `org` | all members | `claude-harness`, `albers-ops`, `team-data` | ontology, skills, rubrics, handbook, team patterns, decisions with `visibility: team` |
| `project` | members with a project `Grant` | the project repo | app code, project decisions, project knowledge |
| `client:<id>` | members with that client's `Grant` | client compartment (§7.3) | source docs, drafts, glossaries, TMs, client correspondence |
| `personal:<person>` | that person only (and, during an incident, the security officer with a logged `Grant`) | `harness-data-<handle>`, `msg-vault-<handle>` | raw prompts, transcripts, preferences, style memory, private messages, job search |

**Sensitivity** (aligned with `organization/information_organization.md` §facets) is set *independently* of visibility, and can only be raised further down: `public`, `private`, `client-confidential`, `third-party-personal`, `secret` (detect-only).

### 7.2 What flows from personal to team (the learning boundary)

The team RL loop needs shared signal, but raw personal logs must stay personal.

- **Flows up** (through `team-data`, written by a `promote` step during `review-week` with the person's per-batch approval):
  - pattern records, with their L-level, kind, support counts and **paraphrased** statements
  - correction *types* (not text)
  - eval results and gate verdicts
  - cost, time and verification-pass aggregates
  - mishap root causes and fixes
  - approved lessons
- **Never flows up:**
  - raw prompts, transcripts or message bodies
  - style samples
  - other people's personal data
  - anything from a `client:` compartment except fully abstract lessons (e.g. "check honorific consistency in KO formal emails" is fine; quoting client text isn't)
- **Consent:** a `Consent` record per person states which classes they share and whether their de-identified data may be used for training (VISION goal 1). Consent can be revoked, and revocation stops future flow and triggers deletion from `team-data` where feasible.
- **Departure:** on offboarding, the person keeps their personal data repo (it's theirs). The company keeps the team-scope records already promoted (covered by consent) and the work artifacts (company IP, per the employment contract). This needs to be written into the employment and contractor agreement: **legal review needed**.

### 7.3 Client compartments and NDA tiers

| Client tier | Typical client | Allowed | Not allowed |
|---|---|---|---|
| **C0 open** | public material, own projects | any tool | — |
| **C1 standard confidential** | most agencies and platforms | Claude (commercial terms, no training on Team data by default [M]); local tools; project TM/glossary kept per client | cloud converters/OCR/spellcheck (`LOCAL_ONLY.md`); reuse across clients; personal machines without disk encryption |
| **C2 restricted NDA** | clients whose NDA bans AI/MT or requires named processors | only what the NDA allows, which may be **no LLM at all**; work on a company-managed machine; a second human reads the deliverable | any AI processing unless the client gave *written* consent (store it as a `Consent` with `party: client-…`) |

**Mechanics:**
- `clients/<id>/CLAUDE.md` declares `tier`, `allowed_tools`, `retention` and `grants`.
- A `PreToolUse` hook (`compartment_guard.py`, new) blocks:
  - WebFetch and WebSearch, cloud MCP tools, and Bash network commands, when the cwd is inside a C1/C2 compartment
  - reads across compartments
  - any Claude use in C2 without a consent record
- Retention: per the client contract. The default is to delete working TMs and drafts 90 days after final payment, keeping only the invoice and an anonymised project summary (ProZ clause model [M]).

### 7.4 Claude org setup and managed settings

**Plan.** Claude **Team** (5–150 seats per most sources [M], *verify the current minimum*). Check the **Claude Startups program**: about 1 year of Team for up to 5 Premium seats [M, `recent_anthropic_updates.md` §6]. Use Premium seats for anyone running Claude Code heavily. Enterprise only becomes worth it for SCIM, custom retention/ZDR, the analytics API or per-group RBAC, none of which is needed at 5 people.

**Trade-off to note:** ZDR (Enterprise) would *disable* managed Code Review and contribution metrics [H]. For our C2 clients, the answer is "no Claude" rather than ZDR.

**Server-managed settings** (claude.ai → Organization settings → Claude Code → Managed settings, Owner only) [H]:

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "anthropics/claude-plugins-official" },
    { "source": "github", "repo": "albers-club/*" },
    { "source": "skills-dir" }
  ],
  "extraKnownMarketplaces": {
    "albers": { "source": { "source": "github", "repo": "albers-club/claude-harness" }, "autoUpdate": true }
  },
  "enabledPlugins": { "harness@albers": true },
  "disableSideloadFlags": true,
  "allowManagedHooksOnly": true,
  "env": { "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2" },
  "permissions": { "deny": ["Read(**/.env)", "Read(**/secrets/**)"] }
}
```

Notes:
- `allowManagedHooksOnly: true` means only managed and plugin-allowed hooks run. **Verify** that hooks from the force-enabled plugin still run under it before rollout (the control matrix says it "doesn't trust hooks from plugins users enable themselves", and ours is force-enabled) [H, needs a test].
- Console settings apply to all users, with no per-group targeting [H]. For a stable vs early-access channel, use two marketplaces (`albers` on `stable`, `albers-latest` on `main`), and give the steward the latest channel through a personal `managed-settings.d/` file on their device [H].
- Keep `syncClaudeAiPlugins` at its default. Org plugins enabled on claude.ai also reach Cowork and the apps, so the translator can use the same skills from the desktop app.

**Other org controls:**
- SSO through Google Workspace for albers.club (Team supports SAML/Google SSO [M]).
- GitHub org with 2FA required, and the Claude GitHub app for Code Review.
- A password manager vault per role.
- Claude Code analytics on, with the **leaderboard ignored** (§10).
- Spend limits per seat.
- OpenTelemetry export later, if per-person cost becomes a question [H, analytics doc].

**Agent identities** (Anthropic SDLC [H]):
- Scheduled routines and CI agents run as `service:` identities with their own minimal GitHub tokens (fine-grained, single-repo).
- No agent identity can merge to `main`, deploy or send external email.
- Every `service:` action is logged to `team-data/log/` (our "SIEM-lite": an append-only, hash-chained JSONL is enough at this size).

**Offboarding checklist** (security officer, same day):
- remove the seat
- remove from the GitHub org
- rotate the shared secrets they could read
- revoke `Grant`s
- remove from client portals
- transfer ownership of open issues, D-records and service identities (log `handoff_accepted` per item)

---

## 8. Onboarding checklist (into the harness)

The goal is that by day 5 the new member has shipped one verified change and one harness contribution, and has run the full loop once. Generate the base material with `/team-onboarding` from the founder's account [M], then curate it into `albers-ops/handbook/onboarding.md`. Durable rules belong in versioned files, not in the generated guide.

### Before day 1 (founder / security officer)
- [ ] Contract and NDA signed, including the **AI-use and data clauses**: personal vs company data, consent defaults, client compartments, departure terms.
- [ ] Claude Team seat (Premium if they'll run Claude Code heavily), SSO account, GitHub org membership with 2FA, Slack.
- [ ] `Member` record created (`p-<handle>`, roles, start date), plus `Grant`s for the projects and clients in scope. **C2 clients stay closed for the first cycle.**
- [ ] A company-managed or encrypted machine checked against the `docs/SECURITY.md` baseline.
- [ ] A starter issue (R1 or R2, about half a day of work) and a buddy assigned.

### Day 1: install and orient
- [ ] `gh auth login`. Managed settings deliver the `albers` marketplace and `harness@albers` on the first session, so check with `/plugin` and `/status` ("Enterprise managed settings" should appear) [H].
- [ ] Run `install.sh --person p-<handle>`. This is new: it creates `~/harness-data-<handle>` as a private repo, a `HARNESS_PERSON` env var, the personal `~/.claude/CLAUDE.md` from a template, and the vault directory.
- [ ] Read, in order: `VISION.md`, `global/PRINCIPLES.md` (org), this operating model, `docs/FANOUT.md`, `docs/LOCAL_ONLY.md`, and the decision log for their area. Use `/why` on 3 decisions to see the format.
- [ ] Run the `interview` skill on themselves to seed personal preferences (working hours, language/register, how they like to be asked). These stay personal.

### Days 2–3: run the loop once, supervised
- [ ] Do the starter issue end-to-end: brief (§5.2) → work → verify → PR with trailers (§5.6) → Code Review → human merge.
- [ ] Write one `D-` record, even a small one, and one `mishap` or `retro`.
- [ ] Hand off one piece of work to the buddy using the person→person HANDOFF (§5.3), and receive one back. Both must pass a human cold-read.
- [ ] Raise at least one `Ask` correctly (deadline, default, options).

### Days 4–5: contribute to the harness
- [ ] Add **one real eval task** to their area's eval set, built from a real case: input, expected output, rubric reference.
- [ ] Propose one small itemized harness edit as a PR (a rule, a skill tweak, or a glossary or style-guide entry), with evidence. It goes through the eval gate in shadow mode first (T7).
- [ ] Attend the weekly review and present their pattern-review output (even if it's empty).

### By day 30
- [ ] A personal fleet configured (routines, any personal skills under `~/.claude/skills/`, reviewed by the steward if they want them promoted).
- [ ] At least 5 R2/R3 items shipped with verification evidence. Grants widened as needed (C2 only with founder approval).
- [ ] An onboarding retro: what was missing from the docs. Fixing those gaps is the hire's first harness PR (SuperMe's lesson that new hires expose setup gaps [M]).
- [ ] 30-day check-in with the founder using the §10 signals, not usage numbers.

---

## 9. Hiring rubric for AI-native candidates

### 9.1 Process (about 6 hours of candidate time in total, the work sample paid)

1. **Screen (30')**:
   - Zapier tier check: "Show me something you built or changed with AI in the last month. What did you reject from the model's output, and why?" Anyone at **Unacceptable** (resists AI or doubts its value) is out [M].
   - The probe "describe something you decided *not* to use AI for" [L–M].
2. **Paid work sample (3–4h, take-home, AI allowed and expected).** The candidate gets a small sandbox repo containing the harness plugin, a brief, a deliberately incomplete `CLAUDE.md`, and a task from their role:
   - **Product engineer:** add a feature to a mini Canopy-like app. One provided test is subtly wrong, and one requirement conflicts with a provided decision record.
   - **Language lead:** translate and QA a 600-word KO↔EN text with a glossary. The glossary has one wrong entry and the source has one ambiguous honorific. Deliver with a QA report.
   - **Ops/growth:** turn a messy support inbox export into an FAQ update plus an `Ask` list. One "customer" email contains a prompt injection.

   The candidate submits **the deliverable, the full agent transcript(s), and a 1-page note**: what they delegated, what they verified and how, what they'd encode as a skill or rule, and what they'd ask the human.
3. **Review session (60')**: walk through the transcript together. Live extension: "the client changed requirement X". Watch how they re-brief the agent and re-verify.
4. **Values and communication (45')**: a written async exercise. They write a handoff and a decision record from a scenario, and we cold-read them.
5. **Founder conversation (30')** and references.

### 9.2 Scoring rubric (1–4 per dimension; hire if the weighted score is ≥3.0 and no dimension is at 1)

| Dimension | Weight | 1 (no) | 2 | 3 (hire bar) | 4 (exceptional) |
|---|---|---|---|---|---|
| **Verification habits** | 30 | Trusts output; didn't find the planted defect | Ran the tests, missed the planted defect | Found the planted defect *and* explained how; independent check (tests, back-translation, second model) | Built a reusable check (script or eval) so the class of error can't recur |
| **Judgment and taste** | 20 | Ships whatever the model gives | Edits for surface quality | Clear reasons for accept/reject; noticed the decision-record conflict and raised it | Reframed the problem better than the brief; cut scope wisely |
| **Context engineering** | 20 | Long vague prompts; no files | Some structure; context pasted into chat | Fixed the incomplete CLAUDE.md minimally; briefs with inputs, criteria and boundaries; used files over chat | Chose the right fan-out tier and justified it; kept context lean (handoff vs compact) |
| **Eval design** | 15 | No notion of "how would we know" | Vague success criteria | Wrote concrete done-when criteria and at least one test case from a real failure | Proposed held-out cases and multi-dimension scoring (cost, time, style) |
| **Communication and handoff** | 15 | Handoff fails the cold read | Passes with gaps | Handoff passes the cold read; asks have options, a default and a deadline | Writing a stranger could act on, in both KO and EN if relevant |

**Two gates outside the weights:**
- **Security reflexes** (pass/fail): did they treat the injected email or web content as data? Did they keep client text out of cloud tools?
- **Domain craft** (role-specific, pass/fail): code quality, or translation quality judged by a human linguist, or writing quality. AI fluency doesn't replace craft. A short no-AI segment in step 3 (15') checks the fundamentals [L–M, the "short no-AI round" counterpoint].

**Red flags:**
- Transcripts that show no reading of the output.
- "I'd just ask the AI" answers to judgment questions.
- Hiding AI use.
- Over-delegation without verification.
- Tokenmaxxing-style volume.
- Contempt for written process.

---

## 10. Performance and feedback loops that include AI usage

### 10.1 What we look at (quarterly conversation and monthly self-review)

| Signal | Source | Why |
|---|---|---|
| **Outcomes**: shipped bets, client acceptance and repeat rate, app metrics, revenue influence | cycle records, client `Message` classes, invoices | What actually matters (P16 "real outcomes") |
| **Verification pass rate at first submission** and **escaped defects** (found after sign-off) | `verification` events, mishaps tagged `escaped` | Quality of judgment and checking |
| **Correction rate received** (from clients, reviewers, teammates) per unit of work | correction events | Style and requirement fit |
| **Harness contributions accepted**: eval tasks added, skills, rules or hooks merged *that passed the gate*, retired rules | PRs to `claude-harness`, encodings with `author` | The compounding (Every) [M]: does your work make the next unit easier for everyone? |
| **Communication quality**: handoff cold-read scores, asks with defaults, decisions documented | handoff and ask events, the verifier's "undocumented decision" flags | Async culture |
| **Review load carried** | approval events on others' work | Avoids review free-riding |

### 10.2 What we don't use for evaluation

- Tokens, sessions, lines accepted, accept rate, the leaderboard or "AI usage %". These are **diagnostics only, at team level**. They're used to spot friction, never to rank people [M, tokenmaxxing].
- The analytics dashboard's leaderboard is hidden from reviews by policy, and this note says so explicitly.
- Shopify's "AI in performance review" expectation is interpreted as *"show the artifacts that prove reflexive AI use: briefs, evals, encodings"*, not as usage volume [M].

### 10.3 Personal RL loop vs team RL loop

- **Personal** (exists today): `review-week` labels → corrections → itemized edits → eval gate → approve. This runs on *your* `$HARNESS_DATA` and changes *your* personal CLAUDE.md, preferences and style memory.
- **Team** (new, §11): personal L2 patterns that 2 or more people share are promoted to team L3 encodings in the plugin, through the weekly review.
- **Calibration:** quarterly, each person compares their personal verifier's verdicts against the human sign-offs and client corrections. If agreement drops, recalibrate the verifier: few-shot examples and rubric wording.

### 10.4 Skill-erosion guard

The Anthropic survey reports concerns about skill erosion and mentorship [M]. Two countermeasures:
- **Monthly craft rep:** one no-AI task of about 1 hour in your own discipline (translate a page, debug a bug, write a pitch). Compare it with the agent's version and log any insight as a Lesson.
- **Pairing** as in §3.1. Code and translation reviews done *by humans* rotate, so everyone keeps reading others' raw work.

---

## 11. The team-level learning loop (RL at company scale)

1. **Observe:** each person's L0/L1 (events and labels), unchanged.
2. **Mine:** personal `pattern-review` produces L2 candidates. These are pushed to `team-data/patterns/candidates.jsonl` as paraphrased, de-identified records with `support_people` and `support_events` (counts only, plus pointers the owner can open).
3. **Aggregate** (Sunday, `team-review-week`): cluster the candidates across people. Any cluster with **support_people ≥ 2** or **one person and ≥3 episodes in a client-facing area** goes on the weekly agenda (§4.2 segment 3).
4. **Encode:** the steward (or the proposer) drafts the smallest possible L3: a rule line, a skill edit, a hook, a rubric criterion or an eval task. Prefer deleting and merging over adding (`review-week` §3).
5. **Gate:** run the eval set for the affected area(s). The rule is still *no regression on held-out tasks on any dimension*. A **new requirement for a team** is that held-out tasks include cases from ≥2 people, so a rule doesn't overfit one person's style.
6. **Shadow:** the new encoding runs in suggest-only mode for 1 week (T7). Logged acceptances and overrides decide whether it goes live.
7. **Release:** merge to the `albers-latest` channel, then to `stable` at the monthly release.
8. **Decay:** encodings unused for 6 weeks, or overridden by people more than X% of the time, are proposed for retirement (this exists in PATTERNS as meta-signals `encoding-unused` and `encoding-overridden`). New team meta-signals:
   - `person-divergence`: one encoding works for some people and is overridden by others. Make it a personal preference instead.
   - `ask-recurrence`: the same Ask answered the same way repeatedly. Turn it into a rule.
9. **Principles:** quarterly `distill-principles` across team patterns (§4.5). The org `PRINCIPLES.md` changes only with founder approval. Personal principles stay in each person's file.

**Eval ownership.** Each area's eval set has an owner (that area's DRI). Producing agents still cannot edit evals or rubrics (`guard_protected.py`). Now *humans* also edit them only through PRs reviewed by someone other than the person whose change is being gated. This is reward-hacking protection at team scale.

---

## 12. Ontology additions (proposed, for ontology v0.3.0)

These are aligned with the Party consolidation proposed in `organization/information_organization.md`, where Client, Organization, Contact and Platform become one `Party` registry. If that lands, a `Member` is a `Party` of kind `person` holding the `member_of: albers` relation. Until then, `Member` is its own type and `Contact` stays for external people.

### 12.1 Actor grammar (changes Event.actor and every `produced_by`)

```yaml
actor_grammar: '^(person:p-[a-z0-9-]+|agent:[a-z0-9-]+@p-[a-z0-9-]+|harness@p-[a-z0-9-]+|service:[a-z0-9-]+|external:pty_[a-z0-9]+)$'
renamed_values:
  actor: {me: "person:p-<founder-handle>", harness: "harness@p-<founder-handle>", "agent:<name>": "agent:<name>@p-<founder-handle>"}
```

A migration script rewrites nothing in place, because the logs are append-only. `schema_check` maps legacy values through `value_aliases` when it reads. The founder's handle (e.g. `p-jw`) has to be chosen.

### 12.2 New enums

```yaml
enums:
  role: [founder, harness-steward, product-engineer, language-lead, growth-ops, security-officer, contractor, buddy]
  visibility: [public, org, project, client, personal]
  sensitivity: [public, private, client-confidential, third-party-personal, secret]   # align with information_organization.md
  client_tier: [C0, C1, C2]
  decision_class: [two-way-door, one-way-door]
  decision_status: [proposed, accepted, held, revised, reversed, superseded]
  risk_tier: [R0, R1, R2, R3, R4]
  ask_status: [open, answered, defaulted, withdrawn, expired]
  grant_scope_kind: [project, client, personal-data, service, admin]
  review_kind: [daily, weekly, betting-table, cooldown, monthly-release, access-review, quarterly]
  consent_class: [patterns, corrections-types, eval-results, cost-aggregates, deidentified-training, client-ai-processing]
  # add to event_type:
  event_type_additions: [ask, ask_answered, handoff_sent, handoff_accepted, approval, review, access_change, onboarding_step, consent_change, promote]
```

### 12.3 New types

```yaml
  Member:
    desc: a person who works at Albers (employee/contractor); the accountable unit for every artifact
    store: {root: repo, path: "albers-ops/people/members.jsonl", format: jsonl, append_only: true, privacy: repo, status: planned, writer: "security officer (onboard/offboard skills)"}
    id_prefix: p-
    id_pattern: '^p-[a-z0-9-]+$'
    unique_id: false            # event-sourced, newest wins
    fields: [id, name, handles, roles, started, ended, employment, timezone, languages, data_repo, buddy, status]
    required: [id, name, roles, started]
    enums: {roles: role}
    refs: {buddy: Member}
    coverage: {provenance: [started], intent: null, meta: [roles]}

  Grant:
    desc: a permission for a member (or service) to a scope: project, client compartment, another person's data, or admin
    store: {root: repo, path: "albers-ops/people/grants.jsonl", format: jsonl, append_only: true, privacy: repo, status: planned, writer: "security officer; logged as access_change"}
    id_prefix: grt_
    fields: [id, grantee, scope_kind, scope, level, reason, granted_by, granted_at, expires, revoked_at, decision]
    required: [id, grantee, scope_kind, scope, level, granted_by, granted_at]
    enums: {scope_kind: grant_scope_kind, level: [read, write, admin]}
    refs: {grantee: Member, granted_by: Member, decision: Decision}
    formats: {granted_at: datetime, expires: date, revoked_at: datetime}

  Delegation:
    desc: Linear-style — an issue/task assigned to a human owner and delegated to an agent identity
    store: {root: harness-data, path: log/YYYY-MM.jsonl, format: event, append_only: true, privacy: harness-data, status: planned, writer: "orchestrator, fanout-plan"}
    fields: [id, task, owner, delegate, on_behalf_of, brief, risk_tier, budget, review_minutes_est, review_minutes_actual]
    required: [owner, delegate, task]
    enums: {risk_tier: risk_tier}
    refs: {owner: Member, on_behalf_of: Member}

  Ask:
    desc: an agent's (or person's) question to a specific human, with options, recommendation, default and deadline (§5.4)
    store: {root: harness-data, path: log/YYYY-MM.jsonl, format: event, append_only: true, privacy: harness-data, status: planned, writer: "skills/ask (new), hooks"}
    id_prefix: ask_
    fields: [id, ts, asker, owner_to_answer, question, options, recommendation, default_if_no_answer, default_is_safe, blocking, deadline, trigger_rule, status, answer, answered_by, answered_at, scope, sensitivity]
    required: [id, asker, owner_to_answer, question, deadline, trigger_rule]
    enums: {status: ask_status, sensitivity: sensitivity}
    refs: {owner_to_answer: Member, answered_by: Member}
    formats: {deadline: datetime, answered_at: datetime}

  Review:
    desc: a ritual instance (weekly review, betting table, access review…) with inputs, decisions taken and actions
    store: {root: repo, path: "albers-ops/reviews/YYYY-MM-DD_<kind>.md", format: md, append_only: true, privacy: repo, status: planned, writer: "skills/team-review-week"}
    id_prefix: rev_
    fields: [id, kind, date, attendees, preread, decisions_reviewed, patterns_promoted, evals_reviewed, asks_closed, actions, notes]
    required: [id, kind, date, attendees]
    enums: {kind: review_kind}
    refs: {attendees: Member}

  Consent:
    desc: what a member (or a client) allows to be shared/processed; revocable; newest per (party, class) wins
    store: {root: repo, path: "albers-ops/people/consents.jsonl", format: jsonl, append_only: true, privacy: repo, status: planned, writer: "member themselves via skills/consent (new)"}
    id_prefix: cns_
    fields: [id, party, class, granted, scope, evidence, ts, expires]
    required: [id, party, class, granted, ts]
    enums: {class: consent_class}

  ClientCompartment:
    desc: the per-client tier/tool/retention policy read by compartment_guard.py
    store: {root: project, path: "clients/<client-id>/CLAUDE.md", format: md, append_only: false, privacy: repo, status: planned, writer: "language lead + security officer"}
    fields: [client, tier, allowed_tools, denied_tools, retention_days, grants, consent, nda_ref]
    required: [client, tier]
    enums: {tier: client_tier}
```

### 12.4 Field additions to existing types

| Type | Add | Notes |
|---|---|---|
| **Event** | `owner`, `on_behalf_of`, `visibility`, `sensitivity`, `risk_tier`, `compartment`, `person` (the `HARNESS_PERSON` that wrote it) | `owner` is required for `task`, `decision`, `verification`, `approval`, `handoff_*` and `ask` (via `expected_when`) |
| **Decision** | `decider`, `consulted`, `class`, `status`, `visibility`, `supersedes` | `decider` is required. Plus a lint: an `one-way-door` decision needs a `Review` reference |
| **Handoff** | `from`, `to`, `owner_after_accept`, `accepted_at`, `grants_needed`, `human_cold_read` | Person→person (§5.3) |
| **Pattern / Encoding** | `support_people`, `scope_owner` (`personal:<p>` or `org`), `author`, `shadow_until` | Team ladder (§11) |
| **EvalTask** | `contributed_by`, `source_person` (for the ≥2-people held-out rule) | — |
| **Mishap** | `escaped` (bool: found after sign-off), `layer_failed` (brief, skill, rule, verifier, eval, human-review) | — |
| **Project** | `dri`, `members`, `visibility` | — |
| **scope_grammar** | Optional owner prefix: `personal:p-x/<area>/<project>`. Without a prefix it means `org` | `Preference.scope` is personal by default |

### 12.5 New relations

- `owned_by` (any artifact → Member)
- `delegated_to` (Task → agent identity)
- `acting_for` (agent identity → Member)
- `asked_of` / `answered_by`
- `approved_by`
- `granted_to`
- `promoted_from` (team Pattern → personal Pattern ids, which only the owner can open)
- `member_of`

---

## 13. Harness changes (concrete, file by file)

Priority **P0** = before hire #1, **P1** = within the first cycle after hire #1, **P2** = at about 3–5 people.

| P | Change | Files |
|---|---|---|
| P0 | **Move the marketplace to an org.** Create GitHub org `albers-club`; transfer `beingwithand/claude-harness` → `albers-club/claude-harness` (GitHub redirects, but update the README install lines); rename the marketplace to `albers` | `README.md`, `.claude-plugin/marketplace.json`, `BLUEPRINT.md` §0.5 Packaging |
| P0 | **Split org vs personal context.** `global/CLAUDE.md` becomes the *org* rules shipped by the plugin (no "About me"). Add `templates/personal/CLAUDE.md` with the "About me" and "How to work with me" sections each person fills in. `install.sh` installs the personal one at `~/.claude/CLAUDE.md`, importing the org file with `@` | `global/CLAUDE.md`, new `templates/personal/CLAUDE.md`, `install.sh` |
| P0 | **Split principles.** `global/PRINCIPLES.md` becomes org principles (P1–P20 plus T1–T8, after approval). Personal principles go to `~/.claude/PRINCIPLES.personal.md` | `global/PRINCIPLES.md`, `skills/distill-principles` (target selection) |
| P0 | **Person identity in the logs.** `hooks/_common.py` reads `HARNESS_PERSON` (from `install.sh`) and writes `actor` per §12.1, plus `person` on every event. `label_events.py` and `patterns.py` accept both legacy and new actor values | `hooks/_common.py`, `hooks/log_event.py`, `scripts/label_events.py`, `scripts/patterns.py`, `scripts/schema_check.py` |
| P0 | **Per-person data repo.** `install.sh --person p-x` creates `~/harness-data-<handle>` (private repo under the *person's* GitHub account, or under the org with a one-person team). `autocommit_data.sh` is parameterized | `install.sh`, `scripts/autocommit_data.sh`, `schema/STORAGE.md` |
| P0 | **Ontology v0.3.0** per §12, with `renamed_values` for the actor | `schema/ontology.yaml`, `schema/event.md`, `schema/STORAGE.md` |
| P0 | **Managed settings template**, plus a doc on applying it from the console | new `config/managed-settings.org.json`, `config/settings.README.md` |
| P0 | **Operating handbook.** This note distilled into `docs/TEAM.md` (protocol: §5, §6, §7) and `albers-ops/handbook/` (rituals, roles, onboarding, hiring) | new `docs/TEAM.md`; `docs/VISION.md` links to it |
| P1 | **`ask` skill + Ask hook.** `/ask` writes an `Ask` event, posts to `#asks` (via Slack MCP or Claude Tag later), and blocks or defaults per `default_is_safe`. A `PreToolUse` hook enforces triggers 7, 8, 10 and 12 (cross-owner writes via CODEOWNERS lookup, compartment crossing, teammate data, spend) | new `skills/ask/`, new `hooks/ask_guard.py`, `hooks/hooks.json` |
| P1 | **`compartment_guard.py`**: blocks network and cloud tools in C1/C2 compartments, blocks cross-compartment reads, and requires a consent record for C2 | new hook; `docs/LOCAL_ONLY.md` becomes the C1 policy section |
| P1 | **Person→person handoff.** Add the `--to <person>` mode: the extra header and sections from §5.3, a human cold-read checklist, and a `handoff_accepted` event on acceptance | `skills/handoff/SKILL.md`, `rubrics/handoff.yaml` |
| P1 | **Decision records v2**: `why` gets the `decider`, `class`, `status` and `visibility` fields; a `decisions-due` report for the weekly review; the verifier "undocumented decision" check in the `rules` lens | `skills/why/`, `agents/verifier.md`, `skills/verify/` |
| P1 | **Approval events + verify_gate R3 rule**: client-bound "done" needs an `approval` event from a `person:` actor | `hooks/verify_gate.py`, `skills/verify/` |
| P1 | **Commit trailers** `Owner`, `Agent`, `Verified-By` and `Decision`, through a `commit-msg` template and a Stop-hook reminder | `templates/project/.gitmessage`, `hooks/verify_gate.py` |
| P1 | **CODEOWNERS** in `claude-harness`: `schema/`, `evals/` and `rubrics/` need the steward plus one other person; `hooks/` needs the security officer. A PR template requires the eval-gate result | new `.github/CODEOWNERS`, `.github/pull_request_template.md` |
| P1 | **`team-review-week` skill**: builds the Sunday pre-read (§4.2) from `team-data` plus each person's opted-in promotions, and writes the `Review` record after the meeting | new `skills/team-review-week/`; `skills/review-week` gains a `promote` step (§7.2) with per-batch approval |
| P1 | **`onboard` / `offboard` skills**: run the §8 and §7.4 checklists, write `Member`, `Grant` and `onboarding_step` events | new `skills/onboard/`, `skills/offboard/` |
| P1 | **`fanout-plan` adds `review_minutes`** and asks when the owner's remaining review budget is exceeded (T6) | `skills/fanout-plan/`, `docs/FANOUT.md` §2 step 6 |
| P1 | **Turn on managed Code Review** (Team) for the Resonance and Canopy repos; add a `REVIEW.md` per repo with our correctness and security rules (read from the base branch only [H]) | app repos |
| P2 | **Release channels**: an `albers-latest` marketplace on `main` and `albers` on a `stable` tag; the steward is on latest | marketplace repos, `config/` |
| P2 | **Team eval rule**: the eval gate requires held-out tasks from ≥2 contributors before an org-scope encoding merges | `scripts/eval_gate.py`, `evals/README.md` |
| P2 | **New PATTERNS meta-signals** `person-divergence` and `ask-recurrence` | `docs/PATTERNS.md`, `scripts/patterns.py` |
| P2 | **Claude Tag in `#ops`** (beta) as a `service:claude-ops` identity with channel-scoped memory and a token cap; it reads and drafts only [M] | Slack admin, `Member`/`Grant` for the service |
| P2 | **Hiring kit**: work-sample repos per role, the §9.2 rubric as a YAML rubric, and a candidate-transcript review checklist | new `rubrics/hiring-ai-native.yaml`, `albers-ops/hiring/` |

---

## 14. Rollout: phases and triggers

| Phase | Trigger | Do |
|---|---|---|
| **0. Solo, team-ready** (now) | — | All P0 items. Run the rituals solo: a weekly review with yourself as attendee, using the same pre-read (it trains the loop and the data). Apply for the Startups program; decide between Team and Max. Start writing D-records with `decider` and `class`. Draft the contractor agreement with AI and data clauses (needs a lawyer) |
| **1. First hire (or first regular contractor)** | **Headcount test** (Shopify-style [M]): for 4+ consecutive weeks the founder's review queue exceeds their review budget, *and* a written memo shows the work can't be absorbed by better agents or fewer bets | Move to Claude Team, managed settings and Code Review. P1 items. A contractor in translation or annotation is the likely first person, which tests the compartment model early |
| **2. 3 people** | second sustained overload, or a new product bet | Rotate the steward role. Turn on `team-data` promotion. Run the betting table for real |
| **3. ~5 people** | — | P2 items. Consider Claude Tag. Quarterly principle review with everyone. Revisit Enterprise only if SCIM, custom retention or per-group policy becomes a real need |

---

## 15. Open questions and risks

1. **Legal.** Employment and contractor terms for (a) personal vs company ownership of harness logs, (b) consent for using de-identified data for training (VISION goal 1), and (c) KR PIPA and GDPR for teammates' data. *Needs a Korean employment and privacy lawyer.*
2. **`allowManagedHooksOnly` with a force-enabled plugin.** Confirm the plugin's hooks still run before turning it on (§7.4).
3. **Team plan minimum seats** and the current pricing: sources conflict [M]. Verify on claude.com/pricing at decision time.
4. **Code Review cost.** Third-party reports put it at about $15–25 per review [L]. Set the monthly spend limit, and use Quick level for low-risk repos [H].
5. **Review capacity estimates** (§6.3) are guesses until about 20 logged runs.
6. **Single founder as security officer, steward and approver** is a single point of failure until hire #2. Mitigate with the CODEOWNERS second-person rule as soon as there is a second person.
7. **Personal vs org principle drift.** If personal principles diverge sharply from org ones, that's a culture signal for the quarterly review, not something to auto-resolve.

---

## Sources

**Primary, read in full [H]:**
- Manage Claude Code plugins for your organization: https://code.claude.com/docs/en/plugins/org
- Track team usage with analytics: https://code.claude.com/docs/en/analytics
- Code Review: https://code.claude.com/docs/en/code-review
- How Anthropic secures its AI-native SDLC (J. Clinton, Jul 2026): https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle
- How Anthropic teams use Claude Code: https://claude.com/blog/how-anthropic-teams-use-claude-code

**Snippets or secondary [M]:**
- Server-managed settings, limitations (no per-group): https://code.claude.com/docs/en/server-managed-settings
- How AI is transforming work at Anthropic (Dec 2025): https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic
- Shopify memo coverage: https://thelogic.co/briefing/shopify-staff-must-use-ai-lutke-says/ · https://www.bensbites.com/p/reflexive-ai-use-isn-t-optional-anymore
- Zapier AI fluency (V1 May 2025, V2 Mar 2026): https://zapier.com/blog/raising-ai-fluency-bar-in-hiring/ · https://zapier.com/blog/zapier-ai-first-hiring-leaning/ *(unreachable; snippets)*
- Linear agents: https://linear.app/docs/assigning-issues · https://linear.app/now/our-approach-to-building-the-agent-interaction-sdk · https://linear.app/enablement/guide/ai-agents *(unreachable; snippets)*
- Accountability mapping (arXiv 2608.15678): https://arxiv.org/pdf/2608.15678 *(unreachable; snippet)*
- UNSW BusinessThink, AI agents as colleagues (Apr 2026): https://www.businessthink.unsw.edu.au/articles/ai-agents-workplace-human-ai-collaboration-governance
- Claude Tag: https://www.reworked.co/digital-workplace/anthropic-puts-claude-ai-agent-inside-slack-channels/ · https://slack.com/intl/en-in/help/articles/53532192117267-Use-Claude-in-Slack
- Zero Trust for AI agents (May 2026): https://claude.com/es/resources/articles/zero-trust-for-ai-agents
- `/team-onboarding`: https://claudelog.com/faqs/what-is-team-onboarding-in-claude-code/
- SuperMe, onboard everyone like an engineer: https://www.caseyaccidental.com/p/building-an-ai-native-company-onboard *(unreachable; snippet)*
- Tokenmaxxing: https://leaddev.com/ai/tokenmaxxing-and-the-search-for-ai-metrics-that-matter · https://en.sedaily.com/international/2026/05/29/big-tech-scraps-ai-usage-leaderboards-amid-tokenmaxxing
- GitLab handbook-first: https://handbook.gitlab.com/handbook/company/culture/all-remote/handbook-first/
- Amazon six-pager: https://amazonchronicles.substack.com/p/working-backwards-dave-limp-on-amazons
- Translation NDA practice: https://www.proz.com/securepro/security-practices/list/all · https://atlas-translations.co.uk/wp-content/uploads/2024/07/Atlas_Use_of_AI_and_MT_Policy_July_22_2024.pdf
- Compound engineering (Every): https://developertoolkit.ai/en/method/principles/compound-engineering/
- Claude Team plan third-party guides (seats, SSO, retention, sources conflict): https://www.layer3labs.io/comparisons/claude-team-vs-enterprise · https://www.aicodex.to/articles/claude-team-vs-enterprise-for-it

**Blog or vendor [L]:**
- AI-allowed interviews: https://www.cerebras.ai/blog/hiring-engineers-for-an-ai-native-world *(unreachable)* · https://cadence.withremote.ai/blog/ai-technical-interviews · https://amplifyit.io/blog/evaluating-judgment-skills-ai-native-technical-interviews
- AI-native team sizing: https://www.futureproofing.dev/resources/ai-native-team/what-is-an-ai-native-team
- ADRs and agents: https://docs.plannotator.ai/templates/architecture-decision-record · https://codex.danielvaughan.com/2026/04/28/codex-cli-architecture-decision-records-adr-automated-governance/

**Internal:**
- `claude-harness/README.md`, `BLUEPRINT.md` §0.5 and §4.13, `docs/FANOUT.md`, `docs/LOCAL_ONLY.md`, `docs/VISION.md`, `global/PRINCIPLES.md`, `global/CLAUDE.md`, `schema/ontology.yaml` v0.2.0, `schema/STORAGE.md`, `skills/handoff`, `skills/review-week`, `skills/pattern-review`
- `research_notes/Claude harness/recent_anthropic_updates.md`, `organization/information_organization.md`

**From memory, not re-verified this run:** Shape Up mechanics (appetite, betting table, 6+2 cycles, circuit breaker; Ryan Singer, Basecamp 2019).
