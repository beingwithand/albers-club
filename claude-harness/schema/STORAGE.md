# Storage map

Which record type lives in which file, whether it is append-only, and how private it is.
Source of truth: the `store:` block of each type in `schema/ontology.yaml` (v0.2.0). Regenerate the
short table with `python3 -I scripts/schema_check.py --stores`; validate data with
`python3 -I scripts/schema_check.py [--root $HARNESS_DATA] [--project <area>/<project>]`.

## Roots and privacy

| Root | Where | Synced to | Privacy value | What may go there |
|---|---|---|---|---|
| `harness-data` | `$HARNESS_DATA` (default `~/harness-data`) | private GitHub repo, auto-pushed hourly (`scripts/autocommit_data.sh`) | `harness-data` | Logs, labels, style memory, preferences, eval results, and *derived* job/contact records that point to the vault by id. Never a copy of a message body or attachment. |
| `msg-vault` | `~/msg-vault/` (mode 700, FileVault) | **nothing**: never a git remote, never synced | `vault` | Raw messages, threads, attachments, sync cursors, raw text excerpts (StyleSample). Other people's personal data and NDA content. |
| `project` | `<area>/<project>/` (from `templates/project`) | the project's own git repo; originals archived to the project Drive folder | `repo` | Project knowledge, assets, decisions, mishaps, session notes, handoffs, invoices. Client content stays local-only for processing (`docs/LOCAL_ONLY.md`). |
| `repo` | this harness (`claude-harness`) | GitHub `claude-harness` (private) | `repo` | Ontology, rubrics, principles, skills, agents. No personal data. |
| `home` | `~/.claude/` | not synced | `local` | Per-machine runtime state (status line / usage guard cache). |

`append_only: yes` means: never edit or delete a line; fix with a new record (`supersedes`, `corrects`,
a `label` event, a ledger `status` row, or a later Application line with the same id where the newest wins).

## Map

| Type | Root | Path | Format | Append-only | Privacy | Status | Id | Writer |
|---|---|---|---|---|---|---|---|---|
| Event | harness-data | `log/YYYY-MM.jsonl` | jsonl | yes | harness-data | active | evt_ | hooks/log_event.py, hooks/_common.py, scripts/label_events.py, skills |
| Proof | harness-data | `log/YYYY-MM.jsonl` | embedded | yes | harness-data | active | — | skills |
| Decision | project | `decisions.md` | md | yes | repo | active | D- | skills/why |
| Correction | harness-data | `log/YYYY-MM.jsonl` | event | yes | harness-data | active | evt_ | skills/review-week (type correction), scripts/label_events.py (label is_correction) |
| Mishap | project | `log/mishaps.md` | md | yes | repo | active | — | skills/mishap |
| Lesson | project | `knowledge/wiki/<area>/<project>-lesson.md` | md | no | repo | active | L- | skills/backcatalog, skills/retro |
| SessionNote | project | `log/sessions/YYYY-MM-DD_<topic>.md` | md | yes | repo | active | — | skills/retro |
| Handoff | project | `HANDOFF.md` | md | no | repo | active | — | skills/handoff, hooks/precompact_snapshot.py (log/handoffs/auto_*.md) |
| ProgressItem | project | `tasks.json` | json | no | repo | active | — | agents/orchestrator (workers may change only `passes`) |
| Preference | harness-data | `preferences.jsonl` | jsonl | yes | harness-data | active | pref_ | skills/interview |
| ResearchNote | harness-data | `research/ledger.jsonl` | jsonl | yes | harness-data | active | rn_ | skills/check, skills/web-research |
| Principle | repo | `global/PRINCIPLES.md` | md | no | repo | active | `P<n>` | skills/distill-principles (after approval) |
| Pattern | harness-data | `patterns/patterns.jsonl` | jsonl | yes (newest per id wins) | harness-data | active | pat_ | scripts/patterns.py record (skills/pattern-review, skills/retro seeds) |
| Encoding | harness-data | `patterns/encodings.jsonl` | jsonl | yes (newest per id wins) | harness-data | active | enc_ | scripts/patterns.py record (skills/pattern-review after approval) |
| MetaPattern | harness-data | `patterns/meta.jsonl` | jsonl | yes (newest per id wins) | harness-data | active | mp_ | scripts/patterns.py record (skills/pattern-review after approval) |
| Evaluation | harness-data | `evals/results/<area>/*.json` | embedded | yes | harness-data | active | — | eval runner |
| EvalRun | harness-data | `evals/results/<area>/*.json` | json | yes | harness-data | active | — | eval runner; read by scripts/eval_gate.py |
| EvalTask | harness-data | `evals/<area>/tasks/*.yaml` | yaml | no | harness-data | active | `^[a-z-]+-\d{3}$` | the user (templates in evals/<area>/task_template.yaml) |
| Rubric | repo | `rubrics/*.yaml` | yaml | no | repo | active | — | the user only |
| Project | project | `CLAUDE.md` | md | no | repo | active | — | skills/new-project |
| Client | harness-data | `clients.jsonl` | jsonl | yes | harness-data | planned | client- | none yet (project CLAUDE.md 'Client / owner') |
| Task | harness-data | `log/YYYY-MM.jsonl` | event | yes | harness-data | active | — | agents/orchestrator, skills |
| Document | project | `knowledge/manifest.json` | json | no | repo | active | `^[0-9a-f]{8}$` | scripts/kb.py |
| WikiPage | project | `knowledge/wiki/*.md` | md | no | repo | active | — | skills/intake, skills/backcatalog; linted by scripts/kb.py |
| IntakeLogEntry | project | `knowledge/log.md` | md | yes | repo | active | — | agents/verifier; read by scripts/kb.py safe-to-delete |
| BackcatalogRow | harness-data | `backcatalog/knowledge/backcatalog*.csv` | csv | no | harness-data | active | — | scripts/kb.py |
| Asset | project | `assets/assets.yaml` | yaml | yes | repo | active | A- | scripts/psd_layers.py, scripts/palette.py, skills/asset-decompose |
| Palette | project | `assets/palette/*.json` | json | no | repo | active | A- | scripts/palette.py |
| GlossaryTerm | project | `knowledge/glossary.md` | md | no | repo | active | — | scripts/glossary.py, the user approves rows |
| ReviewerRule | project | `knowledge/reviewer_rules.md` | md | no | repo | active | R- | skills/synopsis |
| StylePair | harness-data | `style/pairs.jsonl` | jsonl | yes | harness-data | active | sp_ | scripts/style_pairs.py |
| StyleSample | msg-vault | `style/samples.jsonl` | jsonl | yes | vault | planned | ss_ | Gmail backfill (style_samples.jsonl shape) |
| StyleGuide | harness-data | `style/guide.md` | md | no | harness-data | active | — | skills/style-guide (after approval) |
| Application | harness-data | `applications.jsonl` | jsonl | yes | harness-data | active | app- | skills/job-application, skills/email-scan (agents/job-tracker) |
| JobLead | harness-data | `jobleads.jsonl` | jsonl | yes | harness-data | planned | jl- | email-scan / alert parsing (docs/MESSAGING.md) |
| Platform | harness-data | `platforms.jsonl` | jsonl | yes | harness-data | planned | plat- | Gmail backfill (platforms.json shape: {generated, scope, note, platforms: [...]}) |
| Organization | harness-data | `organizations.jsonl` | jsonl | yes | harness-data | planned | org- | none yet |
| Contact | harness-data | `contacts.jsonl` | jsonl | yes | harness-data | planned | ct- | none yet |
| Account | harness-data | `accounts.jsonl` | jsonl | yes | harness-data | planned | acct_ | the user / ingest setup (addresses only, no message content) |
| Message | msg-vault | `<source>/messages.jsonl` | jsonl | yes | vault | planned | msg_ | ingest (docs/MESSAGING.md) |
| Thread | msg-vault | `<source>/threads.jsonl` | jsonl | yes | vault | planned | thr_ | ingest |
| Attachment | msg-vault | `<source>/attachments.jsonl` | jsonl | yes | vault | planned | att_ | ingest |
| SyncCursor | msg-vault | `cursors.json` | json | no | vault | planned | cur_ | ingest |
| Invoice | project | `deliverables/*_invoice_*.md` | md | no | repo | active | INV- | scripts/invoice.py make |
| LedgerEntry | harness-data | `finance/ledger.csv` | csv | yes | harness-data | active | invoice_id: INV- | scripts/invoice.py |
| HarnessState | home | `.claude/harness-state.json` | json | no | local | active | — | scripts/statusline.py; read by hooks/usage_guard.py |

Untyped files in `harness-data` (not records; not validated):
- `labels/batch_<from>_<to>[_partNN].jsonl`, `labels/*.labels.jsonl`, `labels/label_prompt.md`: transient batches from `scripts/label_events.py` (they copy prompt text, so they are as private as the log).
- `backcatalog/knowledge/` (`manifest.json`, `raw/`, `wiki/`, `log.md`): a knowledge folder with the `project` layout, so check it with `--project $HARNESS_DATA/backcatalog`.
- `.autocommit.log`, `.gitattributes` (union merge for `*.jsonl`).
- `patterns/config.json`: thresholds for `scripts/patterns.py ladder|meta` (missing keys fall back to the defaults in the script; `patterns.py config` prints the merged values).

Pattern seeds that ship with the harness (no personal data, evidence as session-note pointers) live in the **repo** at `patterns/seed_patterns.jsonl` (Pattern, Encoding and MetaPattern lines mixed, told apart by id prefix). `patterns.py` reads them next to the harness-data stores until `pattern-review` imports them with `patterns.py record`.

## Known gaps (v0.2.0)
- ~~`finance/ledger.csv` is not union-merged~~ **Fixed:** `autocommit_data.sh` now sets `finance/*.csv merge=union`. Note that the ledger puts amounts and client names in the GitHub-synced repo, which is by design but worth knowing.
- **Session notes have two homes.** `skills/retro` writes `<project>/log/sessions/`, while the header of `autocommit_data.sh` lists `sessions/` as part of `$HARNESS_DATA`. Pick one (the ontology records the project path, which is what the skill does).
- **Gmail backfill outputs are not yet placed.** If they are persisted: `applications.jsonl` and `platforms.json` go to `harness-data` *after* dropping message subjects/quotes (keep thread ids only); `style_samples.jsonl` (subjects and excerpts) and the `reviewer_feedback` quotes in `clients_projects.jsonl` go to `msg-vault`. `clients_projects.jsonl` mixes Client and Project records (`client-…` / `proj-…` ids) and should be split.
- **Planned stores** (`status: planned`) have no writer yet: Client, JobLead, Platform, Organization, Contact, Account, Message, Thread, Attachment, SyncCursor, StyleSample.
