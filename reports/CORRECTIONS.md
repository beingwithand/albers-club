# Corrections log

Every time a fact in a report or chat answer turns out wrong, or a process step fails, it goes here: what was wrong, the fix, where it was fixed, and the rule that stops it happening again.

| # | Date | What was wrong | Correct version | Where fixed | Prevention rule |
|---|------|----------------|-----------------|-------------|-----------------|
| 1 | 2026-10-16 | Chat answer said Wuala shut down in 2017 | Shut down 2015 (P2P trading removed 2011) | Universal shared storage and compute.md (already correct) | Facts stated from memory in chat are labelled "from memory" and checked in the next research pass |
| 2 | 2026-10-16 | Universal shared storage report called Screenpipe "MIT" | Screenpipe is now source-available under a commercial license | Universal shared storage and compute.md, table row | Licenses are checked against the repo's LICENSE/README on the day of writing, never carried over from older notes |
| 3 | 2026-10-16 | A report rewrite overwrote the only complete version of "Personal data reclamation app.md" and was then cut off, leaving a truncated file | Report being regenerated from the notes | Personal data reclamation app.md (in progress) | Writers draft to a separate file and replace the final file only when the draft is complete; keep the previous version as a .prev.md |

## Standing checks before any report is delivered
1. Read this log and make sure no corrected fact reappears.
2. Look for contradictions with earlier reports in reports/ and either fix the old report or add a row here.
3. Mark anything not verified this session as unverified.
4. Analogue scan: before launching research, and again before writing, list who else solves the same underlying problem, including big-company products launched in the last 6 months, adjacent fields, and the user's own projects. Ask: "how does the closest product actually do it, and what can we copy?"

## Later entries
| # | Date | What was wrong | Correct version | Where fixed | Prevention rule |
|---|------|----------------|-----------------|-------------|-----------------|
| 4 | 2026-10-16 | Universal shared storage report gave Screenpipe CPU as 1–3% / 5–10% | Newer sources: ~5–15% CPU, 0.6–3 GB RAM | Universal shared storage and compute.md, table row | Resource figures carry their source and date; newer reports that differ add a row here |
| 5 | 2026-10-16 | Universal shared storage report said Korean users can't get continuous official data feeds | Korea's PIPA transmission right extends to all sectors: public bodies 20 Aug 2026, large private firms 20 Feb 2027 | Universal shared storage and compute.md, jurisdiction paragraph | Legal and regulatory claims carry an "as of" date |
| 6 | 2026-10-16 | Draft concept said "Rewind was bought by Meta" | Meta bought Limitless, Rewind's parent company | Relic concept.md (fixed before delivery) | Name the acquired legal entity, not just the product |
| 7 | 2026-10-16 | I assumed "Dots" meant Dot by New Computer | The user meant "Dots by OpenAI" | Researcher brief corrected mid-run | When a product name is ambiguous, ask or search all candidates before choosing one; name the assumption to the user |
| 8 | 2026-10-16 | I framed the cloud-memory research as a comparison and critique of server-side memory | The user wanted the mechanics of how those products do memory and context, to replicate locally | Writer brief corrected mid-run | Restate the purpose of each research request in one line before launching, and ask if the goal is ambiguous |
| 9 | 2026-10-16 | Backfill notes suggested using the user's everyday browser profile | Keep agents in a dedicated, isolated profile (safety); accept a one-time new-device check | AI memory and context engineering.md follows the isolated-profile rule | Safety design rules from earlier reports override convenience suggestions in new notes unless the user decides otherwise |
| 10 | 2026-10-16 | Reclamation report says OpenAI Atlas was discontinued Aug 2026; new notes call that unverified | Unconfirmed; both reports now say so | AI memory and context engineering.md | A product's status from a single source is marked "single-source" |
| 11 | 2026-10-16 | Earlier Relic design: MCP read-only | Design change: proposed writes go to a review queue the user approves | Relic concept.md, AI memory report | Design changes are logged here so older reports aren't mistaken for the current design |
| 12 | 2026-10-16 | Earlier report: Apple personal-context Siri status conflicting (mid-2026) | Siri AI shipped as a beta with iOS 27 around 14 Sep 2026 (timeline update) | AI memory and context engineering.md | Time-sensitive claims carry an "as of" date |
| — | 2026-10-16 | Note: hardware table RAM figures are estimates from parameter counts at 4-bit, not sourced | Kept, labelled as estimates | AI memory and context engineering.md | Replace with measured benchmarks when the prototype exists |
| 13 | 2026-10-16 | I reported the research was committed and pushed, but the first commit held only README.md: the local git ignore rule for reports/ and research_notes/ also applied to the research branch's worktree | Files force-added and pushed | research/personal-data-ownership branch | After every commit, run `git ls-files` (or `git show --stat`) to confirm the files are in it before reporting success |
| 14 | 2026-10-16 | I didn't connect Relic to OpenAI dots, Meta Muse and AI-memory products; the user had to | AI memory products are the closest technical analogue (always-on agent, memory, context) | AI memory and context engineering.md | Standing check 4 (analogue scan) before every research round |
| 15 | 2026-10-16 | AI memory report: Mem0 chooses ADD/UPDATE/DELETE/NOOP | True only of Mem0 1.x and the paper; current open-source Mem0 is ADD-only | Errata appended to AI memory and context engineering.md | Say which version of a library a claim covers (tag or commit) |
| 16 | 2026-10-16 | AI memory report: OpenMemory MCP described as the reference local design | Removed from Mem0 main; no authentication; likely deny-all bypass; hard-coded OpenAI categorizer, so never fully local | Errata appended | Verify "reference design" claims against the code, not the docs |
| 17 | 2026-10-16 | AI memory report: ChatGPT injects 4 blocks and ~40 recent chats | A newer leak (mid-2025, undated) shows 5 sections and ~50 recent conversations; both unverified | Errata appended | Date leaked or reverse-engineered material and treat it as a snapshot |
| 18 | 2026-10-16 | AI memory report cited OpenAI's own page for the ChatGPT Dreaming date (4 Jun 2026) | Only press coverage could be reached this round, so it is unconfirmed | Errata appended | Note whether the primary source was actually opened |
| 19 | 2026-10-16 | AI memory report: Generative Agents recency is exponential decay | In code it is rank-based (0.99^rank), weighted 0.5/3/2, and appears inverted | Errata appended | Prefer code over paper descriptions when they differ |
| 20 | 2026-10-16 | AI memory report: Letta sleep-time runs while the agent is idle | It fires every 5 turns as a background task; letta-code reflects on compaction | Errata appended | Prefer code over paper descriptions when they differ |
| 21 | 2026-10-16 | Reclamation report: Dayflow's storage and LLM use unverified | SQLite tables; cloud LLMs by default, Ollama optional | Errata appended to Personal data reclamation app.md | — |
| — | 2026-10-16 | Note: the agent-permissions addendum in Relic build guide.md draws partly on background knowledge | Verify each OS permission detail on device | Relic build guide.md addendum | Background-knowledge sections are labelled at the top |
