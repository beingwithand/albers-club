# Session note: 2026-10-16, agent research and harness build

Seed record for `harness-data`. Move to `$HARNESS_DATA/sessions/` once that repo exists.
Session: https://claude.ai/code/session_01TsbW2R32y5VMMxyaYoyyZh

## Goal and intent
- **Situation:** the old laptop's data is likely lost and the user is getting a new laptop.
- **Intent:** never lose anything again, and build a self-improving, logged Claude harness ready to deploy on the new Mac, using up this week's Max 20x allowance before it resets.

## Path
1. Researched OpenClaw on a Mac Mini, Hermes Agent, and autonomous-agent alternatives. Report: `reports/OpenClaw and Hermes agent autonomy.md`.
2. Answered follow-up questions:
   - sandboxing OpenClaw on a MacBook or desktop
   - the cheapest accurate model for agents
   - Jev
   - Claude Code approvals and event triggers
   - running two Max accounts
   - the startup program, which is paused and full
3. Designed the harness: `reports/Claude harness blueprint.md` (v0.1 → v0.3).
4. Researched the current state of the art. Notes are in `research_notes/Claude harness/`:
   - official Claude Code features
   - SOTA harness patterns
   - official setup for remote control and permissions
   - community best settings
   - Anthropic updates from Aug to Oct 2026
5. Built `claude-harness/` (plugin): 12 agents, 27 skills, hooks, schema, scripts, tests, Mac bootstrap, settings and docs.

## Decisions (with justification)
- **D1: Ship the harness as a Claude Code plugin in a private GitHub marketplace.** This is the officially supported route and makes reinstalling one command. Rejected: a loose dotfiles repo (no packaging), and claude.ai sync alone (doesn't cover hooks).
- **D2: Keep CLAUDE.md short and hand-written; put procedures in skills and must-happen behavior in hooks.** Research found that long or generated context files lower success and raise cost by more than 20%.
- **D3: A rule or skill change is merged only if the eval set doesn't regress, and only with user approval.** Ungated self-improvement overfits: one example went from 90→95% on training tasks but from 95→85% on held-out tasks.
- **D4: The verifier is separate and uses a different model; producing agents can't edit evals or rubrics.** Self-evaluation skews positive, and reward hacking is common (76% on ImpossibleBench when tests were editable).
- **D5: Use auto mode, a mandatory sandbox and deny rules, not bypass mode.** The official docs reserve bypass for containers and VMs, and deny rules on Read don't stop Bash.
- **D6: Logs are append-only JSONL in a separate private `harness-data` repo, auto-committed hourly.** This gives durability across machines and keeps the history immutable.
- **D7: Every record carries intent, situation and meta.** This is the user's explicit requirement, and it is the labeling signal for the improvement loop.
- **D8: Research and harness work live on the `research/agent-autonomy` branch of albers-club** until `claude-harness` gets its own repo. Creating a repo through the GitHub app returned 403.
- **D9: The synopsis skill writes 3 drafts with different strategies, and reviewer feedback becomes numbered rules that can be checked.** This mirrors the user's existing Toin workflow.

- **D10: Fan-out policy calibration (user-confirmed).**
  - Search escalates from inline (tier 0) to a small fan-out (tier 2) when it needs more than about 3 sources or mixes source types (papers, GitHub, Reddit).
  - Verification fan-out is **always** run on anything sent to clients or employers.
  - Tier 3 (full fan-out) **asks before starting** when weekly usage is above 75%.

- **D11: Resonance privacy model (user-confirmed).** PDFs and page images *may* be sent to Gemini, Claude or the server for rendering and extraction; that is the app's design. The user's own data (annotations, highlights, notes, journal, voice notes, reading history) stays **local**. The OCR bench sends pages by default and never sends user data.

- **D12: Organization (user-confirmed).** Projects use flat `~/projects/<slug>/` plus a project registry, with fields kept in metadata rather than folder paths. Clients, organizations, contacts and platforms merge into one **Party** registry.
- **D13: Coder plus code-reviewer pair, and verification at every step (user requirement).** Both agents share one coding-rules skill (surgical, minimal fixes). The reviewer reviews each step as it happens and back-reviews earlier work, and may make surgical fixes. Verification between every step applies everywhere, not only to code.

- **D14: Data decisions (user, 2026-10-16).**
  - Q5: local embeddings over vault text are OK.
  - Q6: tax and finance records are kept 7 years at minimum; the default is set to 10 ("7 or more").
  - Q4: the number of Macs is undecided. Design for one writer Mac now, with per-host log files so a second machine is a no-op later. The vault is single-machine for now, with encrypted (age/restic) offsite backup; a second-machine vault is optional later.
  - Q3: the answer was ambiguous ("client text can't go into the vault"), so it needs confirmation.

## Mishaps
- **M1:** Research notes were saved inside an unrelated repo (albers-club) without asking first.
  - Root cause: the deep-research default location.
  - Prevention: global rule "never save non-project files in an unrelated repo" (now in `global/CLAUDE.md`).
- **M2:** The user's YouTube links were not processed, and the reply implied that no links had been sent.
  - Root cause: youtube.com is unreachable from the cloud sandbox.
  - Prevention: when a source can't be reached, say so plainly and ask for pasted content (`web-research` skill §3).
- **M3:** Subagents' suggested test command (`python3 -I -m unittest tests.x`) fails under `-I`.
  - Fix: use `discover -s tests -t .`.
  - Prevention: documented in `docs/INTAKE.md` and the test files.

## Principles distilled
See `claude-harness/global/PRINCIPLES.md` (16 principles, v0).

## Open items (user)
1. Create the empty private repo `claude-harness` and give Claude access, so the harness can move there.
2. Rotate passwords and revoke tokens from the old laptop (`claude-harness/docs/SECURITY.md`).
3. Send the YouTube video titles or transcripts.
4. ~~Confirm the synopsis length unit~~ **Resolved:** characters including spaces (the user confirmed this on 2026-10-16; the synopsis skill is updated).
5. Fill in `docs/REGISTERS.md` and the per-project `reviewer_rules.md`.
6. Claim the monthly $200 API credit (Max 20x) under Settings → Billing.

## Verify first (next session)
- On the Mac: `claude plugin validate`, then run `mac/bootstrap.sh` one step at a time.
- Remote Control's launchd job and the settings keys marked "verify" need checking against the live docs.
