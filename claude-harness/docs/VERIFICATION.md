# Step verification protocol (v1, 2026-10-16)

This is the meta-rule for **all** agentic work in the harness, not just code (principle 21, "Verify every step"). The final independent `verify` (`skills/verify`, `docs/FANOUT.md` §4) checks the finished deliverable; this protocol checks every step on the way there, so errors are caught where they are cheap and don't compound across steps.

## The loop

Every step is five parts. A step that skips one is **unverified**, and the next step may not build on it.

| Part | Question | What it produces |
|---|---|---|
| **1. Precondition** | Is the world in the state this step assumes? (inputs exist, the file is the version I read, the page is the one I expect, the earlier step's proof holds) | a quick check and its result; if it fails, stop and re-plan instead of acting |
| **2. Action** | Do one thing: the smallest action that moves one criterion forward | the change itself |
| **3. Postcondition** | Did the action do what was intended, and nothing else? | a check that can fail: a script, a test, a read-back, a diff |
| **4. Proof** | What shows it? | the command and its decisive output lines, a quote with its location, a `git diff --stat`, a read-back value |
| **5. Log** | Where does the proof live? | the step line in `PROGRESS.md` (with proof pointer); a `verification` event for script checks; `mishap` if the step fixed an earlier mistake |

Rules:
- **Executable checks beat judgment.** Use a script when one exists; an LLM read is the fallback for what scripts can't decide.
- **Checks must be able to fail.** "Looks good" and "should work" are not postconditions. If no check can fail, say the step is unverified.
- **Postcondition includes "nothing else changed".** For files that's the diff; for a browser it's the rest of the form; for data it's the row count.
- **Cheap and proportional.** A step check is the *fastest* relevant check (one test file, one segment, one field), not the full suite. The full suite runs at hand-off and in `verify`.
- **A failed postcondition stops the line.** Fix it (or revert) before the next step. Never stack a new step on an unverified one.
- **Never weaken the check to pass it.** Editing a test, a rubric, a limit or a facts file so the step "passes" is the reward-hacking failure the harness guards against (`coding-standards` §5).
- **Step checks don't replace `verify`.** Hook-written step checks are labeled `step_check` and are ignored by the Stop gate (`hooks/verify_gate.py`).

## Automatic floor: the `step_check` hook

`hooks/step_check.py` runs after every `Edit`, `Write`, `MultiEdit` and `NotebookEdit` and does a cheap syntax check of the edited file:

| File | Check |
|---|---|
| `.py` | `python3 -I -m py_compile` |
| `.json` | JSON parse |
| `.jsonl` | parse each line (files up to 5 MB) |
| `.yaml`, `.yml` | `yaml.safe_load_all` if PyYAML is installed, else skipped |
| `.sh` | `bash -n` |
| `.ipynb` | JSON parse |
| other (`.ts`, `.js`, `.swift`, ...) | only a command configured in the project's `.claude/step_check.json` |

Project config (`<project>/.claude/step_check.json`), glob → command, or glob → `{command, timeout}`:

```json
{
  "*.ts": {"command": "npx tsc --noEmit -p .", "timeout": 20},
  "*.swift": "swiftc -parse {file}"
}
```

`{file}` is replaced by the shell-quoted path; the command runs in the project root (the folder holding `.claude/`). Built-in checks have a hard 5 s timeout; config commands default to 5 s and are capped at 60 s. A timeout is reported as a failure, never treated as a pass, and the whole process group is killed.

**Trust:** hooks run outside the sandbox, so a config file is code that runs on every edit. A config runs only after you trust that exact content: `python3 -I hooks/step_check.py --trust <project>/.claude/step_check.json` (its sha256 goes to `$HARNESS_DATA/step_check_trust.json`). Any later edit to the config, by a pull or by an agent, needs a new `--trust`; until then the hook skips it and says so. Agents never run `--trust` themselves.

It never blocks. On failure it adds `STEP CHECK FAILED: …` to Claude's context, so the agent fixes it before its next step. Each check (pass or fail) appends a `verification` event labeled `step_check` with `items: [path]`. `HARNESS_STEP_CHECK=0` turns it off. It is a floor: syntax, not correctness.

## Per-domain examples

### Code (`coder`, `code-reviewer`)
- **Pre:** read the function, its callers and its tests; run the touched test file once and record the baseline (what already failed).
- **Action:** one surgical diff (`coding-standards` §1).
- **Post:** `step_check` (syntax) → the touched test file (`python3 -I -m unittest tests.test_x`, `pytest tests/test_x.py -q`, `npm test -- x`) → lint/typecheck on the touched files. Nothing that passed in the baseline fails now.
- **Proof:** the commands, the pass/fail counts, `git diff --stat`.
- **Log:** step line in `PROGRESS.md`; hand the diff to `code-reviewer` (`step` mode).

### Translation (`translator`, `translation-qa`)
- **Pre:** the segment's source text and the glossary are loaded; the register for this client is known (`docs/REGISTERS.md`).
- **Action:** translate one segment (or one small batch).
- **Post:** `python3 -I scripts/translation_qa.py --source seg.ko.txt --target seg.en.txt --glossary <glossary> --direction ko-en` on that segment: numbers, units, tags, glossary terms, do-not-translate items, length.
- **Proof:** the QA summary line for the segment (0 errors, or each error and its fix).
- **Log:** mark the segment done in `PROGRESS.md` with the QA result.

### Synopsis (`synopsis`)
- **Pre:** `knowledge/reviewer_rules.md` read; the limit and unit known.
- **Action:** write or revise one draft.
- **Post:** `python3 -I scripts/textlen.py --limit <N> --unit <unit> draft.txt`, then pass/fail for every reviewer rule by its `R-` ID.
- **Proof:** the length line and the R-rule table.
- **Log:** draft version and its results in `PROGRESS.md`. Tier-V verification still follows (client-bound).

### Research (`web-researcher`, `/check`)
- **Pre:** look in `$HARNESS_DATA/research/ledger.jsonl` for an earlier, still-valid note.
- **Action:** find and read one source for one claim.
- **Post:** the claim is supported by a quote from that source, and a second independent source agrees (or the claim is marked single-source); the date is current.
- **Proof:** quote + URL + access date per claim.
- **Log:** one `ResearchNote` per claim in the ledger (`/check`).

### Browser (`browser-operator`, `browser-task`)
- **Pre:** the page URL/title and the target field are what the plan expects (read the DOM/accessibility tree, not a guess).
- **Action:** one input, click or navigation.
- **Post:** **read back** the field or page state and compare with the intended value; check nothing else on the form changed.
- **Proof:** the read-back text.
- **Log:** checkpoint the step in `PROGRESS.md` (field → value → source). Never submit without the user's OK.

### Intake (`intake-extractor`, `intake`)
- **Pre:** the source is registered in `manifest.json` with its sha256.
- **Action:** convert or extract one source into `knowledge/`.
- **Post:** `python3 -I scripts/kb.py lint` (citations resolve, manifest consistent), plus a sample check: 3 random passages compared against the original page.
- **Proof:** the lint output and the 3 sample comparisons with page anchors.
- **Log:** `knowledge/log.md` entry; originals deleted only after `kb.py safe-to-delete` agrees and the archive is verified.

### Invoices (`invoice`)
- **Pre:** the spec JSON's quantities trace to the delivered work (word/char counts recounted with `invoice.py count`).
- **Action:** compute the invoice.
- **Post:** `python3 -I scripts/invoice.py make spec.json --dry-run`; totals, withholding and FX match a hand recount.
- **Proof:** the dry-run line (gross, withholding, net).
- **Log:** only then `make` without `--dry-run`, which writes the ledger row. Sending waits for the user's OK.

### Job applications (`job-application`)
- **Pre:** the posting is still open (checked today); `facts.md` is current.
- **Action:** draft or revise one document.
- **Post:** `python3 -I scripts/claim_check.py draft.md --facts job-search/_master/facts.md`: every claim traces to a fact.
- **Proof:** the claim_check summary (0 untraced claims).
- **Log:** the `Application` record with `claim_check: pass`. Tier-V verification follows; submitting waits for the user's OK.

### Data writes (logs, ledgers, `tasks.json`, any JSONL store)
- **Pre:** the target file exists and its last line parses; you know the record type.
- **Action:** append or update one record.
- **Post:** `python3 -I scripts/schema_check.py --file <path> --type <Type>` (0 errors); the record count went up by exactly the expected number.
- **Proof:** the schema_check summary and the before/after count.
- **Log:** the write itself is the log; note its id in `PROGRESS.md` if it is a step.

## Logging a step check by hand

For script checks that matter later, append a `verification` event (`schema/event.md`) with `verdict`, `items` (the step or file), `scope_hint` (the project cwd), `content` (the command) and `labels: ["step_check"]`. Leave `step_check` off only for the final `verify` events, which are the ones the Stop gate counts.
