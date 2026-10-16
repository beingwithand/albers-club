# Claude harness blueprint

Working spec for a personal, self-improving Claude setup that survives losing any single machine.
Status: draft v0.3 (2026-10-16). Source: conversation requirements. Everything here is to be refined, then built into a private `claude-harness` repo.

## 0. Non-negotiables

1. **Nothing lives only on one laptop.** Config, skills, agents, ontology, decisions and logs go to GitHub. Files (PDFs, client work, assets) go to Google Drive. Secrets go to a password manager.
2. **Everything is logged, labeled, and learnable.** Every task, decision, and correction becomes an event with a scope (`global` or a project).
3. **Every task ends in verification.** Nothing is marked done until a verifier (a script, a model, or a human) has checked it against a stated standard.
4. **Rules change only with your approval.** The harness proposes changes to itself, and you approve them like a PR.
5. **New laptop setup takes about 20 minutes:** install Claude Code, run `git clone`, run `./install.sh`, log in.

## 0.5 State-of-the-art adjustments (v0.3)

These come from the research notes in `research_notes/Claude harness/`. Where the rest of this blueprint conflicts with them, these win.

**Packaging**
- Ship the harness as a **Claude Code plugin** in a private GitHub marketplace. On a new machine:
  1. Run `gh auth login`.
  2. Run `claude plugin marketplace add beingwithand/claude-harness`.
  3. Run `claude plugin install harness@claude-harness --scope user`.
- Hooks go in the plugin's `hooks/hooks.json`. Plugin agents ignore any hooks set in their own frontmatter.

**Agents and skills**
- Each agent file declares its `skills:` (they load fully at startup), `model:`, `effort:`, `memory: project`, and the tools it may use.
- Keep skills **few, focused and hand-curated**. Benchmarks show curated skills help a lot, while self-generated skills average slightly negative.
- New skills are drafted by agents but adopted only after review.

**Keep the memory files small**
- Each `CLAUDE.md` stays under 200 lines, written by hand, containing only what Claude can't infer. Research found that long or LLM-generated context files lower success and raise cost.
- Rules that apply to one area go in `.claude/rules/` with `paths:` filters.
- Procedures go in skills.
- Anything that must always happen goes in a hook.

**Verification**
- Use escalating gates:
  1. A self-check written into the prompt.
  2. A `Stop` hook that blocks until checks pass.
  3. An independent, skeptical verifier.
- The verifier should use a different model where possible, be calibrated with a few examples, and check against criteria agreed before the work started. Self-evaluation "reliably skews positive."
- **Protect against reward hacking:**
  - Producing agents cannot edit tests, rubrics or eval sets (enforced by `PreToolUse` deny rules).
  - Verifiers check correctness and the stated requirements only, not "find anything", which leads to over-engineering.

**Long tasks**
- `PROGRESS.md` plus a `tasks.json` in which agents may change only the `passes` field. JSON is less likely to be rewritten.
- Git commits serve as checkpoints, one verified unit of work per session.
- Write `SPEC.md` first, then run the work in a fresh session.

**The improvement loop (the RL part)**
1. Log sessions, mishaps and corrections.
2. Keep an **eval set of about 20 real tasks for each area**, with automatic checks plus a judge running on a different model.
3. Propose edits to rules and skills as **small itemized changes** (ACE-style), never full rewrites.
4. **Merge an edit only if the eval set does not get worse** (SkillOpt/GEPA-style). This guards against overfitting: one public example went from 90% to 95% on the training tasks while held-out results dropped from 95% to 85%.
5. You review the change, and it is committed to git.
6. Rules that haven't been used in N weeks are expired.

Score along several dimensions: correctness, how often you correct the work, cost, time, style match, and real outcomes.

Methods by maturity:
- **Mature:** DSPy/GEPA prompt optimization, best-of-N with verifiers, and rubric judges.
- **Early-stage (pilot carefully):** ACE, ReasoningBank (learning from failures) and learning from your edits.
- **Fine-tuning open models** with GRPO (OpenPipe ART, TRL) only for narrow, high-volume tasks. Not needed at the start.

**Knowledge and intake (the "LLM wiki" pattern)**
- Layout:
  - `knowledge/raw/` holds the untouched sources.
  - `knowledge/wiki/` holds pages the agent writes, each one cited.
  - `knowledge/index.md` is the catalog agents read first.
  - `knowledge/log.md` records each ingest.
  - `manifest.json` maps each source to its sha256 hash, its archive location, the converter and its version.
- Each wiki page's frontmatter records the source ID, the page anchors and the hash.
- A lint pass checks that every citation resolves.
- **Delete originals only after** the extraction is verified and archived.
- Converters to evaluate: markitdown, Docling, MinerU, Marker. Cleaning the Markdown matters more than which retriever is used.
- Add vector search (via MCP) only for large or fuzzy collections, and a knowledge graph (LightRAG) only for questions that chain across many entities.
- **Back-catalog import:** convert everything in bulk, cluster it by topic, draft candidate rules and skills, then curate them by hand.

**Model routing**
- Haiku for logging, labeling and extraction workers.
- Sonnet for most work.
- Opus or Fable to lead orchestration and make hard calls. Anthropic's best research setup was an Opus lead with Sonnet workers.
- Set a `model:` in every agent file. A subagent with no model set inherits the expensive one.
- Don't switch the main model mid-session: it throws away the prompt cache.

**Security**
- Treat skills, hooks and `.claude/` files as **executable code**: install nothing you haven't read, and scan third-party skills (e.g. NVIDIA SkillSpector). One audit found 36.8% of public skills flawed.
- Avoid mega-catalogs and capture-everything memory plugins: they cause context bloat and risk memory poisoning.

**Borrow ideas from these:**
- anthropics/skills
- obra/superpowers (plan, then one subagent per task with review)
- planning-with-files
- github/spec-kit
- Anthropic's long-running harness quickstart
- ECC, but only its "instincts" scoring and scanner ideas, not the whole catalog

Star counts in 2026 are inflated, so treat them as a measure of attention, not quality.

## 1. Repo layout (`claude-harness`)

```
claude-harness/
├── CLAUDE.md               # global identity, working style, pointers to everything below
├── ontology.yaml           # types + relations (section 5)
├── settings.json           # permissions, hooks, model defaults
├── agents/                 # reusable subagent definitions (section 2)
├── skills/                 # reusable skills (section 3)
├── principles/             # shared building blocks every agent imports (section 4)
├── rubrics/                # self-eval sheets per task type (section 7)
├── commands/               # /new-project /why /interview /review-week /resume
├── hooks/                  # logging, correction capture, verification gates
├── templates/project/      # standard project skeleton (section 6)
├── vendor.md               # vetted external GitHub tools + why (section 9)
└── install.sh              # symlinks into ~/.claude, checks deps
```

## 2. Agent roster (reused across all projects)

| Agent | Job | Default model |
|---|---|---|
| **orchestrator** | Breaks a task down, picks agents and models, fans out, merges results, runs verification | top tier (Opus / Fable) |
| **interviewer** | Runs the scope interview before any non-trivial task (section 4.1) | Sonnet |
| **web-researcher** | Scoped research: decides fan-out count, depth, source standards, then cites everything | Sonnet (workers: Haiku/Sonnet) |
| **pdf-extractor** | PDF → structured text/tables/images + metadata, with confidence scores | Haiku + tool |
| **translator** | KO↔EN, register-aware (section 8), uses your personal style memory | Sonnet |
| **annotation-assistant** | Guideline lookup, consistency checks, workflow notes per platform | Haiku / Sonnet |
| **job-tracker** | Scans email for applications, replies and interviews, then logs and updates status | Haiku |
| **coder** | Code changes in repos | Sonnet (Opus for hard work) |
| **asset-decomposer** | Breaks a digital or art file into component assets plus a manifest (section 10) | Sonnet |
| **browser-operator** | Chrome tasks, such as filling documents and forms (section 11) | Sonnet |
| **verifier(s)** | Independent checking against a rubric. Never the same agent that produced the work | Sonnet / Opus |
| **librarian** | Weekly: labels the log, proposes rule/skill updates, prunes memory | Haiku → Sonnet |

**Model routing rule:**
- Haiku for logging, labeling, extraction, and routine checks.
- Sonnet for most real work.
- Opus or Fable only for planning, orchestration, and hard judgment.

The orchestrator records which model it used per task, so cost and quality can be compared over time. Prices change, so check current rates before you fix defaults.

## 3. Skills (initial list)

`pdf-intake`, `web-research`, `translate-ko-en`, `translate-en-ko`, `annotation-workflow`, `job-application`, `email-scan`, `asset-decompose`, `browser-form-fill`, `verify`, `decision-record`, `progress-resume`.

## 4. Shared principles (imported by every agent)

### 4.1 Interview-first
Before any non-trivial task, ask only what changes the plan:
- the goal and what "done" means
- the audience and the register
- depth (quick, standard, or exhaustive)
- trusted versus banned sources
- the budget (time, money, number of agents)
- the deadline

If a past answer exists in memory for this kind of task, propose it instead of asking again. Your answers are logged as preferences.

### 4.2 Progress / resume (works for any file type)
Every task folder has a `PROGRESS.md` with these sections:
- **Goal**
- **Done**: each step, with a link to its output
- **In progress**
- **Next**
- **Blockers**
- **Last verified state**

Any agent, on any machine, can resume from this file alone. Long or browser tasks checkpoint after every step.

### 4.3 Verification gate
Each task type declares a verifier and a rubric. Results are logged as pass, fail, or needs-human. A fail loops back to the producing agent, up to N times, then escalates to you.

### 4.4 Decision records
Each decision record includes:
- the claim
- the reasons
- the evidence (links)
- the alternatives considered
- the expected outcome, with a date
- the review date

Use `/why` to log one by hand.

### 4.5 Corrections
Whenever you redirect an agent, the harness logs:
- what the agent did
- your correction
- your reasoning
- the scope

Weekly, the librarian proposes rule changes. A correction that repeats across two or more projects is proposed as a global rule.

### 4.6 Mishap log (self-correction capture)
Whenever an agent notices it did something wrong and fixes it, it appends an incident record to `log/mishaps.md` and the event log. Each record covers:
- what happened
- how it was noticed
- the fix
- the root cause
- how to prevent it (a proposed rule, check or hook)
- how to repeat it, if the fix turned out to be a useful pattern
- proof (a diff, output, screenshot or link)

At session end, the open mishaps are reviewed and their prevention rules are proposed. Rules you approve go into project or global `CLAUDE.md`, a verifier, or a hook.

### 4.7 Session retrospective (automatic)
At the end of every substantial session (a SessionEnd/Stop hook, or `/retro`), the agent writes a `log/sessions/YYYY-MM-DD_<topic>.md` file covering:
- the question or goal
- the paths tried, including dead ends
- the resolution
- the decisions made, with their justification
- the proof
- lessons learned
- what to reuse
- what not to repeat
- pointers (files, commits, sources)

The note is indexed, so a future session on the same topic loads it first instead of re-deriving it.

### 4.8 Justification + proof on every step
Every step and decision records three things:
- **Why:** the specific reason, not "seemed best".
- **Proof:** the command output, test result, source quote with link, or before/after.
- **Meta:** how to repeat this if it worked, or how to prevent it if it failed.

A step without proof counts as unverified.

### 4.9 Handoff pointers
Any handoff (agent to agent, session to session, or machine to machine) carries a pointer block:
- `PROGRESS.md` location
- latest decision IDs
- open mishaps
- relevant session notes
- artifacts produced
- what the receiver must verify first

No handoff relies on context the receiver doesn't have.

### 4.10 Research standard (web-researcher default)
- **Recency:** "state of the art as of today". Inject the real current date from the system on every run, never a hard-coded one. Rank by recency, flag anything older than about 6 months on fast-moving topics, and note the publication date for every claim.
- **Source tiers:** set per task in the interview. Defaults:
  1. Primary sources: arXiv, Google Research, Google DeepMind, MIT, Stanford, other labs' papers and blogs, official docs.
  2. Code: GitHub repos ranked by stars, recent commits and releases, plus issue activity, which shows real-world health.
  3. Practitioner sentiment: Reddit, Hacker News, YouTube transcripts.
  4. Press and vendor blogs: lowest weight, flagged as possibly biased.
- **Fan-out:** the interview sets the depth. Quick means 1 agent, standard 3, exhaustive 5 or more split by source tier.
- **Output:** every claim carries a citation, a date and a confidence level. Conflicts between sources are shown, not hidden. Gaps are listed explicitly.
- **Access fallbacks:** when a site can't be reached (as Reddit and YouTube weren't in this cloud session), say so plainly and ask for links or pasted text rather than guessing.

### 4.11 Project intake (extract once, point forever)
At the start of every new project, an intake agent processes everything you give it (PDFs, briefs, links, emails):
1. **Extract** the content into `knowledge/` as clean Markdown, with tables kept and images saved.
2. **Index it** in `knowledge/INDEX.md`: one line per fact cluster, with a pointer to the file, section and page of the original.
3. **Record provenance** for each item:
   - the original filename and a hash of the file
   - the date it was received
   - where the original is archived (a Drive link)
   - the extraction tool used
   - a confidence level
4. **Verify** the extraction: a checker compares samples against the original, and checks page counts and tables.
5. **Archive the original** to Drive. Only then can the local copy be deleted, and the pointer still resolves.

Agents read `INDEX.md` first and open only what they need, which keeps context small.

### 4.12 Back-catalog import (reverse-engineer past work)
Once the new laptop is set up, run the intake pipeline in bulk over old projects, chats, files and emails. Then:
1. **Classify** each item into an area and project, using the ontology.
2. **Extract** decisions, corrections, style pairs and lessons from it.
3. **Propose** a draft `CLAUDE.md` rule set for each area, which you review before anything is adopted.

Import is read-only, and every item links back to its source.

### 4.13 Multi-dimensional improvement loop (RL-style)
- **Rewards along several dimensions:**
  - correctness, from the verifier
  - how often you correct the work
  - cost
  - time
  - style match, for writing and translation
  - outcome, such as an application reply or a client acceptance
- **Policy = prompts, rules, skills and routing.** These are optimized against your logged tasks and benchmark sets.
- **Methods:** to be filled from the state-of-the-art research now running, which covers GEPA/DSPy, ACE, Reflexion-style memory, rubric judges, best-of-N with verifiers, and fine-tuning open models on logged task histories.

## 5. Ontology v0 (`ontology.yaml`)

**Types:**
- Person
- Client
- Project
- Area (translation, annotation, job-search, art, code, personal)
- Task
- Asset
- Document
- Decision
- Correction
- Preference
- Evaluation
- Application (a job application)
- Source
- Mishap
- SessionNote
- Proof
- Lesson

**Relations:**
- `part_of`
- `for_client`
- `produced_by` (an agent, plus the model it used)
- `derived_from`
- `evidence_for`
- `supersedes`
- `corrects`
- `evaluated_by`
- `blocks`
- `prevents` (a Lesson or rule that prevents a Mishap)
- `proven_by` (any step or decision linked to its Proof)
- `handed_off_to`
- `learned_from`

**Rules:**
- Version the file in git.
- Agents may propose new types, but only you approve them.
- Keep a mapping when a type is renamed or merged.

## 6. Folder standard (every project)

```
<area>/<project>/
├── CLAUDE.md        # project rules + pointer to global
├── PROGRESS.md
├── inbox/           # raw inputs (PDFs, briefs, source files) – synced to Drive
├── work/
├── deliverables/
├── assets/          # decomposed parts + assets.yaml manifest
├── decisions.md
└── log/
```

**File naming:** `YYYY-MM-DD_<project>_<what>_v<N>.<ext>`

## 7. Self-eval sheets (`rubrics/`)

Each task type gets a YAML rubric with:
- criteria
- a scale
- examples of a 1 and a 5
- automatic checks where possible

The verifier scores the work, and you score a sample of the same work. Comparing the two calibrates both, and tracks whether you and the agents are improving over time.

Starter rubrics: translation, annotation batch, job application, research report, code change, asset package.

## 8. Language and register memory

Log every pair of draft and your final edit, tagged with:
- `language` (ko, en, mixed)
- `direction` (ko→en, en→ko, none)
- `register` (formal email, office/business, friendly, chat, client deliverable, annotation response)
- `domain`
- `audience`

The translator and writing agents pull the closest past examples as few-shot references. Over time this becomes your personal style guide, generated from the data and approved by you.

## 9. External tools to evaluate (`vendor.md`)

These are candidates, not decisions. Before adopting any tool, check its license, how active it is, and whether it can run offline.

- **PDF:** Docling, Marker, MinerU, PyMuPDF4LLM, Unstructured
- **Web research and scraping:** Crawl4AI, Firecrawl, Trafilatura
- **Browser automation:** Playwright MCP, browser-use, Stagehand, Claude in Chrome
- **Prompt and policy optimization (later):** DSPy, GEPA

Rule: wrap each tool in a skill, so you can swap the tool without changing the agents that use it.

## 10. Asset decomposition

The first step for any digital or art work: split the source into its parts (layers, text, images, palettes, fonts, audio). Record each part in `assets.yaml` with:
- an ID
- its type
- its source file
- its provenance
- its usage rights
- derived variants

Later work references these asset IDs instead of re-extracting the parts.

## 11. Browser and Chrome reliability

- Prefer reading the page structure (the DOM or accessibility tree) over screenshots.
- Use an API or CLI whenever one exists, and fall back to the browser only when nothing else works.
- After every action: confirm the change by reading the page back, checkpoint in `PROGRESS.md`, and keep steps safe to re-run, so a crash just resumes.
- Slow down on fast-changing pages: wait for the page to settle, take a fresh read, then act. Never act on a stale screenshot.
- Never submit forms, payments or applications without your confirmation.

## 12. Logging and backup stack

- **Event log:** Supabase table `events` (id, ts, actor, agent, model, scope, type, inputs, outputs, parent_event, cost, labels, outcome). Append-only.
- **Hooks:** log every prompt, each session summary and every correction, all automatically.
- **Backups:**
  - git auto-commit for text
  - Google Drive for files
  - Time Machine or Backblaze as the third copy, once the laptop arrives
  - a password manager for secrets

## 13. Build order

1. Rotate passwords and revoke tokens on the old laptop (urgent).
2. Create the `claude-harness` repo with `install.sh`, the global `CLAUDE.md`, and the folder template.
3. Set up the logging hooks, the Supabase table, and the `/why` command.
4. Build the interviewer, progress/resume, and verifier principles.
5. Build the first agents: web-researcher, pdf-extractor, translator, job-tracker.
6. Write the rubrics, and capture register memory.
7. Add the librarian's weekly review loop.
8. Add browser-operator hardening and asset-decomposer.
9. Merge in ideas from your YouTube videos.

## Open questions

- Which language pairs and domains do you translate in?
- Which annotation platforms do you use?
- Which email account(s) should the job tracker scan?
- What kind of art and digital work do you do, in which tools?
- What are the YouTube links?
